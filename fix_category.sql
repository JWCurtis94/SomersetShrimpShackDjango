-- Create temporary tables
CREATE TABLE temp_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE temp_product AS 
SELECT * FROM store_product;

-- Create categories from existing product categories
INSERT INTO temp_category (name, slug)
SELECT DISTINCT category, LOWER(REPLACE(REPLACE(category, ' ', '-'), '/', '-')) 
FROM store_product
WHERE category IS NOT NULL;

-- Add category_id column to temporary product table
ALTER TABLE temp_product ADD COLUMN category_id INTEGER;

-- Update products with category IDs
UPDATE temp_product
SET category_id = (
    SELECT id FROM temp_category 
    WHERE name = temp_product.category
)
WHERE category IS NOT NULL;

-- Drop original tables
DROP TABLE store_product;

-- Recreate original tables with proper schema
CREATE TABLE store_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE store_product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER NOT NULL,
    available BOOLEAN NOT NULL,
    created DATETIME NOT NULL,
    updated DATETIME NOT NULL,
    image VARCHAR(100) NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    featured BOOLEAN NOT NULL,
    category_id INTEGER NOT NULL REFERENCES store_category(id)
);

-- Copy data to new tables
INSERT INTO store_category SELECT * FROM temp_category;

INSERT INTO store_product (
    id, name, description, price, stock, available, created, updated, 
    image, slug, featured, category_id
)
SELECT 
    id, name, description, price, stock, available, created, updated, 
    image, slug, featured, category_id
FROM temp_product;

-- Drop temporary tables
DROP TABLE temp_category;
DROP TABLE temp_product;
