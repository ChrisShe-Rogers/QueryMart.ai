# QueryMart Agent Tool Schemas

This document defines the six QueryMart tools exposed to the sales advisor agent. The matching machine-readable OpenAPI document is `openapi/querymart-agent-tools.openapi.yaml`.

These tools are real FastAPI endpoints under `/tools/qm_*`. Tool responses must be treated as the source of truth for product, price, inventory, cart, and order state.

From inside the OpenClaw container, use:

```text
http://host.docker.internal:8000
```

Do not use `http://127.0.0.1:8000` from inside the OpenClaw container; that points at the container itself.

## Global Rules

- Use verified tool responses before making product, price, inventory, cart, or order claims.
- Do not invent unavailable products, prices, stock counts, discounts, shipping dates, or payment outcomes.
- `qm_submit_order` is high risk and must only be called after explicit customer confirmation.
- If the customer disputes price, reports a payment issue, complains, or requests an exception, follow `SALES_ESCALATION.md`.

## Tool: qm_search_products

Search active products by keyword and structured filters.

Endpoint:

```text
POST /tools/qm_search_products
```

From inside the OpenClaw container, send the request to:

```text
POST http://host.docker.internal:8000/tools/qm_search_products
```

Request schema:

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "q": { "type": "string", "maxLength": 255 },
    "category": { "type": "string", "maxLength": 64 },
    "brand": { "type": "string", "maxLength": 128 },
    "price_min": { "type": "number", "minimum": 0 },
    "price_max": { "type": "number", "minimum": 0 },
    "sort": {
      "type": "string",
      "enum": ["relevance", "price_asc", "price_desc", "delivery_asc"],
      "default": "relevance"
    },
    "limit": { "type": "integer", "minimum": 1, "maximum": 100, "default": 20 },
    "cursor": { "type": "string" }
  }
}
```

Response schema:

```json
{
  "type": "object",
  "required": ["meta", "total_estimate", "items"],
  "properties": {
    "meta": { "$ref": "#/components/schemas/ApiMeta" },
    "total_estimate": { "type": "integer" },
    "next_cursor": { "type": ["string", "null"] },
    "items": {
      "type": "array",
      "items": { "$ref": "#/components/schemas/ProductSummary" }
    }
  }
}
```

## Tool: qm_get_product

Fetch one product by SKU.

Endpoint:

```text
POST /tools/qm_get_product
```

Request schema:

```json
{
  "type": "object",
  "required": ["sku_id"],
  "additionalProperties": false,
  "properties": {
    "sku_id": { "type": "string", "minLength": 1, "maxLength": 64 }
  }
}
```

Response schema:

```json
{
  "type": "object",
  "required": ["meta", "item"],
  "properties": {
    "meta": { "$ref": "#/components/schemas/ApiMeta" },
    "item": { "$ref": "#/components/schemas/ProductDetail" }
  }
}
```

## Tool: qm_check_inventory

Check current inventory for a SKU before recommending, adding to cart, or submitting an order.

Endpoint:

```text
POST /tools/qm_check_inventory
```

Request schema:

```json
{
  "type": "object",
  "required": ["sku_id"],
  "additionalProperties": false,
  "properties": {
    "sku_id": { "type": "string", "minLength": 1, "maxLength": 64 },
    "requested_quantity": { "type": "integer", "minimum": 1, "default": 1 }
  }
}
```

Response schema:

```json
{
  "type": "object",
  "required": ["meta", "sku_id", "inventory", "requested_quantity", "available"],
  "properties": {
    "meta": { "$ref": "#/components/schemas/ApiMeta" },
    "sku_id": { "type": "string" },
    "inventory": { "type": "integer", "minimum": 0 },
    "requested_quantity": { "type": "integer", "minimum": 1 },
    "available": { "type": "boolean" },
    "shortfall": { "type": "integer", "minimum": 0 },
    "updated_at": { "type": "string", "format": "date-time" }
  }
}
```

## Tool: qm_get_price

Check current system price for a SKU before quoting or confirming price.

Endpoint:

```text
POST /tools/qm_get_price
```

Request schema:

```json
{
  "type": "object",
  "required": ["sku_id"],
  "additionalProperties": false,
  "properties": {
    "sku_id": { "type": "string", "minLength": 1, "maxLength": 64 },
    "quantity": { "type": "integer", "minimum": 1, "default": 1 }
  }
}
```

Response schema:

```json
{
  "type": "object",
  "required": ["meta", "sku_id", "unit_price", "quantity", "line_subtotal", "currency"],
  "properties": {
    "meta": { "$ref": "#/components/schemas/ApiMeta" },
    "sku_id": { "type": "string" },
    "unit_price": { "type": "number", "minimum": 0 },
    "quantity": { "type": "integer", "minimum": 1 },
    "line_subtotal": { "type": "number", "minimum": 0 },
    "currency": { "type": "string", "minLength": 3, "maxLength": 3 },
    "updated_at": { "type": "string", "format": "date-time" }
  }
}
```

## Tool: qm_create_cart

Create a cart, or create/update a cart with one SKU line.

Endpoint:

```text
POST /tools/qm_create_cart
```

If `items` is empty or omitted, only create an empty cart. If `items` has one or more lines, the endpoint adds each line using the existing cart inventory checks.

Request schema:

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "user_ref": { "type": "string", "maxLength": 128 },
    "agent_ref": { "type": "string", "maxLength": 128 },
    "currency": { "type": "string", "minLength": 3, "maxLength": 3, "default": "USD" },
    "cart_token": { "type": "string", "minLength": 8, "maxLength": 128 },
    "items": {
      "type": "array",
      "items": { "$ref": "#/components/schemas/CartLineInput" },
      "maxItems": 50
    }
  }
}
```

