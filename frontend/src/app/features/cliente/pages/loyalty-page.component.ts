import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { toast } from '@spartan-ng/brain/sonner';

import { getErrorMessage } from '../../../core/utils/http-error.util';
import { LoyaltyBalance, LoyaltyMovement } from '../../shared/models/loyalty.model';
import { LoyaltyApiService } from '../../shared/services/loyalty-api.service';

const MOVEMENT_LABELS: Record<LoyaltyMovement['type'], string> = { earn: 'Ganados', redeem: 'Canjeados', refund: 'Devueltos' };

/** CU17: points and tier per company, plus the movement history. */
@Component({
  selector: 'app-loyalty-page',
  standalone: true,
  imports: [CommonModule],
  template: `
    <section class="space-y-6 text-slate-700">
      <header>
        <h1 class="text-2xl font-semibold">Mis puntos</h1>
        <p class="text-sm text-slate-500">
          Ganas 1 punto por cada 10 Bs pagados y canjeas 10 puntos = 1 Bs al pagar. Los puntos son de cada empresa.
          Nivel por puntos acumulados: Bronce (menos de 500), Plata (500 a 1499) y Oro (1500 o más).
        </p>
      </header>
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        @for (row of balances(); track row.tenant_id) {
          <article class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div class="flex items-center justify-between">
              <p class="font-semibold text-slate-900">{{ row.tenant_name }}</p>
              <span class="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">{{ row.tier }}</span>
            </div>
            <p class="mt-2 text-3xl font-semibold">{{ row.points_balance }} <span class="text-sm font-normal">puntos</span></p>
            <p class="text-xs text-slate-500">Equivalen a {{ row.balance_value | number: '1.2-2' }} Bs · {{ row.lifetime_points }} acumulados</p>
          </article>
        } @empty {
          <p class="text-sm text-slate-500">Aún no tienes puntos. Ganarás puntos con tu primera compra pagada.</p>
        }
      </div>
      @if (movements().length) {
        <div class="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
          <table class="w-full text-sm">
            <thead class="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr><th class="p-3">Fecha</th><th class="p-3">Empresa</th><th class="p-3">Movimiento</th><th class="p-3">Origen</th><th class="p-3 text-right">Puntos</th></tr>
            </thead>
            <tbody>
              @for (row of movements(); track row.id) {
                <tr class="border-t border-slate-100">
                  <td class="p-3">{{ row.created_at | date: 'short' }}</td>
                  <td class="p-3">{{ row.tenant_name }}</td>
                  <td class="p-3">{{ label(row) }}</td>
                  <td class="p-3">{{ row.source_type === 'order' ? 'Pedido web' : 'Compra en tienda' }}</td>
                  <td class="p-3 text-right font-medium" [class.text-emerald-700]="row.type !== 'redeem'" [class.text-rose-700]="row.type === 'redeem'">
                    {{ row.type === 'redeem' ? '-' : '+' }}{{ row.points }}
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      }
    </section>
  `,
})
export class LoyaltyPageComponent {
  private readonly loyalty = inject(LoyaltyApiService);
  protected readonly balances = signal<LoyaltyBalance[]>([]);
  protected readonly movements = signal<LoyaltyMovement[]>([]);

  constructor() {
    void this.load();
  }

  protected label(row: LoyaltyMovement): string {
    return MOVEMENT_LABELS[row.type];
  }

  private async load(): Promise<void> {
    try {
      const [balances, movements] = await Promise.all([
        firstValueFrom(this.loyalty.balances()),
        firstValueFrom(this.loyalty.transactions()),
      ]);
      this.balances.set(balances.data ?? []);
      this.movements.set(movements.data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar tus puntos.'));
    }
  }
}
