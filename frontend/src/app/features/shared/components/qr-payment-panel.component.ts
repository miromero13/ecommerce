import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnDestroy, Output, inject, signal } from '@angular/core';
import { toast } from '@spartan-ng/brain/sonner';
import { firstValueFrom } from 'rxjs';

import { HlmButton } from '../../../components/button/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { QrPayment } from '../models/qr-payment.model';
import { QrPaymentApiService } from '../services/qr-payment-api.service';

/** Simulated QR (platform collection account): shows the code and waits for the bank confirmation. */
@Component({
  selector: 'app-qr-payment-panel',
  standalone: true,
  imports: [CommonModule, HlmButton],
  template: `
    @if (current(); as qr) {
      <div class="space-y-3 rounded-xl border border-slate-200 bg-white p-4 text-center">
        <p class="text-sm font-semibold text-slate-900">{{ title }}</p>
        <img [src]="qr.qr_image" alt="Código QR de pago" class="mx-auto size-48" />
        <p class="text-lg font-bold text-slate-900">{{ qr.amount | number: '1.2-2' }} {{ qr.currency | uppercase }}</p>
        <p class="text-xs text-slate-500">Referencia {{ qr.reference }} · vence {{ qr.expires_at | date: 'shortTime' }}</p>
        @if (qr.status === 'pending') {
          <div class="flex flex-col gap-2 sm:flex-row">
            <button hlmBtn type="button" variant="outline" class="flex-1" [disabled]="busy()" (click)="check()">Verificar pago</button>
            <button hlmBtn type="button" class="flex-1" [disabled]="busy()" (click)="simulate()">Simular pago (demo)</button>
          </div>
          <p class="text-[11px] text-slate-400">En producción el banco confirma el pago automáticamente.</p>
        } @else if (qr.status === 'expired') {
          <p class="text-sm font-medium text-red-600">El código QR expiró. Genera uno nuevo.</p>
        } @else {
          <p class="text-sm font-medium text-emerald-600">Pago recibido</p>
        }
      </div>
    }
  `,
})
export class QrPaymentPanelComponent implements OnDestroy {
  private readonly api = inject(QrPaymentApiService);
  protected readonly current = signal<QrPayment | null>(null);
  protected readonly busy = signal(false);
  private poll?: ReturnType<typeof setInterval>;

  @Input() title = 'Escanea el código QR con tu app bancaria';
  @Input() set qr(value: QrPayment | null) {
    this.current.set(value);
    this.stopPolling();
    if (value?.status === 'pending') this.poll = setInterval(() => void this.check(true), 5000);
  }
  @Output() readonly paid = new EventEmitter<QrPayment>();

  ngOnDestroy(): void {
    this.stopPolling();
  }

  protected async check(silent = false): Promise<void> {
    const qr = this.current();
    if (!qr) return;
    try {
      this.update((await firstValueFrom(this.api.status(qr.reference))).data);
      if (!silent && this.current()?.status === 'pending') toast.info('Aún no recibimos el pago.');
    } catch (error) {
      if (!silent) toast.error(getErrorMessage(error, 'No se pudo verificar el pago.'));
    }
  }

  protected async simulate(): Promise<void> {
    const qr = this.current();
    if (!qr) return;
    this.busy.set(true);
    try {
      const res = await firstValueFrom(this.api.simulate(qr.reference));
      toast.success(res.message);
      this.update(res.data);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo confirmar el pago.'));
    } finally {
      this.busy.set(false);
    }
  }

  private update(qr: QrPayment | null | undefined): void {
    if (!qr) return;
    this.current.set(qr);
    if (qr.status !== 'pending') {
      this.stopPolling();
      if (qr.status === 'paid' || qr.status === 'used') this.paid.emit(qr);
    }
  }

  private stopPolling(): void {
    if (this.poll) clearInterval(this.poll);
    this.poll = undefined;
  }
}
