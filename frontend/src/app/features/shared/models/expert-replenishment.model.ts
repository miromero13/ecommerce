export type SuggestionStatus = 'pending' | 'applied' | 'discarded';

export interface ExpertRule {
  id: string;
  tenant_id: string;
  lookback_days: number;
  coverage_days: number;
  is_auto_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface ExpertRuleUpdate {
  lookback_days?: number;
  coverage_days?: number;
  is_auto_enabled?: boolean;
}

export interface ExpertSuggestion {
  id: string;
  tenant_id: string;
  variant_id: string;
  source_branch_id: string;
  target_branch_id: string;
  suggested_quantity: number;
  reason: string;
  status: SuggestionStatus;
  created_at: string;
  applied_at?: string | null;
  product_name?: string | null;
  variant_sku?: string | null;
  source_branch_name?: string | null;
  target_branch_name?: string | null;
}

export interface ApplyTransfersRequest {
  transfer_ids: string[];
}
