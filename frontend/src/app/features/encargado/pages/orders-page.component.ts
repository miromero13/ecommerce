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
  protected readonly cashReceived = signal<Partial<Record<string, string>>>({});
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

  protected setCashReceived(orderId: string, event: Event): void {
    this.cashReceived.update((values) => ({ ...values, [orderId]: (event.target as HTMLInputElement).value }));
  }

  /** Change to return for a cash order, once the cashier typed what the customer handed over. */
  protected changeFor(order: Order): { value: number } | null {
    const received = this.cashReceived()[order.id];
    return received ? { value: Number(received) - Number(order.total_amount) } : null;
  }

  // Cash orders are charged at the counter; card orders were paid online and are only handed over.
  protected canHandOver(order: Order): boolean {
    if (order.fulfillment_type === 'delivery') return false; // handed to a platform driver instead
    if (order.payment_method === 'cash') return order.payment_status === 'pending' && order.fulfillment_status === 'pending_pickup';
    return order.payment_status === 'paid' && ['pending_pickup', 'ready_for_pickup'].includes(order.fulfillment_status);
  }

  protected async handOver(order: Order): Promise<void> {
    try {
      const received = order.payment_method === 'cash' && this.cashReceived()[order.id] ? Number(this.cashReceived()[order.id]) : null;
      toast.success((await firstValueFrom(this.api.handOver(order.id, this.pickupCodes()[order.id] ?? '', received))).message);
      await this.load();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo entregar el pedido.'));
    }
  }

  // Delivery orders paid in cash are collected by the driver, so they can be dispatched unpaid.
  protected canMarkReady(order: Order): boolean {
    if (order.fulfillment_status !== 'pending_pickup') return false;
    return order.payment_status === 'paid' || (order.fulfillment_type === 'delivery' && order.payment_method === 'cash');
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
  protected paymentMethodLabel(method: Order['payment_method']): string { return method === 'stripe' ? 'Tarjeta' : 'Efectivo'; }
}
