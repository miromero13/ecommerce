import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  lucideArrowRight,
  lucideCheckCircle2,
  lucideClock,
  lucideKeyRound,
  lucideMapPin,
  lucidePackageCheck,
  lucideRefreshCw,
  lucideTruck,
  lucideUser,
} from '@ng-icons/lucide';
import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { DeliveryOrder } from '../../shared/models/delivery.model';
import { DeliveryApiService } from '../../shared/services/delivery-api.service';

@Component({
  selector: 'app-my-deliveries-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    NgIcon,
    HlmButton,
    ...HlmCardImports,
    ...HlmBadgeImports,
  ],
  providers: [
    provideIcons({
      lucideTruck,
      lucideKeyRound,
      lucideMapPin,
      lucideUser,
      lucideArrowRight,
      lucideClock,
      lucideCheckCircle2,
      lucidePackageCheck,
      lucideRefreshCw,
    }),
  ],
  template: `
    <div class="space-y-6 max-w-5xl mx-auto px-4 py-6">
      <!-- Encabezado -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <h1 class="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <ng-icon name="lucideTruck" class="text-primary w-6 h-6"></ng-icon>
            Mis Envíos a Domicilio
          </h1>
          <p class="text-sm text-muted-foreground mt-1">
            Seguimiento en vivo de tus compras despachadas por repartidores y tus códigos PIN de entrega.
          </p>
        </div>

        <button
          hlmBtn
          variant="outline"
          class="gap-2 shrink-0"
          [disabled]="loading()"
          (click)="load()"
        >
          <ng-icon name="lucideRefreshCw" class="w-4 h-4" [class.animate-spin]="loading()"></ng-icon>
          Actualizar
        </button>
      </div>

      <!-- Estado de carga -->
      <div *ngIf="loading()" class="py-12 text-center text-muted-foreground">
        <ng-icon name="lucideTruck" class="w-8 h-8 animate-bounce mx-auto text-primary mb-2"></ng-icon>
        <p class="text-sm">Consultando estado de tus envíos...</p>
      </div>

      <!-- Listado vacío -->
      <div
        *ngIf="!loading() && deliveries().length === 0"
        hlmCard
        class="text-center py-12 px-4 bg-muted/20 border-dashed"
      >
        <div class="w-14 h-14 rounded-full bg-primary/10 text-primary mx-auto flex items-center justify-center mb-3">
          <ng-icon name="lucideTruck" class="w-7 h-7"></ng-icon>
        </div>
        <h3 class="text-lg font-semibold text-foreground">No tenés envíos registrados</h3>
        <p class="text-sm text-muted-foreground mt-1 max-w-sm mx-auto">
          Cuando realices una compra con envío a domicilio, acá vas a poder ver el chofer asignado y tu PIN de seguridad.
        </p>
        <a routerLink="/app/cliente/catalog" hlmBtn class="mt-5 gap-2">
          Explorar catálogo
          <ng-icon name="lucideArrowRight" class="w-4 h-4"></ng-icon>
        </a>
      </div>

      <!-- Listado de Envíos -->
      <div *ngIf="!loading() && deliveries().length > 0" class="space-y-4">
        <div
          *ngFor="let item of deliveries()"
          hlmCard
          class="border shadow-xs hover:border-primary/40 transition-all overflow-hidden"
          [class.border-l-4]="item.status === 'in_transit'"
          [class.border-l-primary]="item.status === 'in_transit'"
        >
          <div hlmCardContent class="p-5 space-y-4">
            <!-- Header de tarjeta -->
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/50 pb-3">
              <div>
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-mono font-bold text-sm text-foreground">#{{ item.order_id.slice(0, 8) }}</span>
                  <span [ngClass]="statusBadgeClass(item.status)" class="text-xs font-semibold px-2.5 py-0.5 rounded-full border">
                    {{ statusLabel(item.status) }}
                  </span>
                  <span class="text-xs text-muted-foreground">· {{ item.created_at | date:'dd/MM/yyyy HH:mm' }}</span>
                </div>
                <p class="text-xs text-muted-foreground mt-0.5">
                  Origen: <strong>{{ item.tenant_name }}</strong>
                  <span *ngIf="item.branch_name">({{ item.branch_name }} - {{ item.branch_city }})</span>
                </p>
              </div>

              <div class="text-right">
                <span class="text-xs text-muted-foreground block">Total con flete</span>
                <span class="text-lg font-bold text-foreground">
                  {{ item.total_amount | currency:(item.currency || 'BOB'):'symbol':'1.2-2' }}
                </span>
              </div>
            </div>

            <!-- Caja de PIN de seguridad (CU20) -->
            <div class="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-amber-500/20 text-amber-700 dark:text-amber-300 flex items-center justify-center shrink-0">
                  <ng-icon name="lucideKeyRound" class="w-5 h-5"></ng-icon>
                </div>
                <div>
                  <p class="text-[11px] font-bold uppercase tracking-wider text-amber-800 dark:text-amber-300">
                    Código PIN de Seguridad
                  </p>
                  <p class="text-2xl font-black font-mono tracking-widest text-foreground">
                    {{ item.delivery_pin || '----' }}
                  </p>
                </div>
              </div>
              <p class="text-xs text-muted-foreground max-w-sm">
                {{ item.status === 'delivered' 
                  ? 'Entrega certificada exitosamente con este PIN.' 
                  : 'Mostrale o dictale este código de 4 dígitos al chofer para recibir el paquete.' }}
              </p>
            </div>

            <!-- Detalles del despacho -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs bg-muted/20 rounded-lg p-3">
              <div class="space-y-1">
                <p class="text-muted-foreground flex items-center gap-1.5">
                  <ng-icon name="lucideMapPin" class="w-4 h-4 text-primary shrink-0"></ng-icon>
                  <strong>Dirección de entrega:</strong>
                </p>
                <p class="text-foreground pl-5.5 font-medium">{{ item.address }}</p>
                <p *ngIf="item.reference" class="text-muted-foreground pl-5.5 italic">
                  Ref: {{ item.reference }}
                </p>
              </div>

              <div class="space-y-1">
                <p class="text-muted-foreground flex items-center gap-1.5">
                  <ng-icon name="lucideUser" class="w-4 h-4 text-primary shrink-0"></ng-icon>
                  <strong>Repartidor:</strong>
                </p>
                <p class="text-foreground pl-5.5 font-medium">
                  {{ item.driver_name || 'Pendiente de asignación' }}
                </p>
                <p *ngIf="item.distance_km != null" class="text-muted-foreground pl-5.5">
                  Distancia: {{ item.distance_km }} km · Flete: {{ item.shipping_cost | currency:(item.currency || 'BOB'):'symbol':'1.2-2' }}
                </p>
              </div>
            </div>

            <div *ngIf="item.delivered_at" class="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5 pt-1">
              <ng-icon name="lucideCheckCircle2" class="w-4 h-4"></ng-icon>
              <span>Entregado el {{ item.delivered_at | date:'dd/MM/yyyy HH:mm' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class MyDeliveriesPageComponent {
  private readonly deliveryApi = inject(DeliveryApiService);
  protected readonly deliveries = signal<DeliveryOrder[]>([]);
  protected readonly loading = signal(false);

  constructor() {
    void this.load();
  }

  // [CU20 - Secuencia: Paso 2] El Cliente ejecuta load() en MyDeliveriesPageComponent
  protected async load(): Promise<void> {
    this.loading.set(true);
    try {
      const res = await firstValueFrom(this.deliveryApi.myOrders());
      this.deliveries.set(res.data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar los envíos.'));
    } finally {
      this.loading.set(false);
    }
  }

  protected statusLabel(status: string): string {
    const map: Record<string, string> = {
      pending_pickup: 'En preparación',
      ready_for_pickup: 'Listo para despacho',
      in_transit: 'En camino (en tránsito)',
      delivered: 'Entregado',
      cancelled: 'Cancelado',
    };
    return map[status] || status;
  }

  protected statusBadgeClass(status: string): string {
    switch (status) {
      case 'in_transit':
        return 'bg-blue-500/10 text-blue-600 border-blue-500/30 dark:text-blue-400';
      case 'delivered':
        return 'bg-emerald-500/10 text-emerald-600 border-emerald-500/30 dark:text-emerald-400';
      case 'pending_pickup':
      case 'ready_for_pickup':
        return 'bg-amber-500/10 text-amber-600 border-amber-500/30 dark:text-amber-400';
      default:
        return 'bg-slate-500/10 text-slate-600 border-slate-500/30';
    }
  }
}
