import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { AdminBranch, BranchListResponse, CreateBranchRequest } from '../models/admin-branch.model';

@Injectable({ providedIn: 'root' })
export class AdminBranchService {
  private readonly api = inject(ApiService);

  listBranches() {
    return this.api.get<BranchListResponse>('/branches/');
  }

  createBranch(payload: CreateBranchRequest) {
    return this.api.post<ApiResponse<AdminBranch>>('/branches/', payload);
  }
}
