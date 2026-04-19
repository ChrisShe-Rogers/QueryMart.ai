USE ai_commerce;

INSERT INTO categories (code, name, parent_id, level, google_taxonomy_id, google_taxonomy_path) VALUES
('textiles', 'Textiles', NULL, 1, '1604', 'Apparel & Accessories'),
('toys', 'Toys', NULL, 1, '1239', 'Toys & Games'),
('electronics', 'Electronics', NULL, 1, '222', 'Electronics'),
('home', 'Home', NULL, 1, '536', 'Home & Garden'),
('daily-goods', 'Daily Goods', NULL, 1, '5710', 'Health & Beauty > Personal Care');

INSERT INTO categories (code, name, parent_id, level, google_taxonomy_path)
SELECT 'textiles-blankets', 'Blankets', id, 2, 'Home & Garden > Linens & Bedding > Bedding > Blankets'
FROM categories WHERE code = 'textiles';
INSERT INTO categories (code, name, parent_id, level, google_taxonomy_path)
SELECT 'toys-stem', 'STEM Toys', id, 2, 'Toys & Games > Toys > Educational Toys'
FROM categories WHERE code = 'toys';
INSERT INTO categories (code, name, parent_id, level, google_taxonomy_path)
SELECT 'electronics-chargers', 'Chargers', id, 2, 'Electronics > Power > Chargers'
FROM categories WHERE code = 'electronics';
INSERT INTO categories (code, name, parent_id, level, google_taxonomy_path)
SELECT 'home-lighting', 'Lighting', id, 2, 'Home & Garden > Lighting'
FROM categories WHERE code = 'home';
INSERT INTO categories (code, name, parent_id, level, google_taxonomy_path)
SELECT 'daily-cleaning', 'Cleaning Supplies', id, 2, 'Home & Garden > Household Supplies > Cleaning Supplies'
FROM categories WHERE code = 'daily-goods';

INSERT INTO attribute_definitions
(attr_key, label, value_type, canonical_unit, allowed_units, enum_values, description, is_filterable, is_comparable)
VALUES
('material', 'Material', 'text', NULL, NULL, NULL, 'Primary material or composition.', 1, 1),
('fabric_gsm', 'Fabric weight', 'number', 'gsm', JSON_ARRAY('gsm'), NULL, 'Fabric weight in grams per square meter.', 1, 1),
('power_w', 'Power', 'number', 'W', JSON_ARRAY('W'), NULL, 'Rated power draw or output.', 1, 1),
('capacity_wh', 'Capacity', 'number', 'Wh', JSON_ARRAY('Wh'), NULL, 'Battery capacity in watt-hours.', 1, 1),
('connector_type', 'Connector type', 'enum', NULL, NULL, JSON_ARRAY('USB-C','USB-A','Lightning','Barrel'), 'Electrical or data connector type.', 1, 1),
('age_range', 'Age range', 'text', NULL, NULL, NULL, 'Human-readable age suitability.', 1, 1),
('dimmable', 'Dimmable', 'boolean', NULL, NULL, NULL, 'Whether brightness can be adjusted.', 1, 1),
('scent', 'Scent', 'text', NULL, NULL, NULL, 'Scent or fragrance profile.', 1, 0);

INSERT INTO category_attribute_definitions (category_id, attribute_definition_id, is_required, display_order)
SELECT c.id, a.id, 1, 10
FROM categories c JOIN attribute_definitions a ON a.attr_key = 'material'
WHERE c.code IN ('textiles-blankets', 'toys-stem', 'daily-cleaning');

INSERT INTO category_attribute_definitions (category_id, attribute_definition_id, is_required, display_order)
SELECT c.id, a.id, 1, 20
FROM categories c JOIN attribute_definitions a ON a.attr_key = 'fabric_gsm'
WHERE c.code = 'textiles-blankets';

INSERT INTO category_attribute_definitions (category_id, attribute_definition_id, is_required, display_order)
SELECT c.id, a.id, 1, 10
FROM categories c JOIN attribute_definitions a ON a.attr_key IN ('power_w', 'connector_type')
WHERE c.code = 'electronics-chargers';

INSERT INTO category_attribute_definitions (category_id, attribute_definition_id, is_required, display_order)
SELECT c.id, a.id, 0, 10
FROM categories c JOIN attribute_definitions a ON a.attr_key = 'dimmable'
WHERE c.code = 'home-lighting';

INSERT INTO products
(sku_id, title, subtitle, description, brand, category_id, gtin, mpn, condition_type, currency, price, inventory, weight_kg,
 dimensions_json, safety_certifications, age_min, age_max, warranty_months, return_policy_days, shipping_regions,
 shipping_fee_rule, delivery_days_min, delivery_days_max, rating_avg, rating_count)
