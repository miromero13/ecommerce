import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { toast } from '@spartan-ng/brain/sonner';
import { firstValueFrom } from 'rxjs';

import { HlmButton } from '../../../components/button/src';
import { HlmInput } from '../../../components/input/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { PayoutSummary, Settlement } from '../../shared/models/payout.model';
import { PayoutApiService } from '../../shared/services/payout-api.service';

const SOURCE: Record<string, string> = { order: 'Pedido web', sale: 'Venta en caja', reservation_deposit: 'Anticipo de reserva' };
const METHOD: Record<string, string> = { card: 'Tarjeta', qr: 'QR' };

// Online payments land in the platform account; each day the company is paid its net amount.
@Component({
  selector: 'app-admin-payouts-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HlmButton, HlmInput],
  template: `
    <section class="space-y-6 text-slate-700">
      <header>
        <h1 class="text-2xl font-semibold">Cobros en línea y liquidaciones</h1>
        <p class="text-sm text-slate-500">Los pagos con tarjeta y QR los recibe la plataforma; cada día se te transfiere lo cobrado menos la comisión.</p>
      </header>

      @if (summary(); as s) {
        <div class="grid gap-3 sm:grid-cols-3">
          <div class="rounded-xl border border-slate-200 bg-white p-4"><p class="text-xs text-slate-500">Por transferirte</p><p class="text-2xl font-bold text-slate-900">{{ s.pending_net_amount | number: '1.2-2' }} {{ s.currency }}</p></div>
          <div class="rounded-xl border border-slate-200 bg-white p-4"><p class="text-xs text-slate-500">Ya transferido</p><p class="text-2xl font-bold text-emerald-700">{{ s.transferred_net_amount | number: '1.2-2' }} {{ s.currency }}</p></div>
          <div class="rounded-xl border border-slate-200 bg-white p-4"><p class="text-xs text-slate-500">Comisión de la plataforma</p><p class="text-2xl font-bold text-slate-900">{{ s.platform_fee_percent }} %</p></div>
        </div>
      }

      <form class="grid gap-3 rounded-xl border border-slate-200 bg-white p-4 sm:grid-cols-4" [formGroup]="bankForm" (ngSubmit)="saveBank()">
        <p class="text-sm font-semibold text-slate-900 sm:col-span-4">Cuenta bancaria para recibir las liquidaciones</p>
        <input hlmInput placeholder="Banco" formControlName="bank_name" />
        <input hlmInput placeholder="Número de cuenta" formControlName="bank_account_number" />
        <input hlmInput placeholder="Titular" formControlName="bank_account_holder" />
        <button hlmBtn type="submit" [disabled]="bankForm.invalid">Guardar cuenta</button>
      </form>

      <div class="space-y-2">
        <h2 class="text-base font-semibold text-slate-900">Liquidaciones diarias</h2>
        @for (item of settlements(); track item.id) {
          <article class="flex flex-col justify-between gap-2 rounded-xl border border-slate-200 bg-white p-4 text-sm sm:flex-row sm:items-center">
            <div>
              <p class="font-medium text-slate-900">{{ item.period_date | date: 'longDate' }} · {{ item.transactions_count }} cobro(s)</p>
              <p class="text-xs text-slate-500">Bruto {{ item.gross_amount }} − comisión {{ item.fee_amount }} = <strong>{{ item.net_amount }} {{ item.currency | uppercase }}</strong></p>
            </div>
            <span class="rounded-full px-2.5 py-1 text-xs font-medium" [class]="item.status === 'paid' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'">
              {{ item.status === 'paid' ? 'Transferida · ' + item.transfer_reference : 'Pendiente de transferencia' }}
            </span>
          </article>
        } @empty {
          <p class="text-sm text-slate-500">Aún no hay liquidaciones. Se generan cada día con los cobros del día anterior.</p>
        }
      </div>

      @if (summary()?.recent_transactions?.length) {
        <div class="space-y-2">
          <h2 class="text-base font-semibold text-slate-900">Últimos cobros recibidos por la plataforma</h2>
          <div class="overflow-hidden rounded-xl border border-slate-200 bg-white text-sm">
            @for (t of summary()!.recent_transactions; track t.id) {
              <div class="flex justify-between border-b border-slate-100 px-4 py-2 last:border-0">
                <span>{{ source(t.source_type) }} · {{ method(t.method) }} · {{ t.created_at | date: 'short' }}</span>
                <span class="font-medium">{{ t.net_amount }} {{ t.currency | uppercase }} {{ t.settlement_id ? '' : '(sin liquidar)' }}</span>
              </div>
            }
          </div>
        </div>
      }
    </section>
  `,
})
export class AdminPayoutsPageComponent {
  private readonly api = inject(PayoutApiService);
  private readonly fb = inject(FormBuilder);
  protected readonly summary = signal<PayoutSummary | null>(null);
  protected readonly settlements = signal<Settlement[]>([]);
  protected readonly bankForm = this.fb.nonNullable.group({
    bank_name: ['', [Validators.required, Validators.minLength(2)]],
    bank_account_number: ['', [Validators.required, Validators.pattern(/^[0-9-]{5,40}$/)]],
    bank_account_holder: ['', [Validators.required, Validators.minLength(2)]],
  });

  constructor() {
    void this.load();
  }

  protected source(type: string): string { return SOURCE[type] ?? type; }
  protected method(type: string): string { return METHOD[type] ?? type; }

  private async load(): Promise<void> {
    try {
      const [summary, settlements] = await Promise.all([
        firstValueFrom(this.api.summary()), firstValueFrom(this.api.settlements()),
      ]);
      this.summary.set(summary.data ?? null);
      this.settlements.set(settlements.data ?? []);
      const bank = summary.data?.bank_account;
      if (bank?.bank_account_number) {
        this.bankForm.reset({ bank_name: bank.bank_name ?? '', bank_account_number: bank.bank_account_number ?? '', bank_account_holder: bank.bank_account_holder ?? '' });
      }
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar las liquidaciones.'));
    }
  }

  protected async saveBank(): Promise<void> {
    try {
      toast.success((await firstValueFrom(this.api.updateBankAccount(this.bankForm.getRawValue()))).message);
      await this.load();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo guardar la cuenta bancaria.'));
    }
  }
}
