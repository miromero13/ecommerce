export type PaymentMethodEnum = 'cash' | 'stripe';
export type PaymentStatusEnum = 'pending' | 'paid' | 'failed';
export type FulfillmentStatusEnum = 'pending_pickup' | 'ready_for_pickup' | 'collected' | 'expired' | 'cancelled';

export interface OrderItem {
  id: string;
  order_id: string;
  variant_id: string;
  reservation_id?: string | null;
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
  payment_method: PaymentMethodEnum;
  payment_status: PaymentStatusEnum;
  stripe_payment_intent_id: string | null;
  cash_reference: string | null;
  pickup_branch_id: string | null;
  pickup_expires_at: string | null;
  pickup_code: string | null;
  fulfillment_status: FulfillmentStatusEnum;
  subtotal: string;
  discount_amount: string;
  promotion_code_id?: string | null;
  total_amount: string;
  currency: string;
  created_at: string;
  updated_at: string | null;
  items: OrderItem[];
}
