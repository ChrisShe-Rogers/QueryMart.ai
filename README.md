# QueryMart.ai API and Database MVP

AI-first commerce foundation for universal SKU storage, agent-friendly product retrieval, comparison, and safe order submission. The local database runs on MySQL 8.4 LTS and the API runs on FastAPI.

## Start The Stack

```bash
cp .env.example .env
docker compose up -d
```

The first boot starts MySQL 8.4 LTS, initializes `ai_commerce` from `mysql/init/*.sql`, builds the FastAPI service, and exposes the API on port `8000`.

Connection defaults:

```text
Host: 127.0.0.1
Port: 3306
Database: ai_commerce
User: querymart
Password: querymartpass
Root password: rootpass
```

API defaults:

```text
Base URL: http://127.0.0.1:8000
OpenAPI: http://127.0.0.1:8000/docs
Health: http://127.0.0.1:8000/health
LLM Guide: /llms.txt
```

Core v1 endpoints:

```text
GET  /api/v1/products/search
GET  /api/v1/products/{sku_id}
POST /api/v1/products/batch
GET  /api/v1/compare?sku=SKU1,SKU2
POST /api/v1/cart/create
POST /api/v1/cart/add
POST /api/v1/order/preview
POST /api/v1/order/submit
```

## Quick Checks

```bash
docker compose ps
docker compose exec mysql mysql -uquerymart -pquerymartpass ai_commerce
curl "http://127.0.0.1:8000/api/v1/products/search?limit=5"
```

Useful smoke-test queries:

```sql
SELECT sku_id, title, price, inventory FROM products ORDER BY sku_id;
SELECT sku_id, category_code, JSON_PRETTY(attributes) FROM v_product_agent_specs;
SELECT attr_key, canonical_unit, value_type FROM attribute_definitions ORDER BY attr_key;
```

## Design Notes

- Product data is split into stable core SKU fields plus extensible `product_attributes`.
- `attribute_definitions` is the standard dictionary for normalized units and comparable fields.
- `category_attribute_definitions` declares which attributes matter per category.
- `v_product_agent_specs` gives API code a ready-made machine-readable product spec block.
- `product_feed_events` supports incremental JSON feed generation for agents.
- `api_clients` and `api_request_logs` prepare for API-key based rate limits instead of blocking agents.
- `orders`, `order_items`, and `order_audit_logs` support preview, human confirmation code, submit, and traceability.
- FastAPI endpoints live under `/api/v1` and return `meta.schema_version`, `meta.api_version`, and `meta.generated_at`.
- Product search supports cursor pagination plus `q`, `category`, `brand`, `price_min`, `price_max`, `sort`, and dynamic `attrs.<key>` filters.
- Cart flow supports both explicit `cart/create` and implicit cart creation during `cart/add` when `cart_token` is omitted.
- `llms.txt` at the project root provides a concise agent-facing access guide for product discovery and safe ordering.

## Reset Local Data

This removes the local MySQL volume and re-runs initialization on the next start:

```bash
docker compose down -v
docker compose up -d
```
