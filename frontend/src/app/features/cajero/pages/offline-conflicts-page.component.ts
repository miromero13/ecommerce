import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { firstValueFrom } from 'rxjs';
import { toast } from '@spartan-ng/brain/sonner';

import { HlmButton } from '../../../components/button/src';
import { HlmInput } from '../../../components/input/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import {
  ConflictAction,
  OfflineConflict,
  OfflineSyncService,
  ResolveConflictRequest,
} from '../../../core/services/offline-sync.service';
import { CatalogApiService } from '../../shared/services/catalog-api.service';

type ExchangeOption = { variant_id: string; label: string; price: number; stock: number };

const RESOLUTION_LABELS: Record<ConflictAction, string> = {
  delivered: 'Prenda ya entregada (venta confirmada)',
  cash_refund: 'Devolución en efectivo',
  wallet_credit: 'Crédito en billetera (+10 %)',
  exchange: 'Cambio por otra prenda',
};

/**
 * CU30: offline sales that lost the last unit to a sale that reached the server first.
 * The conflicts live on the server; each one is resolved once.
 */
@Component({
  selector: 'app-offline-conflicts-page',
  standalone: true,
  imports: [CommonModule, HlmButton, HlmInput],
  template: `
    <section class="mx-auto max-w-5xl space-y-5 py-2">
      <header class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 class="text-2xl font-semibold">Conflictos de ventas offline</h1>
          <p class="text-sm text-slate-500">Ventas cobradas sin conexión cuya última unidad ya la había vendido otra venta que llegó antes al servidor.</p>
        </div>
        <div class="flex gap-2">
          <button hlmBtn type="button" size="sm" [variant]="tab() === 'pending' ? 'default' : 'outline'" (click)="setTab('pending')">Pendientes</button>
          <button hlmBtn type="button" size="sm" [variant]="tab() === 'resolved' ? 'default' : 'outline'" (click)="setTab('resolved')">Resueltos</button>
        </div>
      </header>

      <div class="rounded-2xl border border-amber-300 bg-amber-50 p-4 text-amber-900">
        <p class="text-sm font-semibold">Dinero pendiente de resolución: {{ pendingTotal() | number: '1.2-2' }} Bs. ({{ pendingCount() }} ventas)</p>
        <p class="text-xs">Es efectivo que está en caja retenido hasta resolver cada conflicto.</p>
      </div>

      @if (refundReceipt(); as r) {
        <section class="receipt-print space-y-2 rounded-2xl border border-slate-300 bg-white p-5 text-sm text-slate-800">
          <h2 class="text-lg font-semibold">Comprobante de devolución {{ r.refund_receipt_number }}</h2>
          <p>Fecha: {{ r.resolved_at | date: 'dd/MM/yyyy HH:mm' }}</p>
          <p>Cliente: {{ r.customer_name || 'Cliente' }} {{ r.customer_phone ? '· ' + r.customer_phone : '' }} {{ r.customer_email ? '· ' + r.customer_email : '' }}</p>
          <p>Venta offline: {{ r.receipt_number }}</p>
          <p class="text-base font-semibold">Monto devuelto: {{ (r.refund_amount ?? 0) | number: '1.2-2' }} Bs.</p>
          <p>Motivo: {{ r.reason }}</p>
          <div class="pt-10">
            <div class="w-64 border-t border-slate-500 pt-1 text-center text-xs">Firma del cliente</div>
          </div>
          <div class="flex gap-2 pt-2 print:hidden">
            <button hlmBtn type="button" size="sm" (click)="print()">Imprimir comprobante</button>
            <button hlmBtn type="button" size="sm" variant="outline" (click)="refundReceipt.set(null)">Cerrar</button>
          </div>
        </section>
      }

      @if (loading()) {
        <p class="text-sm text-slate-500">Cargando conflictos...</p>
      } @else {
        @for (c of conflicts(); track c.id) {
          <article class="space-y-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div class="flex flex-wrap items-start justify-between gap-2 border-b border-slate-100 pb-3">
              <div>
                <p class="font-mono text-base font-semibold">{{ c.receipt_number }}</p>
                <p class="text-xs text-slate-500">
                  Venta offline: {{ c.offline_created_at | date: 'dd/MM/yyyy HH:mm' }} · Cajero: {{ c.cashier_name || 'Cajero' }}
                </p>
                <p class="text-xs text-slate-600">
                  Cliente: <strong>{{ c.customer_name || 'Sin nombre' }}</strong>
                  {{ c.customer_phone ? '· Tel. ' + c.customer_phone : '' }} {{ c.customer_email ? '· ' + c.customer_email : '' }}
                </p>
              </div>
              <div class="text-right">
                <p class="text-xs text-slate-500">Monto pagado</p>
                <p class="text-lg font-semibold">{{ c.total | number: '1.2-2' }} Bs.</p>
              </div>
            </div>

            <div class="text-sm">
              @for (item of c.items; track item.variant_id) {
                <div class="flex justify-between border-b border-slate-50 py-1">
                  <span>{{ item.product_name }} ({{ item.sku }})</span>
                  <span>{{ item.quantity }} × {{ item.unit_price | number: '1.2-2' }}</span>
                </div>
              }
            </div>
            <p class="rounded-lg bg-rose-50 p-2 text-xs text-rose-800">Motivo: {{ c.reason }}</p>

            @if (c.status === 'resolved') {
              <div class="grid gap-1 rounded-lg bg-emerald-50 p-3 text-xs text-emerald-900">
                <p class="font-semibold">{{ resolutionLabel(c.resolution) }} · {{ c.resolved_at | date: 'dd/MM/yyyy HH:mm' }}</p>
                @if (c.refund_amount) { <p>Efectivo devuelto: {{ c.refund_amount | number: '1.2-2' }} Bs.</p> }
                @if (c.wallet_credit_amount) { <p>Acreditado en billetera: {{ c.wallet_credit_amount | number: '1.2-2' }} Bs.</p> }
                @if (c.extra_charged) { <p>Diferencia cobrada: {{ c.extra_charged | number: '1.2-2' }} Bs.</p> }
                @if (c.refund_receipt_number) { <p>Comprobante de devolución: {{ c.refund_receipt_number }}</p> }
                @if (c.resolution_notes) { <p>Notas: {{ c.resolution_notes }}</p> }
              </div>
            } @else if (activeId() !== c.id) {
              <div class="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3">
                <span class="text-sm font-medium">¿La prenda ya fue entregada al cliente?</span>
                <button hlmBtn type="button" size="sm" (click)="start(c, 'delivered')">Sí</button>
                <button hlmBtn type="button" size="sm" variant="outline" (click)="start(c, null)">No</button>
              </div>
            } @else {
              <div class="space-y-3 border-t border-slate-100 pt-3">
                @if (option() === 'delivered') {
                  <p class="text-sm">La venta se mantiene y se registrará un ajuste de inventario; se avisará a los administradores para que cuenten el stock.</p>
                } @else {
                  <div class="flex flex-wrap gap-2">
                    <button hlmBtn type="button" size="sm" [variant]="option() === 'cash_refund' ? 'default' : 'outline'" (click)="option.set('cash_refund')">Devolver efectivo</button>
                    <button hlmBtn type="button" size="sm" [variant]="option() === 'wallet_credit' ? 'default' : 'outline'" (click)="option.set('wallet_credit')">Billetera +10 %</button>
                    <button hlmBtn type="button" size="sm" [variant]="option() === 'exchange' ? 'default' : 'outline'" (click)="chooseExchange(c)">Cambiar por otra prenda</button>
                  </div>
                }

                @if (option() === 'cash_refund') {
                  <p class="text-sm">Se retirarán {{ c.total | number: '1.2-2' }} Bs. de tu caja abierta y se emitirá un comprobante de devolución.</p>
                }
                @if (option() === 'wallet_credit') {
                  <div class="space-y-1">
                    <input hlmInput type="email" class="w-full sm:w-80" placeholder="Correo del cliente registrado" [value]="walletEmail()" (input)="walletEmail.set($any($event.target).value)" />
                    <p class="text-sm">Se acreditarán {{ c.total * 1.1 | number: '1.2-2' }} Bs. en su billetera.</p>
                  </div>
                }
                @if (option() === 'exchange') {
                  <div class="space-y-2">
                    <div class="flex flex-wrap gap-2">
                      <input hlmInput class="w-full sm:w-64" placeholder="Buscar prenda" [value]="exchangeQuery()" (input)="exchangeQuery.set($any($event.target).value)" (keyup.enter)="searchExchange(c)" />
                      <button hlmBtn type="button" size="sm" variant="outline" (click)="searchExchange(c)">Buscar</button>
                    </div>
                    <select class="h-9 w-full rounded-md border border-slate-300 bg-white px-2 text-sm" [value]="exchangeVariantId()" (change)="exchangeVariantId.set($any($event.target).value)">
                      <option value="">Elige una prenda con stock</option>
                      @for (o of exchangeOptions(); track o.variant_id) {
                        <option [value]="o.variant_id">{{ o.label }} · {{ o.price | number: '1.2-2' }} Bs. · stock {{ o.stock }}</option>
                      }
                    </select>
                    <input hlmInput type="number" min="1" class="w-28" [value]="exchangeQty()" (input)="exchangeQty.set(+$any($event.target).value || 1)" />
                    @if (exchangeVariantId()) {
                      @if (difference(c) > 0) {
                        <p class="text-sm">El cliente paga la diferencia: {{ difference(c) | number: '1.2-2' }} Bs.</p>
                        <input hlmInput type="number" min="0" step="0.01" class="w-40" placeholder="Efectivo recibido" [value]="exchangeCash()" (input)="exchangeCash.set($any($event.target).value)" />
                      } @else if (difference(c) < 0) {
                        <p class="text-sm">Se devuelve al cliente: {{ -difference(c) | number: '1.2-2' }} Bs.</p>
                        <div class="flex gap-2">
                          <button hlmBtn type="button" size="sm" [variant]="differenceMethod() === 'cash' ? 'default' : 'outline'" (click)="differenceMethod.set('cash')">En efectivo</button>
                          <button hlmBtn type="button" size="sm" [variant]="differenceMethod() === 'wallet' ? 'default' : 'outline'" (click)="differenceMethod.set('wallet')">A su billetera</button>
                        </div>
                        @if (differenceMethod() === 'wallet') {
                          <input hlmInput type="email" class="w-full sm:w-80" placeholder="Correo del cliente registrado" [value]="walletEmail()" (input)="walletEmail.set($any($event.target).value)" />
                        }
                      } @else {
                        <p class="text-sm">Mismo precio: no hay diferencia.</p>
                      }
                    }
                  </div>
                }

                <input hlmInput class="w-full" placeholder="Notas (opcional)" [value]="notes()" (input)="notes.set($any($event.target).value)" />
                <div class="flex gap-2">
                  <button hlmBtn type="button" size="sm" [disabled]="busy() || !option()" (click)="resolve(c)">Confirmar resolución</button>
                  <button hlmBtn type="button" size="sm" variant="ghost" (click)="activeId.set(null)">Cancelar</button>
                </div>
              </div>
            }
          </article>
        } @empty {
          <div class="rounded-2xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">
            {{ tab() === 'pending' ? 'No hay conflictos pendientes.' : 'Aún no hay conflictos resueltos.' }}
          </div>
        }
      }
    </section>
  `,
})
export class OfflineConflictsPageComponent {
  private readonly syncService = inject(OfflineSyncService);
  private readonly catalogApi = inject(CatalogApiService);

