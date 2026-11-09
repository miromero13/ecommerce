import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  lucideAlertCircle,
  lucideArrowLeft,
  lucideCheckCircle2,
  lucideCoins,
  lucideCreditCard,
  lucideDollarSign,
  lucideSparkles,
  lucideWallet,
} from '@ng-icons/lucide';
import { OfflineQueueService } from '../../../core/services/offline-queue.service';
import { OfflineSyncService } from '../../../core/services/offline-sync.service';

@Component({
  selector: 'app-offline-conflicts-page',
  standalone: true,
  imports: [CommonModule, RouterLink, NgIcon],
  providers: [
    provideIcons({
      lucideAlertCircle,
      lucideArrowLeft,
      lucideCheckCircle2,
      lucideCoins,
      lucideCreditCard,
      lucideDollarSign,
      lucideSparkles,
      lucideWallet,
    }),
  ],
  template: `
    <div class="space-y-6 max-w-5xl mx-auto py-2">
      <!-- Encabezado -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <a
            routerLink="/app/cajero/caja"
            class="inline-flex items-center gap-1.5 text-xs font-semibold text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200 transition-colors mb-2"
          >
            <ng-icon name="lucideArrowLeft" class="text-sm" />
            Volver a la Caja POS
          </a>
          <h1 class="text-2xl font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2.5">
            <span class="size-3 rounded-full bg-rose-500 animate-ping"></span>
            Resolución de Conflictos de Inventario
          </h1>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
            Operaciones vendidas en contingencia offline cuyo stock fue consumido en paralelo por otro canal.
          </p>
        </div>

        <div class="flex items-center gap-2">
          <span class="px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300 border border-rose-200 dark:border-rose-800">
            {{ conflictOperations().length }} {{ conflictOperations().length === 1 ? 'colisión pendiente' : 'colisiones pendientes' }}
          </span>
        </div>
      </div>

      <!-- Estado vacío si no hay conflictos -->
      @if (conflictOperations().length === 0) {
        <div class="p-12 text-center bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl shadow-sm space-y-3">
          <div class="h-16 w-16 rounded-3xl bg-emerald-500/10 text-emerald-600 flex items-center justify-center mx-auto">
            <ng-icon name="lucideCheckCircle2" class="text-3xl" />
          </div>
          <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100">
            Sin conflictos de inventario
          </h3>
          <p class="text-xs text-zinc-500 dark:text-zinc-400 max-w-md mx-auto">
            Todas las operaciones offline se han consolidado limpiamente en el inventario central sin colisiones.
          </p>
          <div class="pt-2">
            <a
              routerLink="/app/cajero/caja"
              class="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-xl bg-zinc-900 text-white hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200 transition"
            >
              Ir a la Caja POS
            </a>
          </div>
        </div>
      } @else {
        <!-- Lista de conflictos a resolver -->
        <div class="space-y-4">
          @for (op of conflictOperations(); track op.operation_id) {
            <div class="bg-white dark:bg-zinc-900 border border-rose-200 dark:border-rose-900/40 rounded-3xl p-6 shadow-sm space-y-4">
              
              <!-- Cabecera de la tarjeta -->
              <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3 border-b border-zinc-100 dark:border-zinc-800 pb-4">
                <div>
                  <div class="flex items-center gap-2">
                    <span class="font-mono font-bold text-base text-zinc-900 dark:text-zinc-100">
                      {{ op.receipt_number }}
                    </span>
                    <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300">
                      Quiebre de stock detectado
                    </span>
                  </div>
                  <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                    Fecha de emisión: {{ op.created_at | date:'dd/MM/yyyy HH:mm:ss' }} • Cajero: {{ op.cashier_name || 'Cajero' }}
                  </p>
                </div>

                <div class="text-right font-mono">
                  <span class="text-xs text-zinc-400 block">Total pagado por cliente:</span>
                  <span class="text-lg font-bold text-zinc-900 dark:text-zinc-100">
                    Bs {{ op.total | number:'1.2-2' }}
                  </span>
                </div>
              </div>

              <!-- Motivo del conflicto -->
              <div class="p-3.5 rounded-2xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200/80 dark:border-rose-900/40 flex items-start gap-2.5 text-xs text-rose-800 dark:text-rose-200">
                <ng-icon name="lucideAlertCircle" class="text-base shrink-0 mt-0.5" />
                <div>
                  <span class="font-bold block">Detalle de la colisión:</span>
                  <span>{{ op.sync_error || 'Inventario insuficiente en el servidor al momento de sincronizar.' }}</span>
                </div>
              </div>

              <!-- Prendas afectadas -->
              <div class="border border-zinc-200 dark:border-zinc-800 rounded-2xl p-3 bg-zinc-50/50 dark:bg-zinc-800/20 text-xs">
                <span class="text-[11px] font-bold text-zinc-500 uppercase tracking-wider block mb-2">
                  Prendas de la transacción:
                </span>
                <div class="space-y-1 font-mono">
                  @for (item of op.items; track item.variant_id) {
                    <div class="flex justify-between items-center py-1 border-b border-zinc-100 dark:border-zinc-800/80 last:border-0">
                      <span class="font-sans font-medium text-zinc-800 dark:text-zinc-200">{{ item.product_name }} ({{ item.variant_sku }})</span>
                      <span class="font-semibold">{{ item.quantity }} × Bs {{ item.unit_price | number:'1.2-2' }}</span>
                    </div>
                  }
                </div>
              </div>

              <!-- Acciones de resolución (ICONIX CU30) -->
              <div class="border-t border-zinc-100 dark:border-zinc-800 pt-4 flex flex-col sm:flex-row items-center justify-between gap-3">
                <div class="text-xs text-zinc-500">
                  Cliente: <strong class="text-zinc-800 dark:text-zinc-200">{{ op.customer_name || op.customer_email || 'Cliente Mostrador' }}</strong>
                </div>

                <div class="flex items-center gap-2.5 w-full sm:w-auto">
                  <!-- Opción A: Compensar en Billetera Digital con +10% -->
                  <button
                    type="button"
                    (click)="resolveWithWallet(op.operation_id, op.total, op.customer_email)"
                    [disabled]="resolvingId() === op.operation_id"
                    class="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 px-4 py-2.5 text-xs font-bold rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white transition shadow-sm cursor-pointer"
                    title="Acredita el saldo más un 10% adicional a la billetera digital del cliente"
                  >
                    <ng-icon name="lucideSparkles" class="text-sm" />
                    <span>Compensar Billetera (+10% = Bs {{ (op.total * 1.1) | number:'1.2-2' }})</span>
                  </button>

                  <!-- Opción B: Devolución física de efectivo -->
                  <button
                    type="button"
                    (click)="resolveWithRefund(op.operation_id, op.total)"
                    [disabled]="resolvingId() === op.operation_id"
                    class="px-3.5 py-2.5 text-xs font-semibold rounded-xl border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300 transition cursor-pointer"
                    title="Devolver el dinero en efectivo en el mostrador"
                  >
                    Devolver efectivo
                  </button>
                </div>
              </div>

            </div>
          }
        </div>
      }
    </div>
  `,
})
export class OfflineConflictsPageComponent {
  private readonly queueService = inject(OfflineQueueService);
  private readonly syncService = inject(OfflineSyncService);

  readonly resolvingId = signal<string | null>(null);

  readonly conflictOperations = computed(() =>
    this.queueService.operations().filter((op) => op.status === 'conflict_rejected')
  );

  // [CU30 - Secuencia: Paso 4] El Cajero ejecuta resolveWithWallet(operationId, amount, customerEmail) en OfflineConflictsPageComponent
  async resolveWithWallet(
    operationId: string,
    amount: number,
    customerEmail?: string | null
  ): Promise<void> {
    this.resolvingId.set(operationId);
    await this.syncService.resolveConflict(operationId, 'wallet_compensation', amount, customerEmail);
    this.resolvingId.set(null);
  }

  // [CU30 - Secuencia: Paso 5] El Cajero ejecuta resolveWithRefund(operationId, amount) en OfflineConflictsPageComponent
  async resolveWithRefund(operationId: string, amount: number): Promise<void> {
    this.resolvingId.set(operationId);
    await this.syncService.resolveConflict(operationId, 'cash_refund', amount);
    this.resolvingId.set(null);
  }
}
