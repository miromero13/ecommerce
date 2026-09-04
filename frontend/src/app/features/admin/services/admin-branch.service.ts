import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { AdminBranch, BranchListResponse, CreateBranchRequest, UpdateBranchActiveRequest, UpdateBranchRequest } from '../models/admin-branch.model';

@Injectable({ providedIn: 'root' })
export class AdminBranchService {
  private readonly api = inject(ApiService);

  listBranches() {
    return this.api.get<BranchListResponse>('/branches/');
  }

  createBranch(payload: CreateBranchRequest) {
    return this.api.post<ApiResponse<AdminBranch>>('/branches/', payload);
  }

  updateBranch(branchId: string, payload: UpdateBranchRequest) {
    return this.api.put<ApiResponse<AdminBranch>>(`/branches/${branchId}`, payload);
  }

  updateBranchActive(branchId: string, payload: UpdateBranchActiveRequest) {
    return this.api.patch<ApiResponse<AdminBranch>>(`/branches/${branchId}/active`, payload);
  }

  deleteBranch(branchId: string) {
    return this.api.delete<ApiResponse<{ id: string }>>(`/branches/${branchId}`);
  }
}
