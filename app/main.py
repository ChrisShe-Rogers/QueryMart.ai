from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import random
import secrets
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from mysql.connector import Error as MySQLError

from app.config import get_settings
from app.cursor import decode_cursor, encode_cursor
from app.db import decode_json_field, get_connection
from app.models import (
    AddCartRequest,
    AddCartResponse,
    ApiMeta,
    BatchRequest,
    BatchResponse,
    Bill,
    CartLineResult,
    CheckInventoryToolRequest,
    CheckInventoryToolResponse,
    CompareDimension,
    CompareRecommendation,
    CompareResponse,
    CreateCartRequest,
    CreateCartResponse,
    CreateCartToolRequest,
    CreateCartToolResponse,
    DeliveryEstimate,
    GetPriceToolRequest,
    GetPriceToolResponse,
    GetProductToolRequest,
    OrderPreviewRequest,
    OrderPreviewResponse,
    OrderSubmitRequest,
    OrderSubmitResponse,
    ProductMediaOut,
    ProductOut,
    ProductResponse,
    ScoreBreakdown,
    SearchProductsToolRequest,
    SearchResponse,
    SubmitOrderToolRequest,
)

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")
LLMS_TXT_PATH = Path("/app/llms.txt")


def meta() -> ApiMeta:
    return ApiMeta(generated_at=datetime.now(timezone.utc))


def risk_flags(product: ProductOut) -> list[str]:
    flags: list[str] = []
    if product.inventory <= 5:
        flags.append("low_inventory")
    if product.warranty_months <= 0:
        flags.append("no_warranty")
    if product.return_policy_days < 14:
        flags.append("short_return_window")
    if not product.safety_certifications:
        flags.append("missing_safety_certifications")
    return flags


def normalize_product(row: dict[str, Any], media: list[dict[str, Any]] | None = None) -> ProductOut:
    product = ProductOut(
        sku_id=row["sku_id"],
        title=row["title"],
        subtitle=row.get("subtitle"),
        description=row.get("description"),
        brand=row.get("brand"),
        category=row["category_code"],
        category_name=row["category_name"],
        price=row["price"],
        currency=row["currency"],
        inventory=row["inventory"],
        condition_type=row["condition_type"],
        attributes=decode_json_field(row.get("attributes"), {}),
        shipping_regions=decode_json_field(row.get("shipping_regions"), []),
        shipping_fee_rule=decode_json_field(row.get("shipping_fee_rule"), None),
        safety_certifications=decode_json_field(row.get("safety_certifications"), []),
        return_policy_days=row["return_policy_days"],
        warranty_months=row["warranty_months"],
        delivery_days_min=row["delivery_days_min"],
        delivery_days_max=row["delivery_days_max"],
        rating_avg=row.get("rating_avg"),
        rating_count=row["rating_count"],
        media=[ProductMediaOut(**item) for item in media or []],
        updated_at=row["updated_at"],
    )
    product.risk_flags = risk_flags(product)
    return product


def product_select_sql() -> str:
    return """
        SELECT
          p.id,
          p.sku_id,
          p.title,
          p.subtitle,
          p.description,
          p.brand,
          c.code AS category_code,
          c.name AS category_name,
          p.condition_type,
          p.currency,
          p.price,
          p.inventory,
          p.shipping_regions,
          p.shipping_fee_rule,
          p.delivery_days_min,
          p.delivery_days_max,
          p.return_policy_days,
          p.warranty_months,
          p.safety_certifications,
          p.rating_avg,
          p.rating_count,
          p.updated_at,
          COALESCE(
            JSON_OBJECTAGG(
              pa.attr_key,
              JSON_OBJECT(
                'value_text', pa.attr_value_text,
                'value_num', pa.attr_value_num,
                'value_bool', pa.attr_value_bool,
                'unit', pa.attr_unit,
                'normalized_value', pa.normalized_value,
                'normalized_num', pa.normalized_num,
                'value_type', pa.value_type
              )
            ),
            JSON_OBJECT()
          ) AS attributes
        FROM products p
        JOIN categories c ON c.id = p.category_id
        LEFT JOIN product_attributes pa ON pa.product_id = p.id
    """


