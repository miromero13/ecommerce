export interface OrderItem {
  id: string;
  order_id: string;
  variant_id: string;
  quantity: number;
  unit_price: string;
  line_total: string;
  product_id: string;
  product_name: string;
  variant_sku: string;
  size_id: string | null;
  color_id: string | null;
  size_name: string | null;
  color_name: string | null;
  image_url: string | null;
  image_public_id: string | null;
}

export interface Order {
  id: string;
  user_id: string;
  status: 'pending' | 'paid' | 'failed' | 'cancelled';
  payment_method: 'cash' | 'stripe';
  payment_status: 'pending' | 'paid' | 'failed';
  stripe_payment_intent_id: string | null;
  cash_reference: string | null;
  subtotal: string;
  discount_amount: string;
  total_amount: string;
  currency: string;
  created_at: string;
  updated_at: string | null;
  items: OrderItem[];
}
