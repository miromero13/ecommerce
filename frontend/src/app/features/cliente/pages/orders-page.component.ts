import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { ReceiptActionsComponent } from '../../shared/components/receipt-actions.component';
import { CheckoutApiService } from '../../shared/services/checkout-api.service';
import { DeliveryApiService } from '../../shared/services/delivery-api.service';
import { Order, FulfillmentStatusEnum } from '../../shared/models/order.model';

@Component({
  selector: 'app-orders-page',
  standalone: true,
  imports: [CommonModule, HlmButton, ReceiptActionsComponent, ...HlmCardImports],
  templateUrl: './orders-page.component.html',
})
export class OrdersPageComponent {
  private readonly api = inject(CheckoutApiService);
  private readonly deliveryApi = inject(DeliveryApiService);
  protected readonly orders = signal<Order[]>([]);
  // CU20: the customer shows this PIN to the driver to receive a delivery order.
  protected readonly deliveryPins = signal<Record<string, string>>({});
  protected readonly loading = signal(false);
  protected readonly error = signal<string | null>(null);

  constructor() { void this.load(); }

  protected statusLabel(status: FulfillmentStatusEnum): string {
    return { pending_pickup: 'En preparación', ready_for_pickup: 'Listo', collected: 'Cobrado', in_transit: 'En camino', delivered: 'Entregado', expired: 'Expirado', cancelled: 'Cancelado' }[status];
  }

  protected async load(): Promise<void> {
    this.loading.set(true);
    try {
      const [response, deliveries] = await Promise.all([
        firstValueFrom(this.api.listOrders()),
        firstValueFrom(this.deliveryApi.myOrders()),
      ]);
      this.orders.set(response.data ?? []);
      this.deliveryPins.set(Object.fromEntries((deliveries.data ?? []).map((d) => [d.order_id, d.delivery_pin ?? ''])));
      this.error.set(null);
    } catch (error) {
      this.error.set(getErrorMessage(error, 'No se pudieron cargar los pedidos.'));
    } finally {
      this.loading.set(false);
    }
  }
}