def group_by_product_sql() -> str:
    return """
        GROUP BY
          p.id, p.sku_id, p.title, p.subtitle, p.description, p.brand,
          c.code, c.name, p.condition_type, p.currency, p.price, p.inventory,
          p.shipping_regions, p.shipping_fee_rule, p.delivery_days_min,
          p.delivery_days_max, p.return_policy_days, p.warranty_months,
          p.safety_certifications, p.rating_avg, p.rating_count, p.updated_at
    """


def fetch_media(product_ids: list[int]) -> dict[int, list[dict[str, Any]]]:
    if not product_ids:
        return {}
    placeholders = ", ".join(["%s"] * len(product_ids))
    sql = f"""
        SELECT product_id, media_type, url, alt_text, sort_order
        FROM product_media
        WHERE product_id IN ({placeholders})
        ORDER BY product_id, sort_order
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, product_ids)
        rows = cursor.fetchall()

    media_by_product: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        media_by_product.setdefault(row["product_id"], []).append(row)
    return media_by_product


def fetch_products_by_skus(sku_ids: list[str]) -> list[ProductOut]:
    if not sku_ids:
        return []
    placeholders = ", ".join(["%s"] * len(sku_ids))
    sql = f"""
        {product_select_sql()}
        WHERE p.status = 'active' AND p.sku_id IN ({placeholders})
        {group_by_product_sql()}
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, sku_ids)
        rows = cursor.fetchall()

    media = fetch_media([row["id"] for row in rows])
    products = [normalize_product(row, media.get(row["id"], [])) for row in rows]
    order = {sku_id: index for index, sku_id in enumerate(sku_ids)}
    return sorted(products, key=lambda item: order.get(item.sku_id, len(order)))


def parse_attr_filters(request: Request) -> dict[str, str]:
    return {
        key.removeprefix("attrs."): value
        for key, value in request.query_params.items()
        if key.startswith("attrs.") and key != "attrs."
    }


def add_attr_filter(sql_parts: list[str], params: list[Any], attr_key: str, attr_value: str) -> None:
    alias = f"f_{len(params)}"
    sql_parts.append(
        f"""
        EXISTS (
          SELECT 1
          FROM product_attributes {alias}
          WHERE {alias}.product_id = p.id
            AND {alias}.attr_key = %s
            AND (
              {alias}.normalized_value = %s
              OR {alias}.attr_value_text = %s
              OR CAST({alias}.normalized_num AS CHAR) = %s
            )
        )
        """
    )
    params.extend([attr_key, attr_value, attr_value, attr_value])


def shipping_fee(rule: dict[str, Any] | None, subtotal: Decimal) -> Decimal:
    if not rule:
        return Decimal("0.00")
    rule_type = rule.get("type")
    if rule_type == "flat":
        return Decimal(str(rule.get("fee", "0")))
    if rule_type == "free_over":
        threshold = Decimal(str(rule.get("threshold", "0")))
        if subtotal >= threshold:
            return Decimal("0.00")
        return Decimal(str(rule.get("fee", "0")))
    return Decimal("0.00")


def new_cart_token() -> str:
    return f"cart_{secrets.token_urlsafe(18)}"


