import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { HlmButton } from '../../../components/button/src';
import { CheckoutApiService } from '../../shared/services/checkout-api.service';
import { Order } from '../../shared/models/order.model';
import { requestWithToast } from '../../../core/utils/request-toast.util';

@Component({
  selector: 'app-encargado-orders-page',
  standalone: true,
  imports: [CommonModule, HlmButton],
  templateUrl: './orders-page.component.html',
})
export class EncargadoOrdersPageComponent {
  private readonly api = inject(CheckoutApiService);
  protected readonly orders = signal<Order[]>([]);
  constructor() { void this.load(); }
  private async load(): Promise<void> { const response = await firstValueFrom(this.api.listBranchOrders()); this.orders.set(response.data ?? []); }
  protected async markReady(orderId: string): Promise<void> { await requestWithToast(this.api.markReady(orderId), { loading: 'Actualizando pedido...', success: 'Pedido marcado como listo.', error: 'No se pudo marcar el pedido.' }); await this.load(); }
  protected fulfillmentLabel(status: Order['fulfillment_status']): string {
    return ({
      pending_pickup: 'Pendiente de preparación',
      ready_for_pickup: 'Listo para recoger',
      collected: 'Entregado',
      expired: 'Vencido',
      cancelled: 'Cancelado',
    } satisfies Record<Order['fulfillment_status'], string>)[status];
  }
  protected paymentMethodLabel(method: Order['payment_method']): string { return method === 'stripe' ? 'Tarjeta' : 'Efectivo'; }
}
