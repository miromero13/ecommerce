import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { downloadSimplePdf } from '../../../core/utils/simple-pdf.util';
import { BrandingService } from '../../../core/services/branding.service';
import { CheckoutApiService } from '../../shared/services/checkout-api.service';
import { DeliveryApiService } from '../../shared/services/delivery-api.service';
import { Order, FulfillmentStatusEnum } from '../../shared/models/order.model';

@Component({
  selector: 'app-orders-page',
  standalone: true,
  imports: [CommonModule, HlmButton, ...HlmCardImports],
  templateUrl: './orders-page.component.html',
})
export class OrdersPageComponent {
  private readonly branding = inject(BrandingService);
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

  protected async downloadSalesNote(order: Order): Promise<void> {
    downloadSimplePdf({
      brand: await this.branding.pdfBrand(order.tenant_id),
      filename: `nota-venta-${order.id}.pdf`,
      title: 'Nota de venta',
      generatedAt: new Date().toLocaleString('es-BO'),
      filters: [
        ['Pedido', order.id],
        ['Fecha', new Date(order.created_at).toLocaleString('es-BO')],
        ['Pago', ({ pending: 'Pendiente', paid: 'Pagado', failed: 'Fallido' } satisfies Record<Order['payment_status'], string>)[order.payment_status]],
        ['Método', order.payment_method === 'stripe' ? 'Tarjeta' : 'QR'],
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