def create_cart_record(user_ref: str | None, agent_ref: str | None, currency: str) -> str:
    cart_token = new_cart_token()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO carts (cart_token, user_ref, agent_ref, currency)
            VALUES (%s, %s, %s, %s)
            """,
            [cart_token, user_ref, agent_ref, currency],
        )
        conn.commit()
    return cart_token


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/llms.txt", response_class=PlainTextResponse)
def llms_txt() -> str:
    return LLMS_TXT_PATH.read_text(encoding="utf-8")


@app.post("/api/v1/cart/create", response_model=CreateCartResponse)
def create_cart(req: CreateCartRequest) -> CreateCartResponse:
    currency = req.currency.upper()
    cart_token = create_cart_record(req.user_ref, req.agent_ref, currency)
    return CreateCartResponse(meta=meta(), ok=True, cart_token=cart_token, currency=currency)


@app.post(
    "/tools/qm_search_products",
    response_model=SearchResponse,
    tags=["Agent Tools"],
    operation_id="qm_search_products",
)
def qm_search_products(req: SearchProductsToolRequest, request: Request) -> SearchResponse:
    return search_products(
        request=request,
        q=req.q,
        category=req.category,
        brand=req.brand,
        price_min=req.price_min,
        price_max=req.price_max,
        sort=req.sort,
        limit=req.limit,
        cursor=req.cursor,
    )


@app.post(
    "/tools/qm_get_product",
    response_model=ProductResponse,
    tags=["Agent Tools"],
    operation_id="qm_get_product",
)
def qm_get_product(req: GetProductToolRequest) -> ProductResponse:
    return get_product(req.sku_id)


@app.post(
    "/tools/qm_check_inventory",
    response_model=CheckInventoryToolResponse,
    tags=["Agent Tools"],
    operation_id="qm_check_inventory",
)
def qm_check_inventory(req: CheckInventoryToolRequest) -> CheckInventoryToolResponse:
    product = get_product(req.sku_id).item
    shortfall = max(req.requested_quantity - product.inventory, 0)
    return CheckInventoryToolResponse(
        meta=meta(),
        sku_id=product.sku_id,
        inventory=product.inventory,
        requested_quantity=req.requested_quantity,
        available=shortfall == 0,
        shortfall=shortfall,
        updated_at=product.updated_at,
    )


@app.post(
    "/tools/qm_get_price",
    response_model=GetPriceToolResponse,
    tags=["Agent Tools"],
    operation_id="qm_get_price",
)
def qm_get_price(req: GetPriceToolRequest) -> GetPriceToolResponse:
    product = get_product(req.sku_id).item
    return GetPriceToolResponse(
        meta=meta(),
        sku_id=product.sku_id,
        unit_price=product.price,
        quantity=req.quantity,
        line_subtotal=product.price * req.quantity,
        currency=product.currency,
        updated_at=product.updated_at,
    )


@app.post(
    "/tools/qm_create_cart",
    response_model=CreateCartToolResponse,
    tags=["Agent Tools"],
    operation_id="qm_create_cart",
)
def qm_create_cart(req: CreateCartToolRequest) -> CreateCartToolResponse:
    cart_token = req.cart_token or create_cart_record(req.user_ref, req.agent_ref, req.currency.upper())
    added_items: list[CartLineResult] = []

    for item in req.items:
        add_to_cart(
            AddCartRequest(
                cart_token=cart_token,
                sku_id=item.sku_id,
                quantity=item.quantity,
                user_ref=req.user_ref,
                agent_ref=req.agent_ref,
            )
        )
        added_items.append(CartLineResult(sku_id=item.sku_id, quantity=item.quantity, ok=True))

    return CreateCartToolResponse(
        meta=meta(),
        ok=True,
        cart_token=cart_token,
        currency=req.currency.upper(),
        items=added_items,
    )


@app.post(
    "/tools/qm_submit_order",
    response_model=OrderSubmitResponse,
    tags=["Agent Tools"],
    operation_id="qm_submit_order",
)
def qm_submit_order(req: SubmitOrderToolRequest, request: Request) -> OrderSubmitResponse:
    if not req.explicit_customer_confirmation:
        raise HTTPException(status_code=403, detail="Explicit customer confirmation is required")
    if not req.risk_acknowledged:
        raise HTTPException(status_code=403, detail="Risk acknowledgement is required")
    return order_submit(
        OrderSubmitRequest(
            order_no=req.order_no,
            confirmation_code=req.confirmation_code,
            actor_ref=req.actor_ref,
        ),
        request,
    )


@app.get("/api/v1/products/search", response_model=SearchResponse)
def search_products(
    request: Request,
    q: str | None = Query(default=None, max_length=255),
    category: str | None = Query(default=None, max_length=64),
    brand: str | None = Query(default=None, max_length=128),
    price_min: Decimal | None = Query(default=None, ge=0),
    price_max: Decimal | None = Query(default=None, ge=0),
    sort: str = Query("relevance", pattern="^(relevance|price_asc|price_desc|delivery_asc)$"),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
) -> SearchResponse:
    cursor_data = decode_cursor(cursor) if cursor else None
    if cursor_data and cursor_data.get("sort") != sort:
        raise HTTPException(status_code=400, detail="Cursor sort does not match request sort")

    where = ["p.status = 'active'"]
    params: list[Any] = []

    if q:
        where.append("(MATCH(p.title, p.subtitle, p.description) AGAINST (%s IN NATURAL LANGUAGE MODE) OR p.title LIKE %s)")
        params.extend([q, f"%{q}%"])
    if category:
        where.append("c.code = %s")
        params.append(category)
    if brand:
        where.append("p.brand = %s")
        params.append(brand)
    if price_min is not None:
        where.append("p.price >= %s")
        params.append(price_min)
    if price_max is not None:
        where.append("p.price <= %s")
        params.append(price_max)
    for attr_key, attr_value in parse_attr_filters(request).items():
        add_attr_filter(where, params, attr_key, attr_value)

    order_clause = "p.updated_at DESC, p.sku_id ASC"
    if sort == "price_asc":
        order_clause = "p.price ASC, p.sku_id ASC"
    elif sort == "price_desc":
        order_clause = "p.price DESC, p.sku_id ASC"
    elif sort == "delivery_asc":
        order_clause = "p.delivery_days_min ASC, p.delivery_days_max ASC, p.sku_id ASC"

    total_where_sql = " AND ".join(where)
    total_params = list(params)

    if cursor_data:
        last = cursor_data.get("last", {})
        if sort == "price_asc":
            where.append("(p.price > %s OR (p.price = %s AND p.sku_id > %s))")
            params.extend([last["price"], last["price"], last["sku_id"]])
        elif sort == "price_desc":
            where.append("(p.price < %s OR (p.price = %s AND p.sku_id > %s))")
            params.extend([last["price"], last["price"], last["sku_id"]])
        elif sort == "delivery_asc":
            where.append(
                "(p.delivery_days_min > %s OR (p.delivery_days_min = %s AND p.delivery_days_max > %s) "
                "OR (p.delivery_days_min = %s AND p.delivery_days_max = %s AND p.sku_id > %s))"
            )
            params.extend([
                last["delivery_days_min"],
                last["delivery_days_min"],
                last["delivery_days_max"],
                last["delivery_days_min"],
                last["delivery_days_max"],
                last["sku_id"],
            ])
        else:
            where.append("(p.updated_at < %s OR (p.updated_at = %s AND p.sku_id > %s))")
            params.extend([last["updated_at"], last["updated_at"], last["sku_id"]])

    where_sql = " AND ".join(where)
    count_sql = f"SELECT COUNT(DISTINCT p.id) AS total FROM products p JOIN categories c ON c.id = p.category_id WHERE {total_where_sql}"
    query_sql = f"""
        {product_select_sql()}
        WHERE {where_sql}
        {group_by_product_sql()}
        ORDER BY {order_clause}
        LIMIT %s
    """

    try:
        with get_connection() as conn:
            db_cursor = conn.cursor(dictionary=True)
            db_cursor.execute(count_sql, total_params)
            total_estimate = db_cursor.fetchone()["total"]
            db_cursor.execute(query_sql, [*params, limit + 1])
            rows = db_cursor.fetchall()
    except MySQLError as exc:
        raise HTTPException(status_code=500, detail="Database query failed") from exc

    page_rows = rows[:limit]
    media = fetch_media([row["id"] for row in page_rows])
    items = [normalize_product(row, media.get(row["id"], [])) for row in page_rows]

    next_cursor = None
    if len(rows) > limit and page_rows:
        last_row = page_rows[-1]
        last_value: dict[str, Any] = {"sku_id": last_row["sku_id"]}
        if sort in {"price_asc", "price_desc"}:
            last_value["price"] = str(last_row["price"])
        elif sort == "delivery_asc":
            last_value["delivery_days_min"] = last_row["delivery_days_min"]
            last_value["delivery_days_max"] = last_row["delivery_days_max"]
        else:
            last_value["updated_at"] = last_row["updated_at"].isoformat(sep=" ")
        next_cursor = encode_cursor({"sort": sort, "last": last_value})

    return SearchResponse(meta=meta(), total_estimate=total_estimate, next_cursor=next_cursor, items=items)


@app.get("/api/v1/products/{sku_id}", response_model=ProductResponse)
def get_product(sku_id: str) -> ProductResponse:
    products = fetch_products_by_skus([sku_id])
    if not products:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse(meta=meta(), item=products[0])


@app.post("/api/v1/products/batch", response_model=BatchResponse)
def batch_products(req: BatchRequest) -> BatchResponse:
    products = fetch_products_by_skus(req.sku_ids)
    found = {product.sku_id for product in products}
    return BatchResponse(
        meta=meta(),
        items=products,
        missing_sku_ids=[sku_id for sku_id in req.sku_ids if sku_id not in found],
    )


@app.get("/api/v1/compare", response_model=CompareResponse)
def compare_products(sku: str = Query(min_length=1)) -> CompareResponse:
    sku_ids = [item.strip() for item in sku.split(",") if item.strip()]
    if len(sku_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 SKUs")
    if len(sku_ids) > 10:
        raise HTTPException(status_code=400, detail="Compare supports at most 10 SKUs")

    products = fetch_products_by_skus(sku_ids)
    if len(products) != len(set(sku_ids)):
        found = {product.sku_id for product in products}
        missing = [sku_id for sku_id in sku_ids if sku_id not in found]
        raise HTTPException(status_code=404, detail={"message": "Some SKUs were not found", "missing_sku_ids": missing})

    common_dimensions = [
        CompareDimension(key="price", label="Price", values={p.sku_id: p.price for p in products}),
        CompareDimension(key="inventory", label="Inventory", values={p.sku_id: p.inventory for p in products}),
        CompareDimension(key="delivery_days", label="Estimated delivery days", values={p.sku_id: [p.delivery_days_min, p.delivery_days_max] for p in products}),
        CompareDimension(key="return_policy_days", label="Return policy days", values={p.sku_id: p.return_policy_days for p in products}),
        CompareDimension(key="warranty_months", label="Warranty months", values={p.sku_id: p.warranty_months for p in products}),
    ]

    attr_keys = sorted({key for product in products for key, value in product.attributes.items() if value})
    category_dimensions = [
        CompareDimension(
            key=attr_key,
            label=attr_key.replace("_", " ").title(),
            values={product.sku_id: product.attributes.get(attr_key) for product in products},
        )
        for attr_key in attr_keys
    ]

    max_price = max((p.price for p in products), default=Decimal("1")) or Decimal("1")
    max_delivery = max((p.delivery_days_min for p in products), default=1) or 1
    max_after_sale = max((p.return_policy_days + p.warranty_months * 2 for p in products), default=1) or 1
    max_reviews = max((p.rating_count for p in products), default=1) or 1

    breakdown: dict[str, ScoreBreakdown] = {}
    for product in products:
        demand_match = Decimal("1.00")
        total_cost = Decimal("1.00") - (product.price / max_price * Decimal("0.70"))
        delivery_speed = Decimal("1.00") - (Decimal(product.delivery_days_min) / Decimal(max_delivery) * Decimal("0.70"))
        after_sale = Decimal(product.return_policy_days + product.warranty_months * 2) / Decimal(max_after_sale)
        review_trust = Decimal(product.rating_count) / Decimal(max_reviews)
        final_score = (
            demand_match * Decimal("0.35")
            + total_cost * Decimal("0.25")
            + delivery_speed * Decimal("0.15")
            + after_sale * Decimal("0.15")
            + review_trust * Decimal("0.10")
        )
        breakdown[product.sku_id] = ScoreBreakdown(
            demand_match=demand_match.quantize(Decimal("0.01")),
            total_cost=total_cost.quantize(Decimal("0.01")),
            delivery_speed=delivery_speed.quantize(Decimal("0.01")),
            after_sale=after_sale.quantize(Decimal("0.01")),
            review_trust=review_trust.quantize(Decimal("0.01")),
            final_score=final_score.quantize(Decimal("0.01")),
        )

    top_sku = max(breakdown, key=lambda key: breakdown[key].final_score) if breakdown else None
    why = []
    if top_sku:
        top = next(product for product in products if product.sku_id == top_sku)
        why = [
            f"{top.sku_id} has the strongest weighted score for cost, delivery, after-sale policy, and review trust.",
            f"Return window is {top.return_policy_days} days and warranty is {top.warranty_months} months.",
        ]

    return CompareResponse(
        meta=meta(),
        sku_ids=sku_ids,
        common_dimensions=common_dimensions,
        category_dimensions=category_dimensions,
        recommendation=CompareRecommendation(
            top_sku=top_sku,
            why_recommended=why,
            risk_flags={product.sku_id: product.risk_flags for product in products},
            score_breakdown=breakdown,
        ),
    )


@app.post("/api/v1/cart/add", response_model=AddCartResponse)
def add_to_cart(req: AddCartRequest) -> AddCartResponse:
    products = fetch_products_by_skus([req.sku_id])
    if not products:
        raise HTTPException(status_code=404, detail="Product not found")
    product = products[0]
    if req.quantity > product.inventory:
        raise HTTPException(status_code=409, detail="Requested quantity exceeds inventory")
    cart_token = req.cart_token or create_cart_record(req.user_ref, req.agent_ref, product.currency)

    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            INSERT INTO carts (cart_token, user_ref, agent_ref, currency)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              user_ref = COALESCE(VALUES(user_ref), user_ref),
              agent_ref = COALESCE(VALUES(agent_ref), agent_ref),
              updated_at = CURRENT_TIMESTAMP
            """,
            [cart_token, req.user_ref, req.agent_ref, product.currency],
        )
        cursor.execute("SELECT id FROM carts WHERE cart_token = %s", [cart_token])
        cart_id = cursor.fetchone()["id"]
        cursor.execute(
            """
            INSERT INTO cart_items (cart_id, product_id, quantity, unit_price)
            SELECT %s, id, %s, price
            FROM products
            WHERE sku_id = %s
            ON DUPLICATE KEY UPDATE
              quantity = VALUES(quantity),
              unit_price = VALUES(unit_price),
              updated_at = CURRENT_TIMESTAMP
            """,
            [cart_id, req.quantity, req.sku_id],
        )
        conn.commit()

    return AddCartResponse(meta=meta(), ok=True, cart_token=cart_token, sku_id=req.sku_id, quantity=req.quantity)


