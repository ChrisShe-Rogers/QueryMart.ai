# QueryMart.ai Database MVP

AI-first commerce database foundation for universal SKU storage, agent-friendly product retrieval, comparison, and safe order submission. The local database runs on MySQL 8.4 LTS.

## Start MySQL

```bash
cp .env.example .env
docker compose up -d
```

The first boot starts a MySQL 8.4 LTS container and initializes `ai_commerce` from `mysql/init/*.sql`.

Connection defaults:

```text
Host: 127.0.0.1
Port: 3306
Database: ai_commerce
User: querymart
Password: querymartpass
Root password: rootpass
```

## Quick Checks

```bash
docker compose ps
docker compose exec mysql mysql -uquerymart -pquerymartpass ai_commerce
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

## Reset Local Data

This removes the local MySQL volume and re-runs initialization on the next start:

```bash
docker compose down -v
docker compose up -d
```
