import { Component, EventEmitter, Output, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  lucideAlertTriangle,
  lucideCheckCircle2,
  lucideChevronDown,
  lucideChevronUp,
  lucideClock,
  lucideDollarSign,
  lucideLayers,
  lucidePrinter,
  lucideRefreshCw,
  lucideShoppingBag,
  lucideWifi,
  lucideWifiOff,
  lucideX,
} from '@ng-icons/lucide';
import { OfflineOperation, OfflineQueueService } from '../../../core/services/offline-queue.service';
import { OfflineCatalogService } from '../../../core/services/offline-catalog.service';

@Component({
  selector: 'app-offline-queue-modal',
  standalone: true,
  imports: [CommonModule, NgIcon],
  providers: [
    provideIcons({
      lucideAlertTriangle,
      lucideCheckCircle2,
      lucideChevronDown,
      lucideChevronUp,
      lucideClock,
      lucideDollarSign,
      lucideLayers,
      lucidePrinter,
      lucideRefreshCw,
      lucideShoppingBag,
      lucideWifi,
      lucideWifiOff,
      lucideX,
    }),
  ],
  template: `
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in">
      <div class="relative w-full max-w-3xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl shadow-2xl p-6 overflow-hidden flex flex-col max-h-[90vh]">
        
        <!-- Header -->
        <div class="flex items-start justify-between gap-4 border-b border-zinc-100 dark:border-zinc-800 pb-4">
          <div class="flex items-center gap-3">
            <div class="h-12 w-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center">
              <ng-icon name="lucideLayers" class="text-2xl" />
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h3 class="text-lg font-bold text-zinc-900 dark:text-zinc-100">
                  Monitor de Cola de Operaciones Locales
                </h3>
                <span class="px-2 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider"
                  [ngClass]="offlineCatalog.isOffline() ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400' : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400'">
                  <ng-icon [name]="offlineCatalog.isOffline() ? 'lucideWifiOff' : 'lucideWifi'" class="inline mr-1" />
                  {{ offlineCatalog.isOffline() ? 'Offline' : 'En línea' }}
                </span>
              </div>
              <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                Ventas y reservas resguardadas en IndexedDB (RNF03) pendientes de sincronización central.
              </p>
            </div>
          </div>

          <button
            type="button"
            (click)="close.emit()"
            class="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 p-1.5 rounded-lg transition-colors cursor-pointer"
          >
            <ng-icon name="lucideX" class="text-base" />
          </button>
        </div>

        <!-- Tarjetas de métricas -->
        <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 py-4 border-b border-zinc-100 dark:border-zinc-800">
          <div class="bg-zinc-50 dark:bg-zinc-800/50 p-3 rounded-2xl border border-zinc-100 dark:border-zinc-800">
            <span class="text-[11px] font-medium text-zinc-500 block">Operaciones en cola</span>
            <span class="text-xl font-bold text-zinc-900 dark:text-zinc-100">
              {{ offlineQueue.pendingCount() }}
            </span>
          </div>

          <div class="bg-zinc-50 dark:bg-zinc-800/50 p-3 rounded-2xl border border-zinc-100 dark:border-zinc-800">
            <span class="text-[11px] font-medium text-zinc-500 block">Total acumulado</span>
            <span class="text-xl font-bold text-emerald-600 dark:text-emerald-400 font-mono">
              Bs {{ offlineQueue.totalPendingAmount() | number:'1.2-2' }}
            </span>
          </div>

          <div class="col-span-2 sm:col-span-1 bg-zinc-50 dark:bg-zinc-800/50 p-3 rounded-2xl border border-zinc-100 dark:border-zinc-800 flex flex-col justify-center">
            <span class="text-[11px] font-medium text-zinc-500 block">Persistencia</span>
            <span class="text-xs font-semibold text-zinc-700 dark:text-zinc-300">
              IndexedDB local segura
            </span>
          </div>
        </div>

        <!-- Lista scrollable de operaciones -->
        <div class="overflow-y-auto flex-1 py-4 space-y-3">
          @if (offlineQueue.operations().length === 0) {
            <div class="text-center py-12 text-zinc-400">
              <ng-icon name="lucideCheckCircle2" class="text-4xl text-emerald-500 mx-auto mb-2" />
              <p class="text-sm font-semibold text-zinc-800 dark:text-zinc-200">Cola local vacía</p>
              <p class="text-xs mt-0.5">Todas las operaciones han sido sincronizadas con el servidor.</p>
            </div>
          } @else {
            @for (op of offlineQueue.operations(); track op.operation_id) {
              <div class="border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 bg-white dark:bg-zinc-800/30 transition-all hover:border-zinc-300 dark:hover:border-zinc-700">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div class="space-y-1">
                    <div class="flex items-center gap-2">
                      <span class="font-mono font-bold text-sm text-zinc-900 dark:text-zinc-100">
                        {{ op.receipt_number }}
                      </span>
                      <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider"
                        [ngClass]="{
                          'bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300': op.status === 'local_pending',
                          'bg-blue-100 text-blue-800 dark:bg-blue-950/50 dark:text-blue-300': op.status === 'syncing',
                          'bg-rose-100 text-rose-800 dark:bg-rose-950/50 dark:text-rose-300': op.status === 'conflict_rejected'
                        }">
                        {{ op.status === 'local_pending' ? 'Pendiente' : op.status === 'syncing' ? 'Sincronizando' : 'Conflicto' }}
                      </span>
                    </div>

                    <div class="text-xs text-zinc-500 dark:text-zinc-400 flex items-center gap-2">
                      <span>{{ op.created_at | date:'dd/MM/yyyy HH:mm:ss' }}</span>
                      <span>•</span>
                      <span>{{ op.customer_name || 'Cliente Mostrador' }}</span>
                      <span>•</span>
                      <span>{{ op.items.length }} {{ op.items.length === 1 ? 'prenda' : 'prendas' }}</span>
                    </div>
                  </div>

                  <div class="flex items-center justify-between sm:justify-end gap-3 pt-2 sm:pt-0 border-t sm:border-0 border-zinc-100 dark:border-zinc-800">
                    <div class="text-right font-mono">
                      <span class="text-xs text-zinc-400 block sm:inline mr-1">Total:</span>
                      <span class="text-sm font-bold text-zinc-900 dark:text-zinc-100">
                        Bs {{ op.total | number:'1.2-2' }}
                      </span>
                    </div>

                    <button
                      type="button"
                      (click)="toggleExpand(op.operation_id)"
                      class="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-lg border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300 cursor-pointer"
                    >
                      <ng-icon [name]="isExpanded(op.operation_id) ? 'lucideChevronUp' : 'lucideChevronDown'" class="text-xs" />
                      {{ isExpanded(op.operation_id) ? 'Ocultar' : 'Auditar prendas' }}
                    </button>
                  </div>
                </div>

                <!-- Detalle expandido de auditoría de prendas -->
                @if (isExpanded(op.operation_id)) {
                  <div class="mt-3 pt-3 border-t border-zinc-100 dark:border-zinc-700/60 bg-zinc-50/50 dark:bg-zinc-900/50 rounded-xl p-3 animate-in fade-in">
                    <h5 class="text-[11px] font-bold text-zinc-500 uppercase tracking-wider mb-2">
                      Detalle de prendas resguardadas:
                    </h5>
                    <div class="space-y-1.5 text-xs font-mono">
                      @for (item of op.items; track item.variant_id) {
                        <div class="flex justify-between items-center py-1 border-b border-zinc-100 dark:border-zinc-800 last:border-0">
                          <div>
                            <span class="font-sans font-medium text-zinc-800 dark:text-zinc-200 block">{{ item.product_name }}</span>
                            <span class="text-[11px] text-zinc-400">{{ item.variant_sku }}</span>
                          </div>
                          <div class="text-right">
                            <span>{{ item.quantity }} × {{ item.unit_price | number:'1.2-2' }} = </span>
                            <span class="font-bold text-zinc-900 dark:text-zinc-100">Bs {{ item.subtotal | number:'1.2-2' }}</span>
                          </div>
                        </div>
                      }
                    </div>

                    @if (op.sync_error) {
                      <div class="mt-2 p-2 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-[11px] text-rose-700 dark:text-rose-300 flex items-center gap-1.5">
                        <ng-icon name="lucideAlertTriangle" class="text-xs shrink-0" />
                        <span>Error previo: {{ op.sync_error }}</span>
                      </div>
                    }
                  </div>
                }
              </div>
            }
          }
        </div>

        <!-- Footer -->
        <div class="border-t border-zinc-100 dark:border-zinc-800 pt-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <span class="text-xs text-zinc-500">
            Última verificación de cola: {{ now | date:'HH:mm:ss' }}
          </span>

          <div class="flex items-center gap-2 w-full sm:w-auto">
            <button
              type="button"
              (click)="syncNow.emit()"
              [disabled]="offlineCatalog.isOffline() || offlineQueue.pendingCount() === 0 || isSyncing"
              class="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-xl bg-zinc-900 text-white hover:bg-zinc-800 disabled:opacity-40 disabled:cursor-not-allowed dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200 transition shadow-sm cursor-pointer"
            >
              <ng-icon name="lucideRefreshCw" class="text-xs" [ngClass]="{ 'animate-spin': isSyncing }" />
              {{ isSyncing ? 'Sincronizando lote...' : 'Sincronizar lote ahora' }}
            </button>

            <button
              type="button"
              (click)="close.emit()"
              class="px-4 py-2 text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition cursor-pointer"
            >
              Cerrar
            </button>
          </div>
        </div>

      </div>
    </div>
  `,
})
export class OfflineQueueModalComponent {
  readonly offlineQueue = inject(OfflineQueueService);
  readonly offlineCatalog = inject(OfflineCatalogService);

  @Output() close = new EventEmitter<void>();
  @Output() syncNow = new EventEmitter<void>();

  isSyncing = false;
  now = new Date();
  private expandedOperations = signal<Set<string>>(new Set());

  toggleExpand(operationId: string): void {
    const current = new Set(this.expandedOperations());
    if (current.has(operationId)) {
      current.delete(operationId);
    } else {
      current.add(operationId);
    }
    this.expandedOperations.set(current);
  }

  isExpanded(operationId: string): boolean {
    return this.expandedOperations().has(operationId);
  }
}
