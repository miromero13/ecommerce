import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { DeliveryAddress } from '../models/delivery.model';
import { Order } from '../models/order.model';

@Injectable({ providedIn: 'root' })
export class CheckoutApiService {
  private readonly api = inject(ApiService);

  checkoutStripe(payload: { pickup_branch_id: string; delivery?: DeliveryAddress; points_to_redeem?: number }) {
    return this.api.post<ApiResponse<{ order_id: string; client_secret: string; payment_intent_id: string; pickup_expires_at: string }>>('/payments/stripe/checkout', payload);
  }

  getOrder(orderId: string) {
    return this.api.get<ApiResponse<Order>>(`/orders/${orderId}`);
  }

  listOrders() {
    return this.api.get<ApiResponse<Order[]>>('/orders/me');
  }

  /** Staff see their own branch; the administrator names one branch of the company. */
  listBranchOrders(branchId?: string) {
    const query = branchId ? `?branch_id=${encodeURIComponent(branchId)}` : '';
    return this.api.get<ApiResponse<Order[]>>(`/orders/branch${query}`);
  }

  markReady(orderId: string) {
    return this.api.post<ApiResponse<Order>>(`/orders/${orderId}/ready`, {});
  }

  /** Hands over a web order already paid online; nothing is charged at the counter. */
  handOver(orderId: string, pickupCode: string) {
    return this.api.post<ApiResponse<Order>>(`/orders/${orderId}/hand-over`, { pickup_code: pickupCode });
  }
}
