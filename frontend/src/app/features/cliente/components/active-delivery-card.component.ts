import { CommonModule } from '@angular/common';
import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  lucideArrowRight,
  lucideKeyRound,
  lucideMapPin,
  lucidePackageCheck,
  lucideTruck,
  lucideUser,
} from '@ng-icons/lucide';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { DeliveryOrder } from '../../shared/models/delivery.model';

@Component({
  selector: 'app-active-delivery-card',
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
      lucidePackageCheck,
    }),
  ],
  template: `
    <section *ngIf="activeDeliveries().length > 0" class="space-y-3">
      <div
        *ngFor="let order of activeDeliveries()"
        hlmCard
        class="border-l-4 border-l-primary bg-primary/5 dark:bg-primary/10 shadow-sm overflow-hidden"
      >
        <div hlmCardContent class="p-4 sm:p-5 space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-primary text-primary-foreground flex items-center justify-center shrink-0">
                <ng-icon name="lucideTruck" class="w-5 h-5"></ng-icon>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <h3 class="font-bold text-base text-foreground">
                    {{ order.status === 'in_transit' ? '¡Tu pedido va en camino!' : 'Tu pedido está siendo preparado para despacho' }}
                  </h3>
                  <span hlmBadge class="bg-primary/20 text-primary border border-primary/30 text-xs">
                    {{ order.status === 'in_transit' ? 'En tránsito' : 'En preparación' }}
                  </span>
                </div>
                <p class="text-xs text-muted-foreground mt-0.5">
                  Orden #{{ order.order_id.slice(0, 8) }} · {{ order.tenant_name }}
                  <span *ngIf="order.branch_name">({{ order.branch_name }})</span>
                </p>
              </div>
            </div>

            <!-- PIN destacado -->
            <div *ngIf="order.delivery_pin" class="flex items-center gap-2.5 bg-background border border-border px-3.5 py-2 rounded-xl shadow-xs shrink-0">
              <ng-icon name="lucideKeyRound" class="w-5 h-5 text-amber-600 dark:text-amber-400"></ng-icon>
              <div>
                <p class="text-[10px] font-bold uppercase tracking-wider text-muted-foreground leading-none">PIN de Entrega</p>
                <p class="text-lg font-black font-mono tracking-widest text-foreground leading-tight">{{ order.delivery_pin }}</p>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-muted-foreground bg-background/80 rounded-lg p-3 border border-border/50">
            <div class="flex items-center gap-2">
              <ng-icon name="lucideMapPin" class="w-4 h-4 text-primary shrink-0"></ng-icon>
              <span class="truncate"><strong>Destino:</strong> {{ order.address }}</span>
            </div>
            <div class="flex items-center gap-2">
              <ng-icon name="lucideUser" class="w-4 h-4 text-primary shrink-0"></ng-icon>
              <span class="truncate">
                <strong>Repartidor:</strong> {{ order.driver_name || 'Asignando chofer...' }}
              </span>
            </div>
          </div>

          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-1 border-t border-border/40">
            <p class="text-xs text-muted-foreground">
              Mostrale este código de 4 dígitos al repartidor al momento de recibir tus prendas.
            </p>
            <a
              routerLink="/app/cliente/deliveries"
              hlmBtn
              variant="outline"
              size="sm"
              class="gap-1.5 shrink-0 text-xs font-semibold"
            >
              Ver mis envíos
              <ng-icon name="lucideArrowRight" class="w-3.5 h-3.5"></ng-icon>
            </a>
          </div>
        </div>
      </div>
    </section>
  `,
})
export class ActiveDeliveryCardComponent {
  deliveries = input<DeliveryOrder[]>([]);

  get activeDeliveries(): () => DeliveryOrder[] {
    return () => this.deliveries().filter((d) => d.status === 'in_transit' || d.status === 'ready_for_pickup' || d.status === 'pending_pickup');
  }
}
