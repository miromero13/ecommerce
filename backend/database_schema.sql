-- ========================================================
-- FashionStore eCommerce Platform - Complete Database Schema
-- Compatible with PostgreSQL 14 / 15 / 16 / 17 / 18
-- Generated from SQLAlchemy ORM Models (37 tables)
-- ========================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- PostgreSQL enums must exist before the tables that use them.
-- Labels match SQLAlchemy Enum names, including the current Spanish roles.
CREATE TYPE tenantstatusenum AS ENUM ('active', 'trial', 'suspended');
CREATE TYPE billingcycleenum AS ENUM ('monthly', 'yearly');
CREATE TYPE subscriptionstatusenum AS ENUM ('active', 'trialing', 'past_due', 'canceled');
CREATE TYPE subscriptionpaymentmethodenum AS ENUM ('simulated_card', 'cash', 'stripe');
CREATE TYPE genderenum AS ENUM ('masculino', 'femenino');
CREATE TYPE rolenum AS ENUM ('superadministrador', 'administrador', 'cliente', 'proveedor', 'encargado', 'cajero', 'delivery');
CREATE TYPE providerstatusenum AS ENUM ('active', 'suspended');
CREATE TYPE cartstatusenum AS ENUM ('active', 'checkout_pending', 'checked_out', 'cancelled');
CREATE TYPE orderstatusenum AS ENUM ('pending', 'paid', 'failed', 'cancelled');
CREATE TYPE paymentmethodenum AS ENUM ('cash', 'stripe');
CREATE TYPE paymentstatusenum AS ENUM ('pending', 'paid', 'failed');
CREATE TYPE fulfillmentstatusenum AS ENUM ('pending_pickup', 'ready_for_pickup', 'collected', 'expired', 'cancelled');
CREATE TYPE replenishmentstatusenum AS ENUM ('requested', 'accepted', 'preparing', 'awaiting_receipt', 'delivered');
CREATE TYPE productstatusenum AS ENUM ('pending', 'active', 'inactive');
CREATE TYPE reservationstatusenum AS ENUM ('pending', 'confirmed', 'attended', 'purchase_pending', 'sold', 'not_sold', 'cancelled', 'expired');
CREATE TYPE inventorymovementtypeenum AS ENUM ('income', 'outcome', 'transfer_in', 'transfer_out');
CREATE TYPE salestatusenum AS ENUM ('completed', 'cancelled');

CREATE TABLE collaborative_embeddings (
	id UUID NOT NULL, 
	subject_type VARCHAR(16) NOT NULL, 
	subject_id UUID NOT NULL, 
	vector TEXT NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_collaborative_embedding_subject UNIQUE (subject_type, subject_id)
)

;


CREATE TABLE colors (
	id UUID NOT NULL, 
	name VARCHAR NOT NULL, 
	hex_code VARCHAR, 
	PRIMARY KEY (id), 
	UNIQUE (name)
)

;


