export interface QrPayment {
  reference: string;
  purpose: 'order' | 'sale' | 'reservation_deposit';
  source_id: string | null;
  amount: number;
  currency: string;
  status: 'pending' | 'paid' | 'used' | 'expired';
  expires_at: string;
  paid_at: string | null;
  qr_payload: string;
  qr_image: string;
}
