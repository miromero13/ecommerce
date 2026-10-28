/** 1P-CU18: one movement of a cashier's drawer. */
export interface CashMovement {
  id: string;
  type: 'sale' | 'order' | 'deposit' | 'withdrawal';
  method: 'cash' | 'qr';
  amount: string;
  cash_received: string | null;
  change_given: string | null;
  source_id: string | null;
  reason: string | null;
  created_at: string;
}

/** 1P-CU18: a cashier's drawer session in one branch (amounts in the company's currency). */
export interface CashSession {
  id: string;
  status: 'open' | 'closed';
  branch_id: string;
  branch_name: string | null;
  cashier_id: string;
  cashier_name: string | null;
  opening_amount: string;
  opened_at: string;
  expected_amount: string;
  counted_amount: string | null;
  difference: string | null;
  closing_note: string | null;
  closed_at: string | null;
  cash_sales: string;
  qr_sales: string;
  order_collections: string;
  deposits: string;
  withdrawals: string;
  change_given: string;
  sales_count: number;
  movements?: CashMovement[];
}