@app.post("/api/v1/order/preview", response_model=OrderPreviewResponse)
def order_preview(req: OrderPreviewRequest, request: Request) -> OrderPreviewResponse:
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, currency FROM carts WHERE cart_token = %s", [req.cart_token])
        cart = cursor.fetchone()
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        cursor.execute(
            """
            SELECT ci.quantity, ci.unit_price, p.id AS product_id, p.sku_id, p.title,
                   p.shipping_fee_rule, p.delivery_days_min, p.delivery_days_max,
                   p.return_policy_days, p.warranty_months
            FROM cart_items ci
            JOIN products p ON p.id = ci.product_id
            WHERE ci.cart_id = %s
            """,
            [cart["id"]],
        )
        rows = cursor.fetchall()
        if not rows:
            raise HTTPException(status_code=409, detail="Cart is empty")

        subtotal = sum(Decimal(row["unit_price"]) * row["quantity"] for row in rows)
        shipping = max(shipping_fee(decode_json_field(row["shipping_fee_rule"], None), subtotal) for row in rows)
        tax = Decimal("0.00")
        total = subtotal + shipping + tax
        min_days = max(row["delivery_days_min"] for row in rows)
        max_days = max(row["delivery_days_max"] for row in rows)
        confirmation_code = str(random.SystemRandom().randint(1000, 9999))
        order_no = f"PV{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"

        cursor.execute(
            """
            INSERT INTO orders (
              order_no, cart_id, buyer_ref, status, subtotal, shipping_fee, tax_fee, total, currency,
              delivery_days_min, delivery_days_max, confirmation_code, confirmation_expires_at, agent_ref
            )
            VALUES (%s, %s, %s, 'pending_confirm', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                order_no,
                cart["id"],
                req.buyer_ref,
                subtotal,
                shipping,
                tax,
                total,
                cart["currency"],
                min_days,
                max_days,
                confirmation_code,
                datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15),
                req.agent_ref,
            ],
        )
        order_id = cursor.lastrowid
        for row in rows:
            line_total = Decimal(row["unit_price"]) * row["quantity"]
            cursor.execute(
                """
                INSERT INTO order_items (order_id, product_id, sku_id, title, quantity, unit_price, line_total)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                [order_id, row["product_id"], row["sku_id"], row["title"], row["quantity"], row["unit_price"], line_total],
            )
        cursor.execute(
            """
            INSERT INTO order_audit_logs (order_id, actor_type, actor_ref, action, payload, ip, user_agent)
            VALUES (%s, 'agent', %s, 'preview', JSON_OBJECT('cart_token', %s), %s, %s)
            """,
            [order_id, req.agent_ref, req.cart_token, request.client.host if request.client else None, request.headers.get("user-agent")],
        )
        conn.commit()

    return OrderPreviewResponse(
        meta=meta(),
        order_no=order_no,
        status="pending_confirm",
        confirmation_code_hint=f"CONFIRM {confirmation_code}",
        bill=Bill(subtotal=subtotal, shipping_fee=shipping, tax_fee=tax, total=total, currency=cart["currency"]),
        delivery=DeliveryEstimate(min_days=min_days, max_days=max_days),
        policies={
            "return_policy_days_min": min(row["return_policy_days"] for row in rows),
            "warranty_months_min": min(row["warranty_months"] for row in rows),
            "confirmation_expires_in_minutes": 15,
        },
        items=[
            {
                "sku_id": row["sku_id"],
                "title": row["title"],
                "quantity": row["quantity"],
                "unit_price": row["unit_price"],
                "line_total": Decimal(row["unit_price"]) * row["quantity"],
            }
            for row in rows
        ],
    )


