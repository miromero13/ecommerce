import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { Order } from '../models/order.model';

@Injectable({ providedIn: 'root' })
export class CheckoutApiService {
  private readonly api = inject(ApiService);

  checkoutCash(payload: { pickup_branch_id: string }) {
    return this.api.post<ApiResponse<Order>>('/payments/cash/checkout', payload);
  }

  checkoutStripe(payload: { pickup_branch_id: string }) {
    return this.api.post<ApiResponse<{ order_id: string; client_secret: string; payment_intent_id: string; pickup_expires_at: string }>>('/payments/stripe/checkout', payload);
  }

  getOrder(orderId: string) {
    return this.api.get<ApiResponse<Order>>(`/orders/${orderId}`);
  }

  listOrders() {
    return this.api.get<ApiResponse<Order[]>>('/orders/me');
  }

  listBranchOrders() {
    return this.api.get<ApiResponse<Order[]>>('/orders/branch');
  }

  markReady(orderId: string) {
    return this.api.post<ApiResponse<Order>>(`/orders/${orderId}/ready`, {});
  }
}
