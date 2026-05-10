# QueryMart Agent Tools

This file is regenerated from the live `querymart-api` OpenAPI document at `/openapi.json`.
It describes the real API operations that a sales advisor agent can use to help customers discover products, compare options, build carts, preview orders, and submit confirmed orders.

## Base URLs

From inside the OpenClaw container, use:

```text
http://host.docker.internal:8000
```

From the host machine, use:

```text
http://127.0.0.1:8000
```

The machine-readable agent OpenAPI file is `openapi/querymart-agent-tools.openapi.yaml`.

## Operating Rules

- Treat tool responses as the source of truth for product, price, inventory, cart, and order state.
- Check product details before making SKU-specific claims.
- Check inventory and price before recommending purchase or adding to cart.
- Use `qm_preview_order` before `qm_submit_order`.
- `qm_submit_order` is critical risk. Use it only after explicit customer confirmation and never during price disputes, complaints, or payment anomalies.
- Follow `SALES_ESCALATION.md` whenever escalation rules are triggered.

## Tool Index

| Tool | Method | Path | Risk | Use |
| --- | --- | --- | --- | --- |
| `qm_health` | `GET` | `/health` | `low` | Use to verify the QueryMart API is reachable before a sales workflow. |
| `qm_get_llms_guide` | `GET` | `/llms.txt` | `low` | Use when another agent or human needs a concise guide to available commerce endpoints and safety rules. |
| `qm_create_cart` | `POST` | `/api/v1/cart/create` | `medium` | Use after the customer is ready to start a cart, before adding items. |
| `qm_search_products` | `GET` | `/api/v1/products/search` | `low` | Use to find candidate products that match the customer need, budget, brand, category, or delivery preference. |
| `qm_get_product` | `GET` | `/api/v1/products/{sku_id}` | `low` | Use before making product-specific claims about price, inventory, specifications, delivery, return policy, or warranty. |
| `qm_batch_products` | `POST` | `/api/v1/products/batch` | `low` | Use to retrieve several known SKUs at once for recommendation, availability checks, or comparison setup. |
| `qm_compare_products` | `GET` | `/api/v1/compare` | `low` | Use to explain practical differences and recommend the best fit among shortlisted products. |
| `qm_add_to_cart` | `POST` | `/api/v1/cart/add` | `medium` | Use only after confirming the SKU and desired quantity with the customer. The API rejects quantities above inventory. |
| `qm_preview_order` | `POST` | `/api/v1/order/preview` | `high` | Use before final submission. Show the customer items, quantities, total, delivery estimate, policies, and confirmation code hint. |
| `qm_submit_order` | `POST` | `/api/v1/order/submit` | `critical` | High-risk. Use only after qm_preview_order and explicit customer confirmation. Never call during price disputes, complaints, or payment anomalies. |

## `qm_health`

Check QueryMart API health.

Endpoint:

```text
GET /health
```

OpenClaw container URL:

```text
GET http://host.docker.internal:8000/health
```

Risk level: `low`

Sales advisor use: Use to verify the QueryMart API is reachable before a sales workflow.

Request body schema: none.

Primary success response:

Successful Response

```json
{
  "additionalProperties": {
    "type": "boolean"
  },
  "type": "object",
  "title": "Response Health Health Get"
}
```

## `qm_get_llms_guide`

Fetch the QueryMart LLM access guide.

Endpoint:

```text
GET /llms.txt
```

OpenClaw container URL:

```text
GET http://host.docker.internal:8000/llms.txt
```

Risk level: `low`

Sales advisor use: Use when another agent or human needs a concise guide to available commerce endpoints and safety rules.

Request body schema: none.

Primary success response:

Successful Response

```json
{
  "type": "string"
}
```

## `qm_create_cart`

Create an empty shopping cart.

Endpoint:

```text
POST /api/v1/cart/create
```

OpenClaw container URL:

```text
POST http://host.docker.internal:8000/api/v1/cart/create
```

