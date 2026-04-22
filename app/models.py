from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


class ApiMeta(BaseModel):
    schema_version: str = "1.0"
    api_version: str = "v1"
    generated_at: datetime


class ProductMediaOut(BaseModel):
    media_type: str
    url: str
    alt_text: str | None = None
    sort_order: int


class ProductOut(BaseModel):
    sku_id: str
    title: str
    subtitle: str | None = None
    description: str | None = None
    brand: str | None = None
    category: str
    category_name: str
    price: Decimal
    currency: str
    inventory: int
    condition_type: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    shipping_regions: list[str] = Field(default_factory=list)
    shipping_fee_rule: dict[str, Any] | None = None
    safety_certifications: list[str] = Field(default_factory=list)
    return_policy_days: int
    warranty_months: int
    delivery_days_min: int
    delivery_days_max: int
    rating_avg: Decimal | None = None
    rating_count: int
    media: list[ProductMediaOut] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    updated_at: datetime


class SearchResponse(BaseModel):
    meta: ApiMeta
    total_estimate: int
    next_cursor: str | None = None
    items: list[ProductOut]


class ProductResponse(BaseModel):
    meta: ApiMeta
    item: ProductOut


class BatchRequest(BaseModel):
    sku_ids: list[str] = Field(min_length=1, max_length=100)


class BatchResponse(BaseModel):
    meta: ApiMeta
    items: list[ProductOut]
    missing_sku_ids: list[str] = Field(default_factory=list)


class CompareDimension(BaseModel):
    key: str
    label: str
    values: dict[str, Any]


class ScoreBreakdown(BaseModel):
    demand_match: Decimal
    total_cost: Decimal
    delivery_speed: Decimal
    after_sale: Decimal
    review_trust: Decimal
    final_score: Decimal


class CompareRecommendation(BaseModel):
    top_sku: str | None
    why_recommended: list[str]
    risk_flags: dict[str, list[str]]
    score_breakdown: dict[str, ScoreBreakdown]


class CompareResponse(BaseModel):
    meta: ApiMeta
    sku_ids: list[str]
    common_dimensions: list[CompareDimension]
    category_dimensions: list[CompareDimension]
    recommendation: CompareRecommendation


class AddCartRequest(BaseModel):
    cart_token: str | None = Field(default=None, min_length=8, max_length=128)
    sku_id: str = Field(min_length=1, max_length=64)
    quantity: int = Field(gt=0, le=999)
    user_ref: str | None = Field(default=None, max_length=128)
    agent_ref: str | None = Field(default=None, max_length=128)


class CreateCartRequest(BaseModel):
    user_ref: str | None = Field(default=None, max_length=128)
    agent_ref: str | None = Field(default=None, max_length=128)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class CreateCartResponse(BaseModel):
    meta: ApiMeta
    ok: bool
    cart_token: str
    currency: str


class AddCartResponse(BaseModel):
    meta: ApiMeta
    ok: bool
    cart_token: str
    sku_id: str
    quantity: int


class OrderPreviewRequest(BaseModel):
    cart_token: str = Field(min_length=8, max_length=128)
    buyer_ref: str | None = Field(default=None, max_length=128)
    agent_ref: str | None = Field(default=None, max_length=128)


class Bill(BaseModel):
    subtotal: Decimal
    shipping_fee: Decimal
    tax_fee: Decimal
    total: Decimal
    currency: str


class DeliveryEstimate(BaseModel):
    min_days: int
    max_days: int


class OrderPreviewResponse(BaseModel):
    meta: ApiMeta
    order_no: str
    status: Literal["pending_confirm"]
    confirmation_code_hint: str
    bill: Bill
    delivery: DeliveryEstimate
    policies: dict[str, Any]
    items: list[dict[str, Any]]


class OrderSubmitRequest(BaseModel):
    order_no: str = Field(min_length=1, max_length=64)
    confirmation_code: str = Field(min_length=4, max_length=32)
    actor_ref: str | None = Field(default=None, max_length=128)


class OrderSubmitResponse(BaseModel):
    meta: ApiMeta
    ok: bool
    order_no: str
    status: Literal["submitted"]
