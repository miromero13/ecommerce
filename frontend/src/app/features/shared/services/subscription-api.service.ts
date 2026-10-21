import { Injectable, inject } from '@angular/core';
import { HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { ApiService } from '../../../core/services/api.service';
import { ApiResponse } from '../../../core/models/api.model';
import {
  SubscriptionPlan,
  SubscriptionPurchasePayload,
  SubscriptionSummary,
  TenantWithSubscriptionPayload,
} from '../models/subscription.model';

@Injectable({ providedIn: 'root' })
export class SubscriptionApiService {
  private readonly api = inject(ApiService);

  getPlans(): Observable<ApiResponse<SubscriptionPlan[]>> {
    return this.api.get<ApiResponse<SubscriptionPlan[]>>('/saas/plans');
  }

  purchaseSimulated(payload: SubscriptionPurchasePayload): Observable<ApiResponse<any>> {
    return this.api.post<ApiResponse<any>>('/saas/subscriptions/purchase-simulated', payload);
  }

  getCurrentSubscription(tenantId?: string): Observable<ApiResponse<SubscriptionSummary>> {
    let params = new HttpParams();
    if (tenantId) {
      params = params.set('tenant_id', tenantId);
    }
    return this.api.get<ApiResponse<SubscriptionSummary>>('/saas/subscriptions/current', params);
  }

  createTenantWithSubscription(payload: TenantWithSubscriptionPayload): Observable<ApiResponse<any>> {
    return this.api.post<ApiResponse<any>>('/saas/tenants/with-subscription', payload);
  }
}
