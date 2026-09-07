import { ApiResponse } from '../../../core/models/api.model';

export type ReservationStatus = 'pending' | 'confirmed' | 'attended' | 'cancelled' | 'expired';

export interface ReservationItem {
  id: string;
  reservation_id: string;
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

export interface Reservation {
  id: string;
  branch_id: string;
  branch_name: string;
  user_id: string;
  visit_date: string;
  expires_at: string;
  status: ReservationStatus;
  total_amount: string;
  item_count: number;
  created_at: string;
  updated_at: string | null;
  items: ReservationItem[];
}

export interface ReservationItemRequest {
  variant_id: string;
  quantity: number;
}

export interface CreateReservationRequest {
  branch_id: string;
  visit_date: string;
  items: ReservationItemRequest[];
}

export type ReservationResponse = ApiResponse<Reservation>;
export type ReservationListResponse = ApiResponse<Reservation[]>;
