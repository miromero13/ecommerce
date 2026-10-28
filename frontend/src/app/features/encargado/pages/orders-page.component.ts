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
  protected readonly pickupCodes = signal<Partial<Record<string, string>>>({});
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

  // Web orders are paid online beforehand; the counter only hands them over.
  protected canHandOver(order: Order): boolean {
    if (order.fulfillment_type === 'delivery') return false; // handed to a platform driver instead
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

  protected canMarkReady(order: Order): boolean {
    return order.fulfillment_status === 'pending_pickup' && order.payment_status === 'paid';
  }

  protected fulfillmentLabel(status: Order['fulfillment_status']): string {
    return ({
      pending_pickup: 'Pendiente de preparación',
      ready_for_pickup: 'Listo para recoger',
      collected: 'Entregado',
      in_transit: 'En camino con repartidor',
      delivered: 'Entregado a domicilio',
      expired: 'Vencido',
      cancelled: 'Cancelado',
    } satisfies Record<Order['fulfillment_status'], string>)[status];
  }
  protected paymentMethodLabel(method: Order['payment_method']): string { return method === 'stripe' ? 'Tarjeta' : 'QR'; }
}
