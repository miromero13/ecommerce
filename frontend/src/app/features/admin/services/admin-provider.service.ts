import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { AdminProvider, CreateProviderRequest, ProviderListResponse, UpdateProviderStatusRequest } from '../models/admin-provider.model';

@Injectable({ providedIn: 'root' })
export class AdminProviderService {
  private readonly api = inject(ApiService);

  listProviders() {
    return this.api.get<ProviderListResponse>('/providers/');
  }

  createProvider(payload: CreateProviderRequest) {
    return this.api.post<ApiResponse<AdminProvider>>('/providers/', payload);
  }

  updateProviderStatus(providerId: string, status: UpdateProviderStatusRequest['status']) {
    return this.api.patch<ApiResponse<AdminProvider>>(`/providers/${providerId}/status`, { status });
  }
}
