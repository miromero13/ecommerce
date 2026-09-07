import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { Order } from '../models/order.model';

@Injectable({ providedIn: 'root' })
export class CheckoutApiService {
  private readonly api = inject(ApiService);

  checkoutCash(payload: { cash_reference?: string | null }) {
    return this.api.post<ApiResponse<Order>>('/payments/cash/checkout', payload);
  }

  checkoutStripe(payload: { currency?: string | null }) {
    return this.api.post<ApiResponse<{ order_id: string; client_secret: string; payment_intent_id: string; order?: Order }>>('/payments/stripe/checkout', payload);
  }
}
