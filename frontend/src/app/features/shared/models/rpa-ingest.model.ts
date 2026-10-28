/** CU10: a garment line read from a supplier document. */
export interface RpaItem {
  sku: string;
  name: string;
  size?: string | null;
  color?: string | null;
  quantity: number;
  unit_cost?: number | null;
  variant_id?: string | null;
  recognized?: boolean;
}

export interface RpaJob {
  job_id: string;
  filename: string;
  status: 'processing' | 'completed' | 'failed' | 'committed';
  extracted_items: RpaItem[];
  error_message: string | null;
  target_branch_id: string | null;
  committed_at: string | null;
  created_at: string;
}

export interface RpaCommitResult {
  job_id: string;
  committed_items: number;
  committed_units: number;
  unrecognized_items: RpaItem[];
}