Risk level: `medium`

Sales advisor use: Use after the customer is ready to start a cart, before adding items.

Request body schema:

`CreateCartRequest`

```json
{
  "properties": {
    "user_ref": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ],
      "title": "User Ref"
    },
    "agent_ref": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ],
      "title": "Agent Ref"
    },
    "currency": {
      "type": "string",
      "maxLength": 3,
      "minLength": 3,
      "title": "Currency",
      "default": "USD"
    }
  },
  "type": "object",
  "title": "CreateCartRequest"
}
```

Primary success response:

Successful Response

Schema: `CreateCartResponse`

```json
{
  "properties": {
    "meta": {
      "$ref": "#/components/schemas/ApiMeta"
    },
    "ok": {
      "type": "boolean",
      "title": "Ok"
    },
    "cart_token": {
      "type": "string",
      "title": "Cart Token"
    },
    "currency": {
      "type": "string",
      "title": "Currency"
    }
  },
  "type": "object",
  "required": [
    "meta",
    "ok",
    "cart_token",
    "currency"
  ],
  "title": "CreateCartResponse"
}
```

## `qm_search_products`

Search active products by keyword and structured filters.

Endpoint:

```text
GET /api/v1/products/search
```

OpenClaw container URL:

```text
GET http://host.docker.internal:8000/api/v1/products/search
```

Risk level: `low`

Sales advisor use: Use to find candidate products that match the customer need, budget, brand, category, or delivery preference.

Parameters:

| Name | In | Required | Schema | Description |
| --- | --- | --- | --- | --- |
| `q` | `query` | `False` | `object` |  |
| `category` | `query` | `False` | `object` |  |
| `brand` | `query` | `False` | `object` |  |
| `price_min` | `query` | `False` | `object` |  |
| `price_max` | `query` | `False` | `object` |  |
| `sort` | `query` | `False` | `string` |  |
| `limit` | `query` | `False` | `integer` |  |
| `cursor` | `query` | `False` | `object` |  |

Request body schema: none.

Primary success response:

Successful Response

Schema: `SearchResponse`

```json
{
  "properties": {
    "meta": {
      "$ref": "#/components/schemas/ApiMeta"
    },
    "total_estimate": {
      "type": "integer",
      "title": "Total Estimate"
    },
    "next_cursor": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Next Cursor"
    },
    "items": {
      "items": {
        "$ref": "#/components/schemas/ProductOut"
      },
      "type": "array",
      "title": "Items"
    }
  },
  "type": "object",
  "required": [
    "meta",
    "total_estimate",
    "items"
  ],
  "title": "SearchResponse"
}
```

## `qm_get_product`

Fetch full product details for one SKU.

Endpoint:

```text
GET /api/v1/products/{sku_id}
```

OpenClaw container URL:

```text
GET http://host.docker.internal:8000/api/v1/products/{sku_id}
```

Risk level: `low`

Sales advisor use: Use before making product-specific claims about price, inventory, specifications, delivery, return policy, or warranty.

Parameters:

| Name | In | Required | Schema | Description |
| --- | --- | --- | --- | --- |
| `sku_id` | `path` | `True` | `string` |  |

Request body schema: none.

Primary success response:

Successful Response

Schema: `ProductResponse`

```json
{
  "properties": {
    "meta": {
      "$ref": "#/components/schemas/ApiMeta"
    },
    "item": {
      "$ref": "#/components/schemas/ProductOut"
    }
  },
  "type": "object",
  "required": [
    "meta",
    "item"
  ],
  "title": "ProductResponse"
}
```

## `qm_batch_products`

Fetch multiple products by SKU.

Endpoint:

```text
POST /api/v1/products/batch
```

OpenClaw container URL:

```text
POST http://host.docker.internal:8000/api/v1/products/batch
```

Risk level: `low`

Sales advisor use: Use to retrieve several known SKUs at once for recommendation, availability checks, or comparison setup.

Request body schema:

