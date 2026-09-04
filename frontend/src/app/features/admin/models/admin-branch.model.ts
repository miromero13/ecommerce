import { ApiResponse } from '../../../core/models/api.model';

export interface AdminBranch {
  id: string;
  name: string;
  city: string;
  is_default: boolean;
}

export interface CreateBranchRequest {
  name: string;
  city: string;
  is_default?: boolean;
}

export type BranchListResponse = ApiResponse<AdminBranch[]>;
