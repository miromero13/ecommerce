export type ReceiptKind = 'order' | 'sale' | 'reservation_deposit' | 'subscription';

/** Simple payment receipt (comprobante); not a tax invoice. */
export interface PaymentReceipt {
  id: string;
  number: string; // C-000001 (company) or P-000001 (platform)
  issuer: 'company' | 'platform';
  issuer_name: string;
  kind: ReceiptKind;
  kind_label: string;
  source_id: string;
  tenant_id: string;
  branch_id: string | null;
  customer_name: string | null;
  customer_email: string | null;
  payment_method: 'card' | 'qr' | 'cash';
  payment_method_label: string;
  currency: string;
  total: string;
  lines: { description: string; quantity: number; unit_price: string; total: string }[];
  summary: { label: string; amount: string }[];
  issued_at: string;
  emailed_at: string | null;
}