`BatchRequest`

```json
{
  "properties": {
    "sku_ids": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "maxItems": 100,
      "minItems": 1,
      "title": "Sku Ids"
    }
  },
  "type": "object",
  "required": [
    "sku_ids"
  ],
  "title": "BatchRequest"
}
```

Primary success response:

Successful Response

Schema: `BatchResponse`

```json
{
  "properties": {
    "meta": {
      "$ref": "#/components/schemas/ApiMeta"
    },
    "items": {
      "items": {
        "$ref": "#/components/schemas/ProductOut"
      },
      "type": "array",
      "title": "Items"
    },
    "missing_sku_ids": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "title": "Missing Sku Ids"
    }
  },
  "type": "object",
  "required": [
    "meta",
    "items"
  ],
  "title": "BatchResponse"
}
```

## `qm_compare_products`

Compare two to ten SKUs.

Endpoint:

```text
GET /api/v1/compare
```

OpenClaw container URL:

```text
GET http://host.docker.internal:8000/api/v1/compare
```

Risk level: `low`

Sales advisor use: Use to explain practical differences and recommend the best fit among shortlisted products.

Parameters:

| Name | In | Required | Schema | Description |
| --- | --- | --- | --- | --- |
| `sku` | `query` | `True` | `string` |  |

Request body schema: none.

Primary success response:

Successful Response

Schema: `CompareResponse`

```json
{
  "properties": {
    "meta": {
      "$ref": "#/components/schemas/ApiMeta"
    },
    "sku_ids": {
      "items": {
        "type": "string"
      },
      "type": "array",
      "title": "Sku Ids"
    },
    "common_dimensions": {
      "items": {
        "$ref": "#/components/schemas/CompareDimension"
      },
      "type": "array",
      "title": "Common Dimensions"
    },
    "category_dimensions": {
      "items": {
        "$ref": "#/components/schemas/CompareDimension"
      },
      "type": "array",
      "title": "Category Dimensions"
    },
    "recommendation": {
      "$ref": "#/components/schemas/CompareRecommendation"
    }
  },
  "type": "object",
  "required": [
    "meta",
    "sku_ids",
    "common_dimensions",
    "category_dimensions",
    "recommendation"
  ],
  "title": "CompareResponse"
}
```

## `qm_add_to_cart`

Add or update one product line in a cart.

Endpoint:

```text
POST /api/v1/cart/add
```

OpenClaw container URL:

```text
POST http://host.docker.internal:8000/api/v1/cart/add
```

Risk level: `medium`

Sales advisor use: Use only after confirming the SKU and desired quantity with the customer. The API rejects quantities above inventory.

Request body schema:

`AddCartRequest`

```json
{
  "properties": {
    "cart_token": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 128,
          "minLength": 8
        },
        {
          "type": "null"
        }
      ],
      "title": "Cart Token"
    },
    "sku_id": {
      "type": "string",
      "maxLength": 64,
      "minLength": 1,
      "title": "Sku Id"
    },
    "quantity": {
      "type": "integer",
      "maximum": 999.0,
      "exclusiveMinimum": 0.0,
      "title": "Quantity"
    },
    "user_ref": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ],
      "title": "User Ref"
    },
    "agent_ref": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ],
      "title": "Agent Ref"
    }
  },
  "type": "object",
  "required": [
    "sku_id",
    "quantity"
  ],
  "title": "AddCartRequest"
}
```

Primary success response:

Successful Response

Schema: `AddCartResponse`

```json
{
  "properties": {
    "meta": {
      "$ref": "#/components/schemas/ApiMeta"
    },
    "ok": {
      "type": "boolean",
      "title": "Ok"
    },
    "cart_token": {
      "type": "string",
      "title": "Cart Token"
    },
    "sku_id": {
      "type": "string",
      "title": "Sku Id"
    },
    "quantity": {
      "type": "integer",
      "title": "Quantity"
    }
  },
  "type": "object",
  "required": [
    "meta",
    "ok",
    "cart_token",
    "sku_id",
    "quantity"
  ],
  "title": "AddCartResponse"
}
```

