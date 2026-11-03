/** CU19: Store Wallet models */
export interface WalletBalance {
  balance: number;
  currency: string;
}

export interface WalletRedeemResult {
  credited_amount: number;
  new_balance: number;
}

export interface WalletTransaction {
  id: string;
  type: 'credit' | 'debit';
  amount: number;
  balance_after: number;
  concept: 'gift_card_redeem' | 'order_payment' | 'sale_payment' | 'rma_refund';
  source_type?: string | null;
  source_id?: string | null;
  description?: string | null;
  created_at: string;
}

export interface WalletPayPayload {
  order_id: string;
  amount_to_debit: number;
}

export interface WalletCheckoutPayload {
  pickup_branch_id: string;
  delivery?: Record<string, any> | null;
  points_to_redeem?: number;
}
