import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { DeliveryOrder, DeliveryQuote, DriverCreate } from '../models/delivery.model';
import { UsuarioAuth } from '../models/auth.model';

@Injectable({ providedIn: 'root' })
export class DeliveryApiService {
  private readonly api = inject(ApiService);

  quote(payload: { branch_id: string; latitude: number; longitude: number }) {
    return this.api.post<ApiResponse<DeliveryQuote>>('/delivery/quotes', payload);
  }

  myOrders() {
    return this.api.get<ApiResponse<DeliveryOrder[]>>('/delivery/my-orders');
  }

  available() {
    return this.api.get<ApiResponse<DeliveryOrder[]>>('/delivery/available');
  }

  claim(orderId: string) {
    return this.api.post<ApiResponse<DeliveryOrder>>(`/delivery/orders/${orderId}/claim`, {});
  }

  route() {
    return this.api.get<ApiResponse<DeliveryOrder[]>>('/delivery/routes');
  }

  confirm(orderId: string, securityPin: string) {
    return this.api.post<ApiResponse<{ order_id: string; delivered_at: string }>>('/delivery/confirm-delivery', {
      order_id: orderId,
      security_pin: securityPin,
    });
  }

  drivers() {
    return this.api.get<ApiResponse<UsuarioAuth[]>>('/delivery/drivers');
  }

  createDriver(payload: DriverCreate) {
    return this.api.post<ApiResponse<UsuarioAuth>>('/delivery/drivers', payload);
  }
}
