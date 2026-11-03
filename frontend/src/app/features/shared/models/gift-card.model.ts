/** CU18: Gift Card models */
export interface GiftCard {
  id: string;
  code: string;
  amount: number;
  balance: number;
  recipient_name: string;
  recipient_email: string;
  custom_message?: string | null;
  status: 'active' | 'redeemed' | 'expired';
  payment_method?: string;
  qr_code_url?: string | null;
  expires_at?: string | null;
  created_at: string;
}

export interface GiftCardPurchasePayload {
  amount: number;
  recipient_name: string;
  recipient_email: string;
  custom_message?: string;
  payment_method?: string;
  tenant_id?: string;
}

export interface GiftCardVerify {
  code: string;
  amount: number;
  balance: number;
  status: string;
  recipient_name: string;
  expires_at?: string | null;
}
