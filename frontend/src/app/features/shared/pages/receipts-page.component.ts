import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { toast } from '@spartan-ng/brain/sonner';

import { getErrorMessage } from '../../../core/utils/http-error.util';
import { ReceiptActionsComponent } from '../components/receipt-actions.component';
import { PaymentReceipt, ReceiptKind } from '../models/receipt.model';
import { ReceiptApiService } from '../services/receipt-api.service';

const FILTERS: { value: ReceiptKind | ''; label: string }[] = [
  { value: '', label: 'Todos' },
  { value: 'order', label: 'Pedidos web' },
  { value: 'sale', label: 'Ventas en tienda' },
  { value: 'reservation_deposit', label: 'Anticipos' },
  { value: 'subscription', label: 'Suscripción' },
];

/** Payment receipts visible to the user: the admin sees the company's, managers and cashiers their branch's. */
@Component({
  selector: 'app-receipts-page',
  standalone: true,
  imports: [CommonModule, ReceiptActionsComponent],
  template: `
    <section class="space-y-5 text-slate-700">
      <header>
        <h1 class="text-2xl font-semibold">Comprobantes</h1>
        <p class="text-sm text-slate-500">Cada pago emite un comprobante con su número correlativo; se envía por correo al cliente y puede descargarse en PDF.</p>
      </header>
      <div class="flex flex-wrap gap-2">
        @for (filter of filters; track filter.value) {
          <button type="button" class="cursor-pointer rounded-full border px-3 py-1 text-sm"
            [class.bg-emerald-700]="kind() === filter.value" [class.text-white]="kind() === filter.value"
            (click)="setKind(filter.value)">{{ filter.label }}</button>
        }
      </div>
      <div class="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table class="w-full text-sm">
          <thead class="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr><th class="p-3">N°</th><th class="p-3">Fecha</th><th class="p-3">Tipo</th><th class="p-3">Cliente</th><th class="p-3">Medio</th><th class="p-3 text-right">Total</th><th class="p-3">Correo</th><th class="p-3"></th></tr>
          </thead>
          <tbody>
            @for (receipt of receipts(); track receipt.id) {
              <tr class="border-t border-slate-100">
                <td class="p-3 font-mono text-xs font-semibold">{{ receipt.number }}</td>
                <td class="p-3">{{ receipt.issued_at | date: 'dd/MM/yyyy HH:mm' }}</td>
                <td class="p-3">{{ receipt.kind_label }}</td>
                <td class="p-3">{{ receipt.customer_name || 'Sin nombre' }}</td>
                <td class="p-3">{{ receipt.payment_method_label }}</td>
                <td class="p-3 text-right font-semibold">{{ receipt.total }} {{ receipt.currency }}</td>
                <td class="p-3 text-xs">{{ receipt.customer_email ? (receipt.emailed_at ? 'Enviado' : 'Pendiente') : 'Sin correo' }}</td>
                <td class="p-3"><app-receipt-actions [kind]="receipt.kind" [sourceId]="receipt.source_id" [showResend]="!!receipt.customer_email" /></td>
              </tr>
            } @empty {
              <tr><td colspan="8" class="p-4 text-slate-500">No hay comprobantes para mostrar.</td></tr>
            }
          </tbody>
        </table>
      </div>
    </section>
  `,
})
export class ReceiptsPageComponent {
  private readonly api = inject(ReceiptApiService);
  protected readonly filters = FILTERS;
  protected readonly kind = signal<ReceiptKind | ''>('');
  protected readonly receipts = signal<PaymentReceipt[]>([]);

  constructor() {
    void this.load();
  }

  protected setKind(kind: ReceiptKind | ''): void {
    this.kind.set(kind);
    void this.load();
  }

  private async load(): Promise<void> {
    try {
      this.receipts.set((await firstValueFrom(this.api.list(this.kind() || undefined))).data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar los comprobantes.'));
    }
  }
}