SELECT 'TXT-BLK-0001', 'Organic Cotton Throw Blanket', 'Breathable 320 gsm cotton blanket',
       'Machine washable throw blanket suitable for sofa, bed, and travel.',
       'North Loom', id, '00012345678905', 'NL-THROW-320', 'new', 'USD', 39.99, 120, 0.850,
       JSON_OBJECT('l_cm', 180, 'w_cm', 130, 'h_cm', 1.5), JSON_ARRAY('OEKO-TEX'), NULL, NULL,
       12, 30, JSON_ARRAY('US','CA'), JSON_OBJECT('type','flat','fee',6.99), 3, 7, 4.6, 38
FROM categories WHERE code = 'textiles-blankets';

INSERT INTO products
(sku_id, title, subtitle, description, brand, category_id, gtin, mpn, condition_type, currency, price, inventory, weight_kg,
 dimensions_json, safety_certifications, age_min, age_max, warranty_months, return_policy_days, shipping_regions,
 shipping_fee_rule, delivery_days_min, delivery_days_max, rating_avg, rating_count)
SELECT 'TOY-STEM-0001', 'Magnetic STEM Building Tiles 64 Pack', 'CPSIA certified construction toy for ages 3+',
       'Colorful magnetic tiles for early spatial reasoning and open-ended building.',
       'BrightLab', id, '00012345678912', 'BL-MAG-64', 'new', 'USD', 29.50, 75, 1.200,
       JSON_OBJECT('l_cm', 26, 'w_cm', 20, 'h_cm', 8), JSON_ARRAY('CPSIA','ASTM F963'), 3, 10,
       6, 30, JSON_ARRAY('US','CA'), JSON_OBJECT('type','free_over','threshold',50,'fee',7.99), 2, 6, 4.8, 112
FROM categories WHERE code = 'toys-stem';

INSERT INTO products
(sku_id, title, subtitle, description, brand, category_id, gtin, mpn, condition_type, currency, price, inventory, weight_kg,
 dimensions_json, safety_certifications, age_min, age_max, warranty_months, return_policy_days, shipping_regions,
 shipping_fee_rule, delivery_days_min, delivery_days_max, rating_avg, rating_count)
SELECT 'ELC-CHG-0001', '65W USB-C GaN Fast Charger', 'Compact charger with USB-C PD output',
       'Fast wall charger for laptops, tablets, and phones that support USB-C Power Delivery.',
       'VoltPeak', id, '00012345678929', 'VP-GAN-65C', 'new', 'USD', 34.99, 210, 0.160,
       JSON_OBJECT('l_cm', 5.2, 'w_cm', 4.1, 'h_cm', 3.2), JSON_ARRAY('FCC','CE','UL'), NULL, NULL,
       24, 30, JSON_ARRAY('US','CA'), JSON_OBJECT('type','flat','fee',4.99), 2, 5, 4.5, 260
FROM categories WHERE code = 'electronics-chargers';

INSERT INTO products
(sku_id, title, subtitle, description, brand, category_id, gtin, mpn, condition_type, currency, price, inventory, weight_kg,
 dimensions_json, safety_certifications, age_min, age_max, warranty_months, return_policy_days, shipping_regions,
 shipping_fee_rule, delivery_days_min, delivery_days_max, rating_avg, rating_count)
SELECT 'HOM-LGT-0001', 'LED Desk Lamp with Adjustable Arm', 'Dimmable desk lamp with neutral white mode',
       'Space-saving LED task lamp for desks, nightstands, and reading corners.',
       'LumaNest', id, '00012345678936', 'LN-DESK-8W', 'new', 'USD', 24.99, 58, 0.920,
       JSON_OBJECT('l_cm', 36, 'w_cm', 14, 'h_cm', 42), JSON_ARRAY('FCC','CE'), NULL, NULL,
       18, 30, JSON_ARRAY('US','CA'), JSON_OBJECT('type','flat','fee',5.99), 3, 8, 4.3, 74
FROM categories WHERE code = 'home-lighting';

INSERT INTO products
(sku_id, title, subtitle, description, brand, category_id, gtin, mpn, condition_type, currency, price, inventory, weight_kg,
 dimensions_json, safety_certifications, age_min, age_max, warranty_months, return_policy_days, shipping_regions,
 shipping_fee_rule, delivery_days_min, delivery_days_max, rating_avg, rating_count)
SELECT 'DAY-CLN-0001', 'Plant-Based Multi-Surface Cleaner 2 Pack', 'Unscented daily cleaner for kitchen and bath',
       'Ready-to-use cleaner for sealed counters, tile, and appliance exteriors.',
       'ClearKind', id, '00012345678943', 'CK-MSC-2PK', 'new', 'USD', 12.99, 340, 1.050,
       JSON_OBJECT('l_cm', 22, 'w_cm', 12, 'h_cm', 28), JSON_ARRAY('EPA Safer Choice'), NULL, NULL,
       0, 30, JSON_ARRAY('US','CA'), JSON_OBJECT('type','flat','fee',6.99), 2, 6, 4.4, 91
