import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { CheckoutApiService } from '../../shared/services/checkout-api.service';
import { Order, FulfillmentStatusEnum } from '../../shared/models/order.model';

@Component({
  selector: 'app-orders-page',
  standalone: true,
  imports: [CommonModule, HlmButton, ...HlmCardImports],
  templateUrl: './orders-page.component.html',
})
export class OrdersPageComponent {
  private readonly api = inject(CheckoutApiService);
  protected readonly orders = signal<Order[]>([]);
  protected readonly loading = signal(false);
  protected readonly error = signal<string | null>(null);

  constructor() { void this.load(); }

  protected statusLabel(status: FulfillmentStatusEnum): string {
    return { pending_pickup: 'En preparación', ready_for_pickup: 'Listo', collected: 'Cobrado', expired: 'Expirado', cancelled: 'Cancelado' }[status];
  }

  protected async load(): Promise<void> {
    this.loading.set(true);
    try {
      const response = await firstValueFrom(this.api.listOrders());
      this.orders.set(response.data ?? []);
      this.error.set(null);
    } catch (error) {
      this.error.set(getErrorMessage(error, 'No se pudieron cargar los pedidos.'));
    } finally {
      this.loading.set(false);
    }
  }
}
