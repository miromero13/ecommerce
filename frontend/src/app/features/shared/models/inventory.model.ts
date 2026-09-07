export interface InventoryBranch {
  id: string;
  name: string;
  city: string;
  is_default: boolean;
}

export interface InventoryBranchStock {
  variant_id: string;
  branch_id: string;
  branch_name: string;
  product_id: string;
  product_name: string;
  variant_sku: string;
  variant_price: string;
  image_url: string | null;
  image_public_id: string | null;
  status: string;
  size_id: string | null;
  color_id: string | null;
  size_name: string | null;
  color_name: string | null;
  quantity: number;
  reserved_quantity: number;
  available_quantity: number;
}

export interface InventoryConsolidatedBranch {
  branch_id: string;
  branch_name: string;
  quantity: number;
  reserved_quantity: number;
  available_quantity: number;
}

export interface InventoryConsolidatedStock {
  variant_id: string;
  product_id: string;
  product_name: string;
  variant_sku: string;
  variant_price: string;
  image_url: string | null;
  image_public_id: string | null;
  status: string;
  size_id: string | null;
  color_id: string | null;
  size_name: string | null;
  color_name: string | null;
  quantity: number;
  reserved_quantity: number;
  available_quantity: number;
  branches: InventoryConsolidatedBranch[];
}

export interface InventoryMovement {
  id: string;
  variant_id: string;
  branch_id: string;
  movement_type: 'income' | 'outcome' | 'transfer_in' | 'transfer_out';
  quantity: number;
  reference_branch_id: string | null;
  note: string | null;
  created_by: string | null;
  created_at: string;
}
