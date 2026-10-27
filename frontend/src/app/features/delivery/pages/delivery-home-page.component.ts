import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { toast } from '@spartan-ng/brain/sonner';
import { firstValueFrom } from 'rxjs';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmInput } from '../../../components/input/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { DeliveryOrder } from '../../shared/models/delivery.model';
import { DeliveryApiService } from '../../shared/services/delivery-api.service';

// CU20: platform drivers take ready orders from any company and deliver them with the customer's PIN.
@Component({
  selector: 'app-delivery-home-page',
  standalone: true,
  imports: [CommonModule, HlmButton, HlmInput, ...HlmBadgeImports, ...HlmCardImports],
  templateUrl: './delivery-home-page.component.html',
})
export class DeliveryHomePageComponent {
  private readonly api = inject(DeliveryApiService);
  protected readonly available = signal<DeliveryOrder[]>([]);
  protected readonly route = signal<DeliveryOrder[]>([]);
  protected readonly pins = signal<Partial<Record<string, string>>>({});
  protected readonly busyId = signal<string | null>(null);

  constructor() {
    void this.load();
  }

  protected async load(): Promise<void> {
    try {
      const [available, route] = await Promise.all([
        firstValueFrom(this.api.available()),
        firstValueFrom(this.api.route()),
      ]);
      this.available.set(available.data ?? []);
      this.route.set(route.data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo cargar la hoja de ruta.'));
    }
  }

  protected setPin(orderId: string, event: Event): void {
    this.pins.update((pins) => ({ ...pins, [orderId]: (event.target as HTMLInputElement).value.trim() }));
  }

  protected async claim(order: DeliveryOrder): Promise<void> {
    await this.run(order.order_id, () => firstValueFrom(this.api.claim(order.order_id)), 'No se pudo tomar el pedido.');
  }

  protected async confirm(order: DeliveryOrder): Promise<void> {
    const pin = this.pins()[order.order_id] ?? '';
    await this.run(order.order_id, () => firstValueFrom(this.api.confirm(order.order_id, pin)), 'No se pudo confirmar la entrega.');
  }

  protected statusLabel(status: DeliveryOrder['status']): string {
    return ({ in_transit: 'En camino', delivered: 'Entregado' } as Record<string, string>)[status] ?? status;
  }

  private async run(orderId: string, action: () => Promise<{ message: string }>, fallback: string): Promise<void> {
    this.busyId.set(orderId);
    try {
      toast.success((await action()).message);
      await this.load();
    } catch (error) {
      toast.error(getErrorMessage(error, fallback));
    } finally {
      this.busyId.set(null);
    }
  }
}
