import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { QrPayment } from '../models/qr-payment.model';

/** QR only exists at the store's till (online payments are Stripe only). */
@Injectable({ providedIn: 'root' })
export class QrPaymentApiService {
  private readonly api = inject(ApiService);

  saleIntent(payload: { items: { variant_id: string; quantity: number }[]; promotion_code?: string | null; customer_email?: string | null }) {
    return this.api.post<ApiResponse<QrPayment>>('/payments/qr/sale-intent', payload);
  }

  status(reference: string) {
    return this.api.get<ApiResponse<QrPayment>>(`/payments/qr/${reference}`);
  }

  simulate(reference: string) {
    return this.api.post<ApiResponse<QrPayment>>(`/payments/qr/${reference}/simulate-payment`, {});
  }
}
