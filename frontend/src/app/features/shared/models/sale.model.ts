import { ApiResponse } from '../../../core/models/api.model';
import { PaymentMethodEnum, PaymentStatusEnum } from './order.model';

export type SaleStatus = 'completed' | 'cancelled';

export interface SaleItem {
  id: string;
  sale_id: string;
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

export interface Sale {
  id: string;
  branch_id: string;
  branch_name: string;
  user_id: string;
  reservation_id: string | null;
  status: SaleStatus;
  payment_method: PaymentMethodEnum;
  payment_status: PaymentStatusEnum;
  cash_reference: string | null;
  subtotal: string;
  discount_amount: string;
  total_amount: string;
  currency: string;
  created_at: string;
  updated_at: string | null;
  items: SaleItem[];
}

export interface CreateSaleItemRequest {
  variant_id: string;
  quantity: number;
}

export interface CreateSaleRequest {
  branch_id?: string | null;
  reservation_id?: string | null;
  payment_method: PaymentMethodEnum;
  cash_reference?: string | null;
  items: CreateSaleItemRequest[];
}

export type SaleResponse = ApiResponse<Sale>;
export type SalesListResponse = ApiResponse<Sale[]>;
