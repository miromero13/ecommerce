/** CU17: points of a customer in one company (10 points = 1 Bs). */
export interface LoyaltyBalance {
  tenant_id: string;
  tenant_name: string;
  points_balance: number;
  lifetime_points: number;
  tier: 'Bronce' | 'Plata' | 'Oro';
  balance_value: number;
  customer_email?: string;
}

export interface LoyaltyMovement {
  id: string;
  tenant_name: string;
  type: 'earn' | 'redeem' | 'refund';
  points: number;
  source_type: 'order' | 'sale';
  source_id: string;
  created_at: string;
}
