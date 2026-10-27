import { Injectable, inject } from '@angular/core';
import { HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { ApiService } from '../../../core/services/api.service';
import { ApiResponse } from '../../../core/models/api.model';
import {
  SubscriptionChangePlanPayload,
  SubscriptionPlan,
  SubscriptionPlanPayload,
  SubscriptionPurchasePayload,
  StripeConnectStatus,
  SubscriptionSummary,
  TenantWithSubscriptionPayload,
} from '../models/subscription.model';

@Injectable({ providedIn: 'root' })
export class SubscriptionApiService {
  private readonly api = inject(ApiService);

  getStripeConnectStatus(): Observable<ApiResponse<StripeConnectStatus>> {
    return this.api.get<ApiResponse<StripeConnectStatus>>('/saas/stripe-connect/status');
  }

  createStripeOnboardingLink(returnUrl: string): Observable<ApiResponse<{ url: string }>> {
    return this.api.post<ApiResponse<{ url: string }>>('/saas/stripe-connect/onboarding-link', { return_url: returnUrl });
  }

  getPlans(): Observable<ApiResponse<SubscriptionPlan[]>> {
    return this.api.get<ApiResponse<SubscriptionPlan[]>>('/saas/plans');
  }

  /** Superadmin: every plan, including deactivated ones. */
  getAllPlans(): Observable<ApiResponse<SubscriptionPlan[]>> {
    return this.api.get<ApiResponse<SubscriptionPlan[]>>('/saas/plans/admin');
  }

  createPlan(payload: SubscriptionPlanPayload): Observable<ApiResponse<SubscriptionPlan>> {
    return this.api.post<ApiResponse<SubscriptionPlan>>('/saas/plans', payload);
  }

  updatePlan(planId: string, payload: Partial<SubscriptionPlanPayload>): Observable<ApiResponse<SubscriptionPlan>> {
    return this.api.patch<ApiResponse<SubscriptionPlan>>(`/saas/plans/${planId}`, payload);
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

  changePlan(payload: SubscriptionChangePlanPayload): Observable<ApiResponse<SubscriptionSummary>> {
    return this.api.post<ApiResponse<SubscriptionSummary>>('/saas/subscriptions/change-plan', payload);
  }

  createTenantWithSubscription(payload: TenantWithSubscriptionPayload): Observable<ApiResponse<any>> {
    return this.api.post<ApiResponse<any>>('/saas/tenants/with-subscription', payload);
  }
}
