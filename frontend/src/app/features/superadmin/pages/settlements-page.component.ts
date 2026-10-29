import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { toast } from '@spartan-ng/brain/sonner';
import { firstValueFrom } from 'rxjs';

import { HlmButton } from '../../../components/button/src';
import { HlmInput } from '../../../components/input/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { Settlement } from '../../shared/models/payout.model';
import { PayoutApiService } from '../../shared/services/payout-api.service';

// The superadmin transfers each settlement to the company's bank account and records the receipt.
@Component({
  selector: 'app-settlements-page',
  standalone: true,
  imports: [CommonModule, HlmButton, HlmInput],
  template: `
    <section class="space-y-6 text-slate-700">
      <header class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 class="text-2xl font-semibold">Liquidaciones a empresas</h1>
          <p class="text-sm text-slate-500">Cada día se liquida a cada empresa lo cobrado en línea el día anterior, menos la comisión de la plataforma.</p>
        </div>
        <button hlmBtn type="button" variant="outline" [disabled]="running()" (click)="run()">Generar liquidaciones ahora</button>
      </header>

      @for (item of settlements(); track item.id) {
        <article class="space-y-3 rounded-xl border border-slate-200 bg-white p-4 text-sm">
          <div class="flex flex-col justify-between gap-2 sm:flex-row sm:items-start">
            <div>
              <p class="font-semibold text-slate-900">{{ item.tenant_name }} · {{ item.period_date | date: 'longDate' }}</p>
              <p class="text-xs text-slate-500">{{ item.transactions_count }} cobro(s) · bruto {{ item.gross_amount }} − comisión {{ item.fee_amount }}</p>
              <p class="text-xs text-slate-500">Cuenta: {{ item.bank_name || 'sin banco' }} {{ item.bank_account_number || '' }} {{ item.bank_account_holder ? '(' + item.bank_account_holder + ')' : '' }}</p>
            </div>
            <p class="text-lg font-bold text-slate-900">{{ item.net_amount }} {{ item.currency | uppercase }}</p>
          </div>
          @if (item.status === 'pending') {
            <div class="flex gap-2">
              <input hlmInput class="flex-1" placeholder="N.º de comprobante de la transferencia" [value]="references()[item.id] ?? ''" (input)="setReference(item.id, $event)" />
              <button hlmBtn type="button" [disabled]="(references()[item.id] ?? '').length < 3" (click)="markPaid(item)">Marcar transferida</button>
            </div>
          } @else {
            <p class="text-xs font-medium text-emerald-700">Transferida el {{ item.paid_at | date: 'short' }} · comprobante {{ item.transfer_reference }}</p>
          }
        </article>
      } @empty {
        <p class="text-sm text-slate-500">No hay liquidaciones generadas.</p>
      }
    </section>
  `,
})
export class SettlementsPageComponent {
  private readonly api = inject(PayoutApiService);
  protected readonly settlements = signal<Settlement[]>([]);
  protected readonly references = signal<Partial<Record<string, string>>>({});
  protected readonly running = signal(false);

  constructor() {
    void this.load();
  }

  protected setReference(id: string, event: Event): void {
    this.references.update((refs) => ({ ...refs, [id]: (event.target as HTMLInputElement).value.trim() }));
  }

  private async load(): Promise<void> {
    try {
      this.settlements.set((await firstValueFrom(this.api.settlements())).data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar las liquidaciones.'));
    }
  }

  protected async run(): Promise<void> {
    this.running.set(true);
    try {
      toast.success((await firstValueFrom(this.api.runSettlements())).message);
      await this.load();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron generar las liquidaciones.'));
    } finally {
      this.running.set(false);
    }
  }

  protected async markPaid(item: Settlement): Promise<void> {
    try {
      toast.success((await firstValueFrom(this.api.markPaid(item.id, this.references()[item.id] ?? ''))).message);
      await this.load();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo registrar la transferencia.'));
    }
  }
}
