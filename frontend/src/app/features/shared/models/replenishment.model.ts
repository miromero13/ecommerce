export type ReplenishmentStatus = 'requested' | 'accepted' | 'preparing' | 'awaiting_receipt' | 'delivered';

export interface ReplenishmentItem {
  variant_id: string;
  product_name: string;
  sku: string;
  size_name: string | null;
  color_name: string | null;
  provider_quantity: number;
  requested_quantity: number;
}

export interface ReplenishmentRequest {
  id: string;
  provider_id: string;
  branch_id: string;
  requested_by: string;
  status: ReplenishmentStatus;
  created_at: string;
  updated_at: string;
  items: ReplenishmentItem[];
}