  protected readonly tab = signal<'pending' | 'resolved'>('pending');
  protected readonly conflicts = signal<OfflineConflict[]>([]);
  protected readonly pendingCount = signal(0);
  protected readonly pendingTotal = signal(0);
  protected readonly loading = signal(false);
  protected readonly busy = signal(false);
  protected readonly refundReceipt = signal<OfflineConflict | null>(null);

  // Form state of the conflict being resolved (one at a time).
  protected readonly activeId = signal<string | null>(null);
  protected readonly option = signal<ConflictAction | null>(null);
  protected readonly walletEmail = signal('');
  protected readonly notes = signal('');
  protected readonly exchangeQuery = signal('');
  protected readonly exchangeOptions = signal<ExchangeOption[]>([]);
  protected readonly exchangeVariantId = signal('');
  protected readonly exchangeQty = signal(1);
  protected readonly exchangeCash = signal('');
  protected readonly differenceMethod = signal<'cash' | 'wallet'>('cash');
  private readonly exchangeOption = computed(() => this.exchangeOptions().find((o) => o.variant_id === this.exchangeVariantId()) ?? null);

  constructor() {
    void this.load();
  }

  // [CU30 - Secuencia: Paso 4] El Cajero ejecuta setTab(tab) en OfflineConflictsPageComponent
  protected setTab(tab: 'pending' | 'resolved'): void {
    this.tab.set(tab);
    this.activeId.set(null);
    void this.load();
  }

