import { Injectable, inject } from '@angular/core';
import { HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { ApiService } from '../../../core/services/api.service';
import { ApiResponse } from '../../../core/models/api.model';
import {
  Tenant,
  TenantCreatePayload,
  TenantStatus,
  TenantUpdatePayload,
} from '../models/tenant.model';

@Injectable({ providedIn: 'root' })
export class TenantApiService {
  private readonly api = inject(ApiService);

  listTenants(params?: {
    skip?: number;
    limit?: number;
    search?: string;
    status?: string;
  }): Observable<ApiResponse<Tenant[]>> {
    let httpParams = new HttpParams();
    if (params?.skip !== undefined) {
      httpParams = httpParams.set('skip', params.skip.toString());
    }
    if (params?.limit !== undefined) {
      httpParams = httpParams.set('limit', params.limit.toString());
    }
    if (params?.search) {
      httpParams = httpParams.set('search', params.search);
    }
    if (params?.status) {
      httpParams = httpParams.set('status', params.status);
    }

    return this.api.get<ApiResponse<Tenant[]>>('/saas/tenants/', {
      params: httpParams,
    });
  }

  listPublicTenants(): Observable<ApiResponse<Array<{ id: string; name: string; slug: string; currency: string; country: string }>>> {
    return this.api.get<ApiResponse<Array<{ id: string; name: string; slug: string; currency: string; country: string }>>>('/saas/tenants/public');
  }

  getTenant(tenantId: string): Observable<ApiResponse<Tenant>> {
    return this.api.get<ApiResponse<Tenant>>(`/saas/tenants/${tenantId}`);
  }

  createTenant(payload: TenantCreatePayload): Observable<ApiResponse<Tenant>> {
    return this.api.post<ApiResponse<Tenant>>('/saas/tenants/', payload);
  }

  updateTenant(
    tenantId: string,
    payload: TenantUpdatePayload,
  ): Observable<ApiResponse<Tenant>> {
    return this.api.patch<ApiResponse<Tenant>>(`/saas/tenants/${tenantId}`, payload);
  }

  updateTenantStatus(
    tenantId: string,
    status: TenantStatus,
  ): Observable<ApiResponse<Tenant>> {
    return this.api.patch<ApiResponse<Tenant>>(`/saas/tenants/${tenantId}/status`, {
      status,
    });
  }
}
