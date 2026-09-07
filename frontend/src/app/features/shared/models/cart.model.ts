import { ApiResponse } from '../../../core/models/api.model';

export interface CartItem {
  id: string;
  cart_id: string;
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

export interface Cart {
  id: string;
  user_id: string;
  status: 'active' | 'checked_out' | 'cancelled';
  subtotal: string;
  discount_amount: string;
  total_amount: string;
  item_count: number;
  created_at: string;
  updated_at: string | null;
  items: CartItem[];
}

export interface AddCartItemRequest {
  variant_id: string;
  quantity: number;
}

export interface UpdateCartItemRequest {
  quantity: number;
}

export type CartResponse = ApiResponse<Cart>;
