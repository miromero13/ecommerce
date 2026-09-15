export type PromotionDiscountType = 'percentage' | 'fixed';

export interface PromotionCode {
  id: string;
  code: string;
  discount_type: PromotionDiscountType;
  discount_value: string;
  valid_from: string | null;
  valid_until: string | null;
  branch_id: string | null;
  created_by: string;
  is_active: boolean;
  created_at: string;
}

export interface CreatePromotionCodeRequest {
  code: string;
  discount_type: PromotionDiscountType;
  discount_value: string;
  valid_from?: string | null;
  valid_until?: string | null;
  branch_id?: string | null;
  is_active?: boolean;
}
