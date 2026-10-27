import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { DeliveryAddress } from '../models/delivery.model';
import { Order } from '../models/order.model';
import { QrPayment } from '../models/qr-payment.model';

@Injectable({ providedIn: 'root' })
export class QrPaymentApiService {
  private readonly api = inject(ApiService);

  checkout(payload: { pickup_branch_id: string; delivery?: DeliveryAddress }) {
    return this.api.post<ApiResponse<{ order: Order; qr: QrPayment }>>('/payments/qr/checkout', payload);
  }

  saleIntent(payload: { items: { variant_id: string; quantity: number }[] }) {
    return this.api.post<ApiResponse<QrPayment>>('/payments/qr/sale-intent', payload);
  }

  reservationDeposit(reservationId: string) {
    return this.api.post<ApiResponse<QrPayment>>(`/payments/qr/reservations/${reservationId}`, {});
  }

  status(reference: string) {
    return this.api.get<ApiResponse<QrPayment>>(`/payments/qr/${reference}`);
  }

  simulate(reference: string) {
    return this.api.post<ApiResponse<QrPayment>>(`/payments/qr/${reference}/simulate-payment`, {});
  }
}
