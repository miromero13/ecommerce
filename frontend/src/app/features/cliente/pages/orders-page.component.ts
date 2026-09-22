import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { downloadSimplePdf } from '../../../core/utils/simple-pdf.util';
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

  protected downloadSalesNote(order: Order): void {
    downloadSimplePdf({
      filename: `nota-venta-${order.id}.pdf`,
      title: 'Nota de venta',
      generatedAt: new Date().toLocaleString('es-BO'),
      filters: [
        ['Pedido', order.id],
        ['Fecha', new Date(order.created_at).toLocaleString('es-BO')],
        ['Pago', ({ pending: 'Pendiente', paid: 'Pagado', failed: 'Fallido' } satisfies Record<Order['payment_status'], string>)[order.payment_status]],
        ['Método', order.payment_method === 'stripe' ? 'Tarjeta' : 'Efectivo'],
        ...(order.pickup_code ? [['Código de retiro', order.pickup_code]] : []),
        ['Subtotal', `${order.subtotal} ${order.currency}`],
        ['Descuento', `${order.discount_amount} ${order.currency}`],
        ['Total', `${order.total_amount} ${order.currency}`],
      ],
      columns: ['Producto', 'Variante', 'Cantidad', 'Precio unitario', 'Total'],
      rows: order.items.map((item) => [
        item.product_name,
        [item.size_name, item.color_name].filter(Boolean).join(' / ') || item.variant_sku,
        String(item.quantity),
        `${item.unit_price} ${order.currency}`,
        `${item.line_total} ${order.currency}`,
      ]),
    });
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