Response schema:

```json
{
  "type": "object",
  "required": ["meta", "ok", "cart_token", "currency", "items"],
  "properties": {
    "meta": { "$ref": "#/components/schemas/ApiMeta" },
    "ok": { "type": "boolean" },
    "cart_token": { "type": "string" },
    "currency": { "type": "string", "minLength": 3, "maxLength": 3 },
    "items": {
      "type": "array",
      "items": { "$ref": "#/components/schemas/CartLineResult" }
    }
  }
}
```

## Tool: qm_submit_order

Submit a pending order after human confirmation. This is a high-risk tool.

Endpoint:

```text
POST /tools/qm_submit_order
```

Required preconditions:

- The order must have been previewed first through `POST /api/v1/order/preview`.
- The customer must see the item list, quantities, current total, return policy, warranty, and confirmation code hint.
- The customer must explicitly confirm they want to place the order.
- The agent must provide the confirmation code generated by the preview step.

Request schema:

```json
{
  "type": "object",
  "required": [
    "order_no",
    "confirmation_code",
    "explicit_customer_confirmation",
    "risk_acknowledged"
  ],
  "additionalProperties": false,
  "properties": {
    "order_no": { "type": "string", "minLength": 1, "maxLength": 64 },
    "confirmation_code": {
      "type": "string",
      "minLength": 4,
      "maxLength": 32,
      "description": "Code from order preview, with or without the CONFIRM prefix."
    },
    "actor_ref": { "type": "string", "maxLength": 128 },
    "explicit_customer_confirmation": {
      "type": "boolean",
      "const": true,
      "description": "Must be true only after the customer explicitly confirms final order submission."
    },
    "risk_acknowledged": {
      "type": "boolean",
      "const": true,
      "description": "Must be true after the agent verifies no escalation condition is active."
    },
    "confirmation_summary": {
      "type": "string",
      "maxLength": 1000,
      "description": "Short human-readable summary of what the customer confirmed."
    }
  }
}
```

Response schema:

```json
{
  "type": "object",
  "required": ["meta", "ok", "order_no", "status"],
  "properties": {
    "meta": { "$ref": "#/components/schemas/ApiMeta" },
    "ok": { "type": "boolean" },
    "order_no": { "type": "string" },
    "status": { "type": "string", "enum": ["submitted"] }
  }
}
```
