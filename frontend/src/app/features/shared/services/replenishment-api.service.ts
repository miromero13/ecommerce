import { Injectable, inject } from '@angular/core';
import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { ReplenishmentRequest, ReplenishmentStatus } from '../models/replenishment.model';

@Injectable({ providedIn: 'root' })
export class ReplenishmentApiService {
  private readonly api = inject(ApiService);

  list() { return this.api.get<ApiResponse<ReplenishmentRequest[]>>('/replenishment/requests'); }
  create(payload: { provider_id: string; branch_id: string; items: Array<{ variant_id: string; requested_quantity: number }> }) { return this.api.post<ApiResponse<ReplenishmentRequest>>('/replenishment/requests', payload); }
  updateStatus(id: string, status: ReplenishmentStatus) { return this.api.patch<ApiResponse<ReplenishmentRequest>>(`/replenishment/requests/${id}/status`, { status }); }
}