  private async load(): Promise<void> {
    this.loading.set(true);
    try {
      const data = await this.syncService.loadConflicts(this.tab());
      this.conflicts.set(data.items);
      this.pendingCount.set(data.pending_count);
      this.pendingTotal.set(data.pending_total);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar los conflictos.'));
    } finally {
      this.loading.set(false);
    }
  }

  // Sí → 'delivered'; No → null until one of the three options is picked.
  protected start(c: OfflineConflict, option: ConflictAction | null): void {
    this.activeId.set(c.id);
    this.option.set(option);
    this.walletEmail.set(c.customer_email ?? '');
    this.notes.set('');
    this.exchangeVariantId.set('');
    this.exchangeQty.set(1);
    this.exchangeCash.set('');
    this.differenceMethod.set('cash');
  }

  protected chooseExchange(c: OfflineConflict): void {
    this.option.set('exchange');
    if (!this.exchangeOptions().length) void this.searchExchange(c);
  }

  protected async searchExchange(c: OfflineConflict): Promise<void> {
    try {
      const res = await firstValueFrom(this.catalogApi.listProducts({ q: this.exchangeQuery() || undefined, branch_id: c.branch_id }));
      this.exchangeOptions.set(
        (res.data ?? []).flatMap((p) =>
          (p.variants ?? [])
            .filter((v) => (v.branch_quantity ?? 0) > 0)
            .map((v) => ({ variant_id: v.id, label: `${p.name} (${v.sku})`, price: Number(v.price), stock: v.branch_quantity ?? 0 })),
        ),
      );
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo consultar el catálogo.'));
    }
  }

