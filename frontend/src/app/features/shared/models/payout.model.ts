export interface BankAccount {
  bank_name: string | null;
  bank_account_number: string | null;
  bank_account_holder: string | null;
}

export interface Settlement extends BankAccount {
  id: string;
  tenant_id: string;
  tenant_name: string | null;
  period_date: string;
  gross_amount: number;
  fee_amount: number;
  net_amount: number;
  transactions_count: number;
  currency: string;
  status: 'pending' | 'paid';
  transfer_reference: string | null;
  paid_at: string | null;
  created_at: string;
}

export interface PaymentTransaction {
  id: string;
  source_type: 'order' | 'sale' | 'reservation_deposit';
  method: 'card' | 'qr' | 'cash';
  gross_amount: number;
  fee_amount: number;
  net_amount: number;
  currency: string;
  settlement_id: string | null;
  created_at: string;
}

export interface PayoutSummary {
  currency: string;
  platform_fee_percent: number;
  pending_net_amount: number;
  transferred_net_amount: number;
  bank_account: BankAccount;
  recent_transactions: PaymentTransaction[];
}