@app.post("/api/v1/order/submit", response_model=OrderSubmitResponse)
def order_submit(req: OrderSubmitRequest, request: Request) -> OrderSubmitResponse:
    normalized_code = req.confirmation_code.removeprefix("CONFIRM ").strip()
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, confirmation_code, confirmation_expires_at, status
            FROM orders
            WHERE order_no = %s
            FOR UPDATE
            """,
            [req.order_no],
        )
        order = cursor.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order["status"] != "pending_confirm":
            raise HTTPException(status_code=409, detail="Order is not pending confirmation")
        if order["confirmation_code"] != normalized_code:
            raise HTTPException(status_code=403, detail="Invalid confirmation code")
        if order["confirmation_expires_at"] and order["confirmation_expires_at"] < datetime.utcnow():
            raise HTTPException(status_code=409, detail="Confirmation code expired")

        cursor.execute(
            """
            UPDATE orders
            SET status = 'submitted', confirmed_at = CURRENT_TIMESTAMP, submitted_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            [order["id"]],
        )
        cursor.execute(
            """
            INSERT INTO order_audit_logs (order_id, actor_type, actor_ref, action, payload, ip, user_agent)
            VALUES (%s, 'human', %s, 'submit', JSON_OBJECT('order_no', %s), %s, %s)
            """,
            [order["id"], req.actor_ref, req.order_no, request.client.host if request.client else None, request.headers.get("user-agent")],
        )
        conn.commit()

    return OrderSubmitResponse(meta=meta(), ok=True, order_no=req.order_no, status="submitted")
