import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { toast } from '@spartan-ng/brain/sonner';
import { firstValueFrom } from 'rxjs';

import { HlmButton } from '../../../components/button/src';
import { HlmInput } from '../../../components/input/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { Order } from '../../shared/models/order.model';
import { CheckoutApiService } from '../../shared/services/checkout-api.service';
import { SessionService } from '../../shared/services/session.service';

@Component({
  selector: 'app-encargado-orders-page',
  standalone: true,
  imports: [CommonModule, HlmButton, HlmInput],
  templateUrl: './orders-page.component.html',
})
export class EncargadoOrdersPageComponent {
  private readonly api = inject(CheckoutApiService);
  private readonly session = inject(SessionService);
  protected readonly orders = signal<Order[]>([]);
  protected readonly pickupCodes = signal<Record<string, string>>({});
  protected readonly isManager = () => this.session.user()?.rol === 'encargado';
  constructor() { void this.load(); }
  private async load(): Promise<void> { const response = await firstValueFrom(this.api.listBranchOrders()); this.orders.set(response.data ?? []); }

  protected async markReady(orderId: string): Promise<void> {
    try {
      toast.success((await firstValueFrom(this.api.markReady(orderId))).message);
      await this.load();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo marcar el pedido.'));
    }
  }

  protected setPickupCode(orderId: string, event: Event): void {
    this.pickupCodes.update((codes) => ({ ...codes, [orderId]: (event.target as HTMLInputElement).value.trim() }));
  }

  // Cash orders are charged at the counter; card orders were paid online and are only handed over.
  protected canHandOver(order: Order): boolean {
    if (order.payment_method === 'cash') return order.payment_status === 'pending' && order.fulfillment_status === 'pending_pickup';
    return order.payment_status === 'paid' && ['pending_pickup', 'ready_for_pickup'].includes(order.fulfillment_status);
  }

  protected async handOver(order: Order): Promise<void> {
    try {
      toast.success((await firstValueFrom(this.api.handOver(order.id, this.pickupCodes()[order.id] ?? ''))).message);
      await this.load();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo entregar el pedido.'));
    }
  }

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