CREATE TABLE saas_plans (
	id VARCHAR(50) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	slug VARCHAR(100) NOT NULL, 
	description VARCHAR(500), 
	price_monthly NUMERIC(10, 2) NOT NULL, 
	price_yearly NUMERIC(10, 2) NOT NULL, 
	max_branches INTEGER NOT NULL, 
	max_garments INTEGER NOT NULL, 
	features JSON NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;


CREATE TABLE sizes (
	id UUID NOT NULL, 
	name VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
)

;


CREATE TABLE stripe_events (
	id UUID NOT NULL, 
	stripe_event_id VARCHAR NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
)

;


CREATE TABLE tenants (
	id UUID NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	slug VARCHAR(120) NOT NULL, 
	contact_email VARCHAR(255) NOT NULL, 
	currency VARCHAR(10) NOT NULL, 
	country VARCHAR(80), 
	status tenantstatusenum NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
)

;


CREATE TABLE branches (
	id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	name VARCHAR NOT NULL, 
	city VARCHAR NOT NULL, 
	is_default BOOLEAN NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	CONSTRAINT uq_branches_name_tenant UNIQUE (name, tenant_id)
)

;


CREATE TABLE categories (
	id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	name VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
)

;


CREATE TABLE seasons (
	id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	name VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
)

;


CREATE TABLE tenant_subscriptions (
	id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	plan_id VARCHAR(50) NOT NULL, 
	billing_cycle billingcycleenum NOT NULL, 
	status subscriptionstatusenum NOT NULL, 
	payment_method subscriptionpaymentmethodenum NOT NULL, 
	start_date TIMESTAMP WITH TIME ZONE NOT NULL, 
	end_date TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(plan_id) REFERENCES saas_plans (id) ON DELETE RESTRICT
)

;


CREATE TABLE collections (
	id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	name VARCHAR NOT NULL, 
	season_id UUID, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(season_id) REFERENCES seasons (id)
)

;


CREATE TABLE users (
	id UUID NOT NULL, 
	tenant_id UUID, 
	name VARCHAR NOT NULL, 
	email VARCHAR NOT NULL, 
	hashed_password VARCHAR NOT NULL, 
	gender genderenum NOT NULL, 
	rol rolenum NOT NULL, 
	branch_id UUID, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(branch_id) REFERENCES branches (id)
)

;


CREATE TABLE conversations (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;


CREATE TABLE device_tokens (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	token VARCHAR NOT NULL, 
	platform VARCHAR NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_device_token_user_token UNIQUE (user_id, token), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;


CREATE TABLE notifications (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	title VARCHAR NOT NULL, 
	body VARCHAR NOT NULL, 
	data JSON NOT NULL, 
	read_at TIMESTAMP WITH TIME ZONE, 
	dedupe_key VARCHAR, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;


CREATE TABLE promotion_codes (
	id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	code VARCHAR(40) NOT NULL, 
	discount_type VARCHAR(20) NOT NULL, 
	discount_value NUMERIC(10, 2) NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE, 
	valid_until TIMESTAMP WITH TIME ZONE, 
	branch_id UUID, 
	created_by UUID NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(branch_id) REFERENCES branches (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
)

;


CREATE TABLE providers (
	id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	business_name VARCHAR NOT NULL, 
	contact_name VARCHAR NOT NULL, 
	phone VARCHAR, 
	status providerstatusenum NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;


CREATE TABLE user_body_profiles (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	top_size VARCHAR(32), 
	bottom_size VARCHAR(32), 
	shoe_size VARCHAR(32), 
	body_shape VARCHAR(64), 
	fit_preference VARCHAR(64), 
	notes TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_user_body_profiles_user_id UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;


CREATE TABLE carts (
	id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	promotion_code_id UUID, 
	status cartstatusenum NOT NULL, 
	subtotal NUMERIC(10, 2) NOT NULL, 
	discount_amount NUMERIC(10, 2) NOT NULL, 
	total_amount NUMERIC(10, 2) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(promotion_code_id) REFERENCES promotion_codes (id)
)

;


CREATE TABLE conversation_messages (
	id UUID NOT NULL, 
	conversation_id UUID NOT NULL, 
	role VARCHAR(9) NOT NULL, 
	content TEXT NOT NULL, 
	message_data JSON, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_conversation_messages_role CHECK (role IN ('user', 'assistant')), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
)

;


CREATE TABLE orders (
	id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	promotion_code_id UUID, 
	status orderstatusenum NOT NULL, 
	payment_method paymentmethodenum NOT NULL, 
	payment_status paymentstatusenum NOT NULL, 
	stripe_payment_intent_id VARCHAR, 
	cash_reference VARCHAR, 
	pickup_branch_id UUID, 
	pickup_expires_at TIMESTAMP WITH TIME ZONE, 
	pickup_code VARCHAR, 
	fulfillment_status fulfillmentstatusenum, 
	subtotal NUMERIC(10, 2) NOT NULL, 
	discount_amount NUMERIC(10, 2) NOT NULL, 
	total_amount NUMERIC(10, 2) NOT NULL, 
	currency VARCHAR NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(promotion_code_id) REFERENCES promotion_codes (id), 
	FOREIGN KEY(pickup_branch_id) REFERENCES branches (id), 
	UNIQUE (pickup_code)
)

;


CREATE TABLE products (
	id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	name VARCHAR NOT NULL, 
	description TEXT, 
	provider_id UUID, 
	category_id UUID NOT NULL, 
	collection_id UUID, 
	discount_type VARCHAR(20), 
	discount_value NUMERIC(10, 2), 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(provider_id) REFERENCES providers (id), 
	FOREIGN KEY(category_id) REFERENCES categories (id), 
	FOREIGN KEY(collection_id) REFERENCES collections (id)
)

;


CREATE TABLE promotion_code_usages (
	id UUID NOT NULL, 
	promotion_code_id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	used_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_promotion_code_usage_user UNIQUE (promotion_code_id, user_id), 
	FOREIGN KEY(promotion_code_id) REFERENCES promotion_codes (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;


CREATE TABLE replenishment_requests (
	id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	provider_id UUID NOT NULL, 
	branch_id UUID NOT NULL, 
	requested_by UUID NOT NULL, 
	status replenishmentstatusenum NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	accepted_by UUID, 
	accepted_at TIMESTAMP WITH TIME ZONE, 
	preparing_by UUID, 
	preparing_at TIMESTAMP WITH TIME ZONE, 
	awaiting_receipt_by UUID, 
	awaiting_receipt_at TIMESTAMP WITH TIME ZONE, 
	delivered_by UUID, 
	delivered_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(provider_id) REFERENCES providers (id), 
	FOREIGN KEY(branch_id) REFERENCES branches (id), 
	FOREIGN KEY(requested_by) REFERENCES users (id), 
	FOREIGN KEY(accepted_by) REFERENCES users (id), 
	FOREIGN KEY(preparing_by) REFERENCES users (id), 
	FOREIGN KEY(awaiting_receipt_by) REFERENCES users (id), 
	FOREIGN KEY(delivered_by) REFERENCES users (id)
)

;


CREATE TABLE payment_attempts (
	id UUID NOT NULL, 
	order_id UUID NOT NULL, 
	cart_id UUID NOT NULL, 
	stripe_payment_intent_id VARCHAR, 
	status VARCHAR NOT NULL, 
	idempotency_key VARCHAR NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id), 
	FOREIGN KEY(cart_id) REFERENCES carts (id), 
	UNIQUE (stripe_payment_intent_id), 
	UNIQUE (idempotency_key)
)

;


CREATE TABLE product_variants (
	id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	sku VARCHAR NOT NULL, 
	price NUMERIC(10, 2) NOT NULL, 
	size_id UUID, 
	color_id UUID, 
	image_url VARCHAR, 
	image_public_id VARCHAR, 
	garment_points JSON, 
	status productstatusenum NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_product_variant_combo UNIQUE (product_id, size_id, color_id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	FOREIGN KEY(size_id) REFERENCES sizes (id), 
	FOREIGN KEY(color_id) REFERENCES colors (id)
)

;


CREATE TABLE reservations (
	id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	branch_id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	cart_id UUID, 
	visit_date DATE NOT NULL, 
	expires_at DATE NOT NULL, 
	status reservationstatusenum NOT NULL, 
	total_amount NUMERIC(10, 2) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(branch_id) REFERENCES branches (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(cart_id) REFERENCES carts (id)
)

;


CREATE TABLE cart_items (
	id UUID NOT NULL, 
	cart_id UUID NOT NULL, 
	reservation_id UUID, 
	variant_id UUID NOT NULL, 
	quantity INTEGER NOT NULL, 
	unit_price NUMERIC(10, 2) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_cart_item_cart_variant UNIQUE (cart_id, variant_id), 
	FOREIGN KEY(cart_id) REFERENCES carts (id), 
	FOREIGN KEY(reservation_id) REFERENCES reservations (id), 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id)
)

;


CREATE TABLE inventory (
	id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	variant_id UUID NOT NULL, 
	branch_id UUID NOT NULL, 
	quantity INTEGER NOT NULL, 
	reserved_quantity INTEGER NOT NULL, 
	minimum_stock INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_inventory_variant_branch UNIQUE (variant_id, branch_id), 
	CONSTRAINT ck_inventory_minimum_stock_non_negative CHECK (minimum_stock >= 0), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id), 
	FOREIGN KEY(branch_id) REFERENCES branches (id)
)

;


CREATE TABLE inventory_movements (
	id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	variant_id UUID NOT NULL, 
	branch_id UUID NOT NULL, 
	movement_type inventorymovementtypeenum NOT NULL, 
	quantity INTEGER NOT NULL, 
	reference_branch_id UUID, 
	note TEXT, 
	created_by UUID, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id), 
	FOREIGN KEY(branch_id) REFERENCES branches (id), 
	FOREIGN KEY(reference_branch_id) REFERENCES branches (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
)

;


CREATE TABLE order_items (
	id UUID NOT NULL, 
	order_id UUID NOT NULL, 
	reservation_id UUID, 
	variant_id UUID NOT NULL, 
	quantity INTEGER NOT NULL, 
	unit_price NUMERIC(10, 2) NOT NULL, 
	line_total NUMERIC(10, 2) NOT NULL, 
	product_id UUID NOT NULL, 
	product_name VARCHAR NOT NULL, 
	variant_sku VARCHAR NOT NULL, 
	size_id UUID, 
	color_id UUID, 
	image_url VARCHAR, 
	image_public_id VARCHAR, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_order_item_order_variant UNIQUE (order_id, variant_id), 
	FOREIGN KEY(order_id) REFERENCES orders (id), 
	FOREIGN KEY(reservation_id) REFERENCES reservations (id), 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id)
)

;


CREATE TABLE provider_variant_availability (
	id UUID NOT NULL, 
	provider_id UUID NOT NULL, 
	variant_id UUID NOT NULL, 
	quantity INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_provider_variant_availability UNIQUE (provider_id, variant_id), 
	CONSTRAINT ck_provider_variant_availability_quantity_non_negative CHECK (quantity >= 0), 
	FOREIGN KEY(provider_id) REFERENCES providers (id) ON DELETE CASCADE, 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id) ON DELETE CASCADE
)

;


CREATE TABLE replenishment_request_items (
	id UUID NOT NULL, 
	request_id UUID NOT NULL, 
	variant_id UUID NOT NULL, 
	requested_quantity INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_replenishment_request_variant UNIQUE (request_id, variant_id), 
	CONSTRAINT ck_replenishment_requested_quantity_positive CHECK (requested_quantity > 0), 
	FOREIGN KEY(request_id) REFERENCES replenishment_requests (id) ON DELETE CASCADE, 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id)
)

;


CREATE TABLE reservation_items (
	id UUID NOT NULL, 
	reservation_id UUID NOT NULL, 
	variant_id UUID NOT NULL, 
	quantity INTEGER NOT NULL, 
	unit_price NUMERIC(10, 2) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_reservation_item_reservation_variant UNIQUE (reservation_id, variant_id), 
	FOREIGN KEY(reservation_id) REFERENCES reservations (id), 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id)
)

;


CREATE TABLE sales (
	id UUID NOT NULL, 
	tenant_id UUID NOT NULL, 
	branch_id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	reservation_id UUID, 
	status salestatusenum NOT NULL, 
	payment_method paymentmethodenum NOT NULL, 
	payment_status paymentstatusenum NOT NULL, 
	cash_reference VARCHAR, 
	subtotal NUMERIC(10, 2) NOT NULL, 
	discount_amount NUMERIC(10, 2) NOT NULL, 
	total_amount NUMERIC(10, 2) NOT NULL, 
	currency VARCHAR NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(branch_id) REFERENCES branches (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(reservation_id) REFERENCES reservations (id)
)

;


CREATE TABLE user_product_interactions (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	product_id UUID NOT NULL, 
	interaction_type VARCHAR(32) NOT NULL, 
	weight INTEGER NOT NULL, 
	order_id UUID, 
	variant_id UUID, 
	branch_id UUID, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_interaction_order_product_type UNIQUE (order_id, product_id, interaction_type), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id), 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id), 
	FOREIGN KEY(branch_id) REFERENCES branches (id)
)

;


CREATE TABLE sale_items (
	id UUID NOT NULL, 
	sale_id UUID NOT NULL, 
	variant_id UUID NOT NULL, 
	quantity INTEGER NOT NULL, 
	unit_price NUMERIC(10, 2) NOT NULL, 
	line_total NUMERIC(10, 2) NOT NULL, 
	product_id UUID NOT NULL, 
	product_name VARCHAR NOT NULL, 
	variant_sku VARCHAR NOT NULL, 
	size_id UUID, 
	color_id UUID, 
	image_url VARCHAR, 
	image_public_id VARCHAR, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_sale_item_sale_variant UNIQUE (sale_id, variant_id), 
	FOREIGN KEY(sale_id) REFERENCES sales (id), 
	FOREIGN KEY(variant_id) REFERENCES product_variants (id)
)

;

-- Explicit indexes are not included in CREATE TABLE output from SQLAlchemy.
CREATE INDEX ix_colors_id ON colors (id);
CREATE UNIQUE INDEX ix_saas_plans_slug ON saas_plans (slug);
CREATE INDEX ix_sizes_id ON sizes (id);
CREATE UNIQUE INDEX ix_stripe_events_stripe_event_id ON stripe_events (stripe_event_id);
CREATE INDEX ix_tenants_id ON tenants (id);
CREATE UNIQUE INDEX ix_tenants_slug ON tenants (slug);
CREATE INDEX ix_branches_id ON branches (id);
CREATE INDEX ix_branches_tenant_id ON branches (tenant_id);
CREATE INDEX ix_categories_id ON categories (id);
CREATE INDEX ix_categories_tenant_id ON categories (tenant_id);
CREATE INDEX ix_seasons_id ON seasons (id);
CREATE INDEX ix_seasons_tenant_id ON seasons (tenant_id);
CREATE INDEX ix_tenant_subscriptions_id ON tenant_subscriptions (id);
CREATE INDEX ix_tenant_subscriptions_plan_id ON tenant_subscriptions (plan_id);
CREATE INDEX ix_tenant_subscriptions_status ON tenant_subscriptions (status);
CREATE INDEX ix_tenant_subscriptions_tenant_id ON tenant_subscriptions (tenant_id);
CREATE INDEX ix_collections_id ON collections (id);
CREATE INDEX ix_collections_season_id ON collections (season_id);
CREATE INDEX ix_collections_tenant_id ON collections (tenant_id);
CREATE INDEX ix_users_branch_id ON users (branch_id);
CREATE UNIQUE INDEX ix_users_email ON users (email);
CREATE INDEX ix_users_id ON users (id);
CREATE INDEX ix_users_tenant_id ON users (tenant_id);
CREATE INDEX ix_conversations_created_at ON conversations (created_at);
CREATE INDEX ix_conversations_id ON conversations (id);
CREATE UNIQUE INDEX ix_conversations_user_id ON conversations (user_id);
CREATE INDEX ix_device_tokens_id ON device_tokens (id);
CREATE UNIQUE INDEX ix_device_tokens_token ON device_tokens (token);
CREATE INDEX ix_device_tokens_user_id ON device_tokens (user_id);
CREATE UNIQUE INDEX ix_notifications_dedupe_key ON notifications (dedupe_key);
CREATE INDEX ix_notifications_id ON notifications (id);
CREATE INDEX ix_notifications_user_id ON notifications (user_id);
CREATE INDEX ix_promotion_codes_branch_id ON promotion_codes (branch_id);
CREATE UNIQUE INDEX ix_promotion_codes_code ON promotion_codes (code);
CREATE INDEX ix_promotion_codes_created_by ON promotion_codes (created_by);
CREATE INDEX ix_promotion_codes_id ON promotion_codes (id);
CREATE INDEX ix_promotion_codes_tenant_id ON promotion_codes (tenant_id);
CREATE INDEX ix_providers_id ON providers (id);
CREATE INDEX ix_providers_tenant_id ON providers (tenant_id);
CREATE UNIQUE INDEX ix_providers_user_id ON providers (user_id);
CREATE INDEX ix_user_body_profiles_id ON user_body_profiles (id);
CREATE INDEX ix_user_body_profiles_user_id ON user_body_profiles (user_id);
CREATE INDEX ix_carts_id ON carts (id);
CREATE INDEX ix_carts_promotion_code_id ON carts (promotion_code_id);
CREATE INDEX ix_carts_tenant_id ON carts (tenant_id);
CREATE UNIQUE INDEX ix_carts_user_id ON carts (user_id);
CREATE INDEX ix_conversation_messages_conversation_id ON conversation_messages (conversation_id);
CREATE INDEX ix_conversation_messages_created_at ON conversation_messages (created_at);
CREATE INDEX ix_conversation_messages_id ON conversation_messages (id);
CREATE INDEX ix_orders_id ON orders (id);
CREATE INDEX ix_orders_pickup_branch_id ON orders (pickup_branch_id);
CREATE INDEX ix_orders_promotion_code_id ON orders (promotion_code_id);
CREATE INDEX ix_orders_stripe_payment_intent_id ON orders (stripe_payment_intent_id);
CREATE INDEX ix_orders_tenant_id ON orders (tenant_id);
CREATE INDEX ix_orders_user_id ON orders (user_id);
CREATE INDEX ix_products_category_id ON products (category_id);
CREATE INDEX ix_products_collection_id ON products (collection_id);
CREATE INDEX ix_products_id ON products (id);
CREATE INDEX ix_products_provider_id ON products (provider_id);
CREATE INDEX ix_products_tenant_id ON products (tenant_id);
CREATE INDEX ix_promotion_code_usages_id ON promotion_code_usages (id);
CREATE INDEX ix_promotion_code_usages_promotion_code_id ON promotion_code_usages (promotion_code_id);
CREATE INDEX ix_promotion_code_usages_user_id ON promotion_code_usages (user_id);
CREATE INDEX ix_replenishment_requests_branch_id ON replenishment_requests (branch_id);
CREATE INDEX ix_replenishment_requests_id ON replenishment_requests (id);
CREATE INDEX ix_replenishment_requests_provider_id ON replenishment_requests (provider_id);
CREATE INDEX ix_replenishment_requests_status ON replenishment_requests (status);
CREATE INDEX ix_replenishment_requests_tenant_id ON replenishment_requests (tenant_id);
CREATE INDEX ix_payment_attempts_cart_id ON payment_attempts (cart_id);
CREATE INDEX ix_payment_attempts_order_id ON payment_attempts (order_id);
CREATE INDEX ix_product_variants_color_id ON product_variants (color_id);
CREATE INDEX ix_product_variants_id ON product_variants (id);
CREATE INDEX ix_product_variants_product_id ON product_variants (product_id);
CREATE INDEX ix_product_variants_size_id ON product_variants (size_id);
CREATE UNIQUE INDEX ix_product_variants_sku ON product_variants (sku);
CREATE INDEX ix_product_variants_tenant_id ON product_variants (tenant_id);
CREATE INDEX ix_reservations_branch_id ON reservations (branch_id);
CREATE UNIQUE INDEX ix_reservations_cart_id ON reservations (cart_id);
CREATE INDEX ix_reservations_expires_at ON reservations (expires_at);
CREATE INDEX ix_reservations_id ON reservations (id);
CREATE INDEX ix_reservations_tenant_id ON reservations (tenant_id);
CREATE INDEX ix_reservations_user_id ON reservations (user_id);
CREATE INDEX ix_reservations_visit_date ON reservations (visit_date);
CREATE INDEX ix_cart_items_cart_id ON cart_items (cart_id);
CREATE INDEX ix_cart_items_id ON cart_items (id);
CREATE INDEX ix_cart_items_reservation_id ON cart_items (reservation_id);
CREATE INDEX ix_cart_items_variant_id ON cart_items (variant_id);
CREATE INDEX ix_inventory_branch_id ON inventory (branch_id);
CREATE INDEX ix_inventory_id ON inventory (id);
CREATE INDEX ix_inventory_tenant_id ON inventory (tenant_id);
CREATE INDEX ix_inventory_variant_id ON inventory (variant_id);
CREATE INDEX ix_inventory_movements_branch_id ON inventory_movements (branch_id);
CREATE INDEX ix_inventory_movements_created_by ON inventory_movements (created_by);
CREATE INDEX ix_inventory_movements_id ON inventory_movements (id);
CREATE INDEX ix_inventory_movements_reference_branch_id ON inventory_movements (reference_branch_id);
CREATE INDEX ix_inventory_movements_tenant_id ON inventory_movements (tenant_id);
CREATE INDEX ix_inventory_movements_variant_id ON inventory_movements (variant_id);
CREATE INDEX ix_order_items_id ON order_items (id);
CREATE INDEX ix_order_items_order_id ON order_items (order_id);
CREATE INDEX ix_order_items_product_id ON order_items (product_id);
CREATE INDEX ix_order_items_reservation_id ON order_items (reservation_id);
CREATE INDEX ix_order_items_variant_id ON order_items (variant_id);
CREATE INDEX ix_provider_variant_availability_id ON provider_variant_availability (id);
CREATE INDEX ix_provider_variant_availability_provider_id ON provider_variant_availability (provider_id);
CREATE INDEX ix_provider_variant_availability_variant_id ON provider_variant_availability (variant_id);
CREATE INDEX ix_replenishment_request_items_request_id ON replenishment_request_items (request_id);
CREATE INDEX ix_replenishment_request_items_variant_id ON replenishment_request_items (variant_id);
CREATE INDEX ix_reservation_items_id ON reservation_items (id);
CREATE INDEX ix_reservation_items_reservation_id ON reservation_items (reservation_id);
CREATE INDEX ix_reservation_items_variant_id ON reservation_items (variant_id);
CREATE INDEX ix_sales_branch_id ON sales (branch_id);
CREATE INDEX ix_sales_id ON sales (id);
CREATE UNIQUE INDEX ix_sales_reservation_id ON sales (reservation_id);
CREATE INDEX ix_sales_tenant_id ON sales (tenant_id);
CREATE INDEX ix_sales_user_id ON sales (user_id);
CREATE INDEX ix_user_product_interactions_branch_id ON user_product_interactions (branch_id);
CREATE INDEX ix_user_product_interactions_interaction_type ON user_product_interactions (interaction_type);
CREATE INDEX ix_user_product_interactions_order_id ON user_product_interactions (order_id);
CREATE INDEX ix_user_product_interactions_product_id ON user_product_interactions (product_id);
CREATE INDEX ix_user_product_interactions_user_id ON user_product_interactions (user_id);
CREATE INDEX ix_user_product_interactions_variant_id ON user_product_interactions (variant_id);

CREATE INDEX ix_sale_items_id ON sale_items (id);
CREATE INDEX ix_sale_items_product_id ON sale_items (product_id);
CREATE INDEX ix_sale_items_sale_id ON sale_items (sale_id);
CREATE INDEX ix_sale_items_variant_id ON sale_items (variant_id);