FROM categories WHERE code = 'daily-cleaning';

INSERT INTO product_attributes
(product_id, attr_key, attr_value_text, attr_value_num, attr_value_bool, attr_unit, value_type, normalized_value, normalized_num)
SELECT id, 'material', 'organic cotton', NULL, NULL, NULL, 'text', 'organic cotton', NULL FROM products WHERE sku_id = 'TXT-BLK-0001';
INSERT INTO product_attributes
(product_id, attr_key, attr_value_text, attr_value_num, attr_value_bool, attr_unit, value_type, normalized_value, normalized_num)
SELECT id, 'fabric_gsm', NULL, 320, NULL, 'gsm', 'number', '320 gsm', 320 FROM products WHERE sku_id = 'TXT-BLK-0001';

INSERT INTO product_attributes
(product_id, attr_key, attr_value_text, attr_value_num, attr_value_bool, attr_unit, value_type, normalized_value, normalized_num)
SELECT id, 'material', 'ABS plastic with magnets', NULL, NULL, NULL, 'text', 'abs plastic with magnets', NULL FROM products WHERE sku_id = 'TOY-STEM-0001';
INSERT INTO product_attributes
(product_id, attr_key, attr_value_text, attr_value_num, attr_value_bool, attr_unit, value_type, normalized_value, normalized_num)
SELECT id, 'age_range', '3-10 years', NULL, NULL, NULL, 'text', '3-10 years', NULL FROM products WHERE sku_id = 'TOY-STEM-0001';

INSERT INTO product_attributes
(product_id, attr_key, attr_value_text, attr_value_num, attr_value_bool, attr_unit, value_type, normalized_value, normalized_num)
SELECT id, 'power_w', NULL, 65, NULL, 'W', 'number', '65 W', 65 FROM products WHERE sku_id = 'ELC-CHG-0001';
INSERT INTO product_attributes
(product_id, attr_key, attr_value_text, attr_value_num, attr_value_bool, attr_unit, value_type, normalized_value, normalized_num)
SELECT id, 'connector_type', 'USB-C', NULL, NULL, NULL, 'enum', 'USB-C', NULL FROM products WHERE sku_id = 'ELC-CHG-0001';

INSERT INTO product_attributes
(product_id, attr_key, attr_value_text, attr_value_num, attr_value_bool, attr_unit, value_type, normalized_value, normalized_num)
SELECT id, 'power_w', NULL, 8, NULL, 'W', 'number', '8 W', 8 FROM products WHERE sku_id = 'HOM-LGT-0001';
INSERT INTO product_attributes
(product_id, attr_key, attr_value_text, attr_value_num, attr_value_bool, attr_unit, value_type, normalized_value, normalized_num)
SELECT id, 'dimmable', NULL, NULL, 1, NULL, 'boolean', 'true', NULL FROM products WHERE sku_id = 'HOM-LGT-0001';

INSERT INTO product_attributes
(product_id, attr_key, attr_value_text, attr_value_num, attr_value_bool, attr_unit, value_type, normalized_value, normalized_num)
SELECT id, 'material', 'plant-based surfactants', NULL, NULL, NULL, 'text', 'plant-based surfactants', NULL FROM products WHERE sku_id = 'DAY-CLN-0001';
INSERT INTO product_attributes
(product_id, attr_key, attr_value_text, attr_value_num, attr_value_bool, attr_unit, value_type, normalized_value, normalized_num)
SELECT id, 'scent', 'unscented', NULL, NULL, NULL, 'text', 'unscented', NULL FROM products WHERE sku_id = 'DAY-CLN-0001';

INSERT INTO product_media (product_id, media_type, url, alt_text, sort_order)
SELECT id, 'image', CONCAT('https://cdn.querymart.local/products/', sku_id, '/main.jpg'), CONCAT(title, ' main image'), 0
FROM products;

INSERT INTO product_faqs (product_id, question, answer, sort_order)
SELECT id, 'What fields should agents rely on?', 'Use sku_id, category_code, normalized attributes, price, inventory, shipping, return, and warranty fields as stable v1 contract fields.', 0
FROM products;

INSERT INTO product_feed_events (product_id, sku_id, event_type, payload)
SELECT id, sku_id, 'created', JSON_OBJECT('sku_id', sku_id, 'status', status, 'updated_at', updated_at)
FROM products;

INSERT INTO api_clients (client_id, client_name, api_key_hash, rate_limit_per_minute)
VALUES
('demo-agent', 'Demo Agent Client', SHA2('demo-agent-key-change-me', 256), 120);
