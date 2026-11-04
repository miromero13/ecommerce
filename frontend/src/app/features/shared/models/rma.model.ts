export interface SameProductVariant {
  variant_id: string;
  sku: string;
  size_name?: string | null;
  color_name?: string | null;
  stock: number;
}

export interface EligibleOrderItem {
  order_item_id: string;
  product_id: string;
  product_name: string;
  variant_id: string;
  sku: string;
  size_name?: string | null;
  color_name?: string | null;
  unit_price: number;
  quantity: number;
  image_url?: string | null;
  eligible_for_rma: boolean;
  ineligible_reason?: string | null;
  same_product_variants: SameProductVariant[];
}

export interface EligibleOrder {
  order_id: string;
  order_number: string;
  delivered_at?: string | null;
  created_at: string;
  days_since_delivery: number;
  items: EligibleOrderItem[];
}

export interface RmaItem {
  id: string;
  order_item_id: string;
  product_name: string;
  original_sku: string;
  original_size?: string | null;
  original_color?: string | null;
  unit_price: number;
  quantity: number;
  image_url?: string | null;
  reason: string;
  preferred_resolution: string;
  requested_variant_id?: string | null;
  requested_variant_label?: string | null;
  customer_notes?: string | null;
  item_condition?: string | null;
  action?: string | null;
  status: string;
  replacement_variant_id?: string | null;
  replacement_variant_label?: string | null;
  branch_id?: string | null;
  branch_name?: string | null;
  inspection_notes?: string | null;
  quarantine_record?: string | null;
  refund_amount?: number | null;
  wallet_settlement_date?: string | null;
  settlement_status?: string | null;
}

export interface RmaRequest {
  id: string;
  tenant_id: string;
  order_id: string;
  order_number: string;
  user_id: string;
  customer_name: string;
  customer_email: string;
  rma_number: string;
  status: 'pending_inspection' | 'approved' | 'partially_approved' | 'rejected' | 'completed' | string;
  customer_notes?: string | null;
  pdf_url: string;
  created_at: string;
  updated_at?: string | null;
  items: RmaItem[];
}

export interface CreateRmaItemPayload {
  order_item_id: string;
  quantity: number;
  reason: string;
  preferred_resolution: string;
  requested_variant_id?: string | null;
  customer_notes?: string | null;
}

export interface CreateRmaRequestPayload {
  order_id: string;
  customer_notes?: string | null;
  items: CreateRmaItemPayload[];
}

export interface ReviewRmaItemPayload {
  status: 'approved' | 'rejected' | string;
  item_condition: 'intact' | 'factory_damaged' | 'customer_damaged' | string;
  action: 'restock_available' | 'scrap_quarantine' | 'return_to_customer' | string;
  resolution: 'exchange' | 'store_credit' | string;
  replacement_variant_id?: string | null;
  branch_id?: string | null;
  inspection_notes?: string | null;
}
