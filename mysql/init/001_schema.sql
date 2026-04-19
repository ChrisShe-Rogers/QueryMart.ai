CREATE DATABASE IF NOT EXISTS ai_commerce DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE ai_commerce;

SET NAMES utf8mb4;
SET time_zone = '+00:00';

CREATE TABLE categories (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  code VARCHAR(64) NOT NULL UNIQUE,
  name VARCHAR(128) NOT NULL,
  parent_id BIGINT NULL,
  level TINYINT NOT NULL DEFAULT 1,
  google_taxonomy_id VARCHAR(64) NULL,
  google_taxonomy_path VARCHAR(512) NULL,
  is_active TINYINT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_parent(parent_id),
  INDEX idx_level_active(level, is_active),
  CONSTRAINT fk_cat_parent FOREIGN KEY (parent_id) REFERENCES categories(id),
  CONSTRAINT chk_categories_level CHECK (level BETWEEN 1 AND 3)
) ENGINE=InnoDB;

CREATE TABLE attribute_definitions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  attr_key VARCHAR(128) NOT NULL UNIQUE,
  label VARCHAR(128) NOT NULL,
  value_type ENUM('text','number','boolean','enum') NOT NULL,
  canonical_unit VARCHAR(32) NULL,
  allowed_units JSON NULL,
  enum_values JSON NULL,
  description VARCHAR(512) NULL,
  is_filterable TINYINT NOT NULL DEFAULT 1,
  is_comparable TINYINT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE category_attribute_definitions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  category_id BIGINT NOT NULL,
  attribute_definition_id BIGINT NOT NULL,
  is_required TINYINT NOT NULL DEFAULT 0,
  display_order INT NOT NULL DEFAULT 0,
  UNIQUE KEY uk_category_attribute (category_id, attribute_definition_id),
  INDEX idx_category_attr_order(category_id, display_order),
  CONSTRAINT fk_cat_attr_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
  CONSTRAINT fk_cat_attr_definition FOREIGN KEY (attribute_definition_id) REFERENCES attribute_definitions(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE products (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  sku_id VARCHAR(64) NOT NULL UNIQUE,
  title VARCHAR(255) NOT NULL,
  subtitle VARCHAR(255) NULL,
  description TEXT NULL,
  brand VARCHAR(128) NULL,
  category_id BIGINT NOT NULL,
  gtin VARCHAR(32) NULL,
  upc VARCHAR(32) NULL,
  ean VARCHAR(32) NULL,
  mpn VARCHAR(64) NULL,
  condition_type ENUM('new','refurbished','used') NOT NULL DEFAULT 'new',
  status ENUM('draft','active','inactive') NOT NULL DEFAULT 'active',
  currency CHAR(3) NOT NULL DEFAULT 'USD',
  price DECIMAL(12,2) NOT NULL,
  inventory INT NOT NULL DEFAULT 0,
  weight_kg DECIMAL(10,3) NULL,
  dimensions_json JSON NULL,
  safety_certifications JSON NULL,
  age_min INT NULL,
  age_max INT NULL,
  warranty_months INT NOT NULL DEFAULT 0,
  return_policy_days INT NOT NULL DEFAULT 0,
  shipping_regions JSON NOT NULL,
  shipping_fee_rule JSON NULL,
  delivery_days_min INT NOT NULL DEFAULT 3,
  delivery_days_max INT NOT NULL DEFAULT 10,
  rating_avg DECIMAL(3,2) NULL,
  rating_count INT NOT NULL DEFAULT 0,
  schema_version VARCHAR(16) NOT NULL DEFAULT '1.0',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_cat_price (category_id, price),
  INDEX idx_brand (brand),
  INDEX idx_status_updated (status, updated_at),
  INDEX idx_delivery (delivery_days_min, delivery_days_max),
  FULLTEXT INDEX ftx_product_text (title, subtitle, description),
  CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES categories(id),
  CONSTRAINT chk_products_price CHECK (price >= 0),
  CONSTRAINT chk_products_inventory CHECK (inventory >= 0),
  CONSTRAINT chk_products_delivery CHECK (delivery_days_min >= 0 AND delivery_days_max >= delivery_days_min),
  CONSTRAINT chk_products_rating CHECK (rating_avg IS NULL OR (rating_avg >= 0 AND rating_avg <= 5))
) ENGINE=InnoDB;

CREATE TABLE product_attributes (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  product_id BIGINT NOT NULL,
  attr_key VARCHAR(128) NOT NULL,
  attr_value_text VARCHAR(255) NULL,
  attr_value_num DECIMAL(16,4) NULL,
  attr_value_bool TINYINT NULL,
  attr_unit VARCHAR(32) NULL,
  value_type ENUM('text','number','boolean','enum') NOT NULL DEFAULT 'text',
  is_filterable TINYINT NOT NULL DEFAULT 1,
  is_comparable TINYINT NOT NULL DEFAULT 1,
  normalized_value VARCHAR(255) NULL,
  normalized_num DECIMAL(16,4) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_product_attr (product_id, attr_key),
  INDEX idx_attr_text (attr_key, attr_value_text),
  INDEX idx_attr_num (attr_key, normalized_num),
  INDEX idx_attr_filterable (is_filterable, attr_key),
  CONSTRAINT fk_attr_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE product_media (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  product_id BIGINT NOT NULL,
  media_type ENUM('image','video','manual') NOT NULL,
  url VARCHAR(1024) NOT NULL,
  alt_text VARCHAR(255) NULL,
  sort_order INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_media_product (product_id, sort_order),
  CONSTRAINT fk_media_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE product_reviews (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  product_id BIGINT NOT NULL,
  reviewer_ref VARCHAR(128) NULL,
  rating TINYINT NOT NULL,
  title VARCHAR(255) NULL,
  body TEXT NULL,
  is_verified_purchase TINYINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_reviews_product (product_id, created_at),
  CONSTRAINT fk_reviews_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
  CONSTRAINT chk_reviews_rating CHECK (rating BETWEEN 1 AND 5)
) ENGINE=InnoDB;

CREATE TABLE product_faqs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  product_id BIGINT NOT NULL,
  question VARCHAR(512) NOT NULL,
  answer TEXT NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_faq_product (product_id, sort_order),
  CONSTRAINT fk_faq_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE api_clients (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  client_id VARCHAR(96) NOT NULL UNIQUE,
  client_name VARCHAR(128) NOT NULL,
  api_key_hash CHAR(64) NOT NULL,
  status ENUM('active','suspended','revoked') NOT NULL DEFAULT 'active',
  rate_limit_per_minute INT NOT NULL DEFAULT 120,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_api_clients_status (status)
) ENGINE=InnoDB;

CREATE TABLE api_request_logs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  client_id VARCHAR(96) NULL,
  request_path VARCHAR(255) NOT NULL,
  method VARCHAR(8) NOT NULL,
  status_code INT NOT NULL,
  ip VARCHAR(64) NULL,
  user_agent VARCHAR(512) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_api_logs_client_time (client_id, created_at),
  INDEX idx_api_logs_path_time (request_path, created_at)
) ENGINE=InnoDB;

CREATE TABLE carts (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  cart_token VARCHAR(128) NOT NULL UNIQUE,
  user_ref VARCHAR(128) NULL,
  agent_ref VARCHAR(128) NULL,
  currency CHAR(3) NOT NULL DEFAULT 'USD',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE cart_items (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  cart_id BIGINT NOT NULL,
  product_id BIGINT NOT NULL,
  quantity INT NOT NULL,
  unit_price DECIMAL(12,2) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_cart_product (cart_id, product_id),
  CONSTRAINT fk_cart_items_cart FOREIGN KEY (cart_id) REFERENCES carts(id) ON DELETE CASCADE,
  CONSTRAINT fk_cart_items_product FOREIGN KEY (product_id) REFERENCES products(id),
  CONSTRAINT chk_cart_items_quantity CHECK (quantity > 0),
  CONSTRAINT chk_cart_items_price CHECK (unit_price >= 0)
) ENGINE=InnoDB;

CREATE TABLE orders (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_no VARCHAR(64) NOT NULL UNIQUE,
  cart_id BIGINT NOT NULL,
  buyer_ref VARCHAR(128) NULL,
  status ENUM('previewed','pending_confirm','submitted','paid','cancelled') NOT NULL DEFAULT 'previewed',
  subtotal DECIMAL(12,2) NOT NULL,
  shipping_fee DECIMAL(12,2) NOT NULL DEFAULT 0,
  tax_fee DECIMAL(12,2) NOT NULL DEFAULT 0,
  total DECIMAL(12,2) NOT NULL,
  currency CHAR(3) NOT NULL,
  delivery_days_min INT NOT NULL,
  delivery_days_max INT NOT NULL,
  confirmation_code VARCHAR(16) NULL,
  confirmation_expires_at DATETIME NULL,
  confirmed_at DATETIME NULL,
  submitted_at DATETIME NULL,
  agent_ref VARCHAR(128) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_orders_status_created (status, created_at),
  INDEX idx_orders_buyer (buyer_ref),
  CONSTRAINT fk_orders_cart FOREIGN KEY (cart_id) REFERENCES carts(id),
  CONSTRAINT chk_orders_total CHECK (subtotal >= 0 AND shipping_fee >= 0 AND tax_fee >= 0 AND total >= 0),
  CONSTRAINT chk_orders_delivery CHECK (delivery_days_min >= 0 AND delivery_days_max >= delivery_days_min)
) ENGINE=InnoDB;

CREATE TABLE order_items (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_id BIGINT NOT NULL,
  product_id BIGINT NOT NULL,
  sku_id VARCHAR(64) NOT NULL,
  title VARCHAR(255) NOT NULL,
  quantity INT NOT NULL,
  unit_price DECIMAL(12,2) NOT NULL,
  line_total DECIMAL(12,2) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_order_items_order (order_id),
  CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  CONSTRAINT fk_order_items_product FOREIGN KEY (product_id) REFERENCES products(id),
  CONSTRAINT chk_order_items_quantity CHECK (quantity > 0),
  CONSTRAINT chk_order_items_total CHECK (unit_price >= 0 AND line_total >= 0)
) ENGINE=InnoDB;

CREATE TABLE order_audit_logs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_id BIGINT NOT NULL,
  actor_type ENUM('human','agent','system') NOT NULL,
  actor_ref VARCHAR(128) NULL,
  action VARCHAR(64) NOT NULL,
  payload JSON NULL,
  ip VARCHAR(64) NULL,
  user_agent VARCHAR(512) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_order_action (order_id, action),
  INDEX idx_audit_actor_time (actor_type, actor_ref, created_at),
  CONSTRAINT fk_audit_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE product_feed_events (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  product_id BIGINT NOT NULL,
  sku_id VARCHAR(64) NOT NULL,
  event_type ENUM('created','updated','deleted') NOT NULL,
  schema_version VARCHAR(16) NOT NULL DEFAULT '1.0',
  payload JSON NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_feed_created (created_at, id),
  INDEX idx_feed_sku (sku_id),
  CONSTRAINT fk_feed_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE OR REPLACE VIEW v_product_agent_specs AS
SELECT
  p.sku_id,
  p.schema_version,
  UTC_TIMESTAMP() AS generated_at,
  p.title,
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
  ) AS attributes
FROM products p
JOIN categories c ON c.id = p.category_id
LEFT JOIN product_attributes pa ON pa.product_id = p.id
WHERE p.status = 'active'
GROUP BY p.id, c.id;
