import { ApiResponse } from '../../../core/models/api.model';

export interface AdminBranch {
  id: string;
  name: string;
  city: string;
  is_default: boolean;
  is_active: boolean;
}

export interface CreateBranchRequest {
  name: string;
  city: string;
  is_default?: boolean;
}

export interface UpdateBranchRequest {
  name: string;
  city: string;
  is_default?: boolean;
  is_active: boolean;
}

export interface UpdateBranchActiveRequest {
  is_active: boolean;
}

export type BranchListResponse = ApiResponse<AdminBranch[]>;