  /** Positive: the customer pays it; negative: it is returned to the customer. */
  protected difference(c: OfflineConflict): number {
    const o = this.exchangeOption();
    return o ? Number((o.price * this.exchangeQty() - c.total).toFixed(2)) : 0;
  }

  protected resolutionLabel(action: ConflictAction | null): string {
    return action ? RESOLUTION_LABELS[action] : '';
  }

  // [CU30 - Secuencia: Paso 5] El Cajero ejecuta resolve(c) en OfflineConflictsPageComponent
  protected async resolve(c: OfflineConflict): Promise<void> {
    const action = this.option();
    if (!action) return;
    const body: ResolveConflictRequest = { action, notes: this.notes().trim() || undefined };
    const email = this.walletEmail().trim();

    if (action === 'wallet_credit') {
      if (!email) return void toast.warning('Ingresa el correo del cliente registrado.');
      body.customer_email = email;
    }
    if (action === 'exchange') {
      if (!this.exchangeOption()) return void toast.warning('Elige la prenda para el cambio.');
      body.exchange_items = [{ variant_id: this.exchangeVariantId(), quantity: this.exchangeQty() }];
      const diff = this.difference(c);
      if (diff > 0) {
        const received = Number(this.exchangeCash());
        if (this.exchangeCash() === '' || received < diff) return void toast.warning('El efectivo recibido no cubre la diferencia.');
        body.cash_received = received;
      } else if (diff < 0) {
        body.difference_method = this.differenceMethod();
        if (body.difference_method === 'wallet') {
          if (!email) return void toast.warning('Ingresa el correo del cliente registrado.');
          body.customer_email = email;
        }
      }
    }

    this.busy.set(true);
    const resolved = await this.syncService.resolveConflict(c.id, body);
    this.busy.set(false);
    if (!resolved) return;

    this.activeId.set(null);
    // Cash leaving the drawer is backed by a refund receipt signed by the customer.
    if (resolved.refund_receipt_number) this.refundReceipt.set(resolved);
    await this.load();
  }

  protected print(): void {
    window.print();
  }
}