## `qm_preview_order`

Create an order preview with totals and a confirmation code hint.

Endpoint:

```text
POST /api/v1/order/preview
```

OpenClaw container URL:

```text
POST http://host.docker.internal:8000/api/v1/order/preview
```

Risk level: `high`

Sales advisor use: Use before final submission. Show the customer items, quantities, total, delivery estimate, policies, and confirmation code hint.

Request body schema:

`OrderPreviewRequest`

```json
{
  "properties": {
    "cart_token": {
      "type": "string",
      "maxLength": 128,
      "minLength": 8,
      "title": "Cart Token"
    },
    "buyer_ref": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ],
      "title": "Buyer Ref"
    },
    "agent_ref": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ],
      "title": "Agent Ref"
    }
  },
  "type": "object",
  "required": [
    "cart_token"
  ],
  "title": "OrderPreviewRequest"
}
```

Primary success response:

Successful Response

Schema: `OrderPreviewResponse`

```json
{
  "properties": {
    "meta": {
      "$ref": "#/components/schemas/ApiMeta"
    },
    "order_no": {
      "type": "string",
      "title": "Order No"
    },
    "status": {
      "type": "string",
      "const": "pending_confirm",
      "title": "Status"
    },
    "confirmation_code_hint": {
      "type": "string",
      "title": "Confirmation Code Hint"
    },
    "bill": {
      "$ref": "#/components/schemas/Bill"
    },
    "delivery": {
      "$ref": "#/components/schemas/DeliveryEstimate"
    },
    "policies": {
      "additionalProperties": true,
      "type": "object",
      "title": "Policies"
    },
    "items": {
      "items": {
        "additionalProperties": true,
        "type": "object"
      },
      "type": "array",
      "title": "Items"
    }
  },
  "type": "object",
  "required": [
    "meta",
    "order_no",
    "status",
    "confirmation_code_hint",
    "bill",
    "delivery",
    "policies",
    "items"
  ],
  "title": "OrderPreviewResponse"
}
```

## `qm_submit_order`

Submit a pending order after explicit customer confirmation.

Endpoint:

```text
POST /api/v1/order/submit
```

OpenClaw container URL:

```text
POST http://host.docker.internal:8000/api/v1/order/submit
```

Risk level: `critical`

Sales advisor use: High-risk. Use only after qm_preview_order and explicit customer confirmation. Never call during price disputes, complaints, or payment anomalies.

Request body schema:

`OrderSubmitRequest`

```json
{
  "properties": {
    "order_no": {
      "type": "string",
      "maxLength": 64,
      "minLength": 1,
      "title": "Order No"
    },
    "confirmation_code": {
      "type": "string",
      "maxLength": 32,
      "minLength": 4,
      "title": "Confirmation Code"
    },
    "actor_ref": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 128
        },
        {
          "type": "null"
        }
      ],
      "title": "Actor Ref"
    }
  },
  "type": "object",
  "required": [
    "order_no",
    "confirmation_code"
  ],
  "title": "OrderSubmitRequest"
}
```

Primary success response:

Successful Response

Schema: `OrderSubmitResponse`

```json
{
  "properties": {
    "meta": {
      "$ref": "#/components/schemas/ApiMeta"
    },
    "ok": {
      "type": "boolean",
      "title": "Ok"
    },
    "order_no": {
      "type": "string",
      "title": "Order No"
    },
    "status": {
      "type": "string",
      "const": "submitted",
      "title": "Status"
    }
  },
  "type": "object",
  "required": [
    "meta",
    "ok",
    "order_no",
    "status"
  ],
  "title": "OrderSubmitResponse"
}
```

Critical safety requirement: call this only after `qm_preview_order`, after showing the customer final items and total, and after the customer explicitly confirms submission. The API requires the preview confirmation code.
