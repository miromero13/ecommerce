import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideCheckCircle, lucideClock, lucidePrinter, lucideWifiOff, lucideX } from '@ng-icons/lucide';
import { OfflineOperation } from '../../../core/services/offline-queue.service';

@Component({
  selector: 'app-offline-provisional-receipt-dialog',
  standalone: true,
  imports: [CommonModule, NgIcon],
  providers: [provideIcons({ lucideCheckCircle, lucideClock, lucidePrinter, lucideWifiOff, lucideX })],
  template: `
    @if (operation) {
      <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in">
        <div class="relative w-full max-w-lg bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl shadow-2xl p-6 overflow-hidden flex flex-col max-h-[90vh]">
          
          <!-- Encabezado del Comprobante -->
          <div class="flex items-start justify-between gap-3 border-b border-zinc-100 dark:border-zinc-800 pb-4">
            <div class="flex items-center gap-3">
              <div class="h-11 w-11 rounded-2xl bg-amber-500/10 text-amber-600 flex items-center justify-center">
                <ng-icon name="lucideWifiOff" class="text-2xl" />
              </div>
              <div>
                <span class="inline-flex items-center gap-1 text-[11px] font-bold uppercase tracking-wider text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2.5 py-0.5 rounded-full border border-amber-200 dark:border-amber-800">
                  <ng-icon name="lucideClock" class="text-xs" />
                  Contingencia Offline
                </span>
                <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100 mt-1">
                  Comprobante Provisional
                </h3>
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

          <!-- Contenido scrollable del ticket -->
          <div class="overflow-y-auto flex-1 py-4 space-y-4 text-xs text-zinc-700 dark:text-zinc-300">
            <!-- Datos de la transacción -->
            <div class="bg-zinc-50 dark:bg-zinc-800/50 p-3.5 rounded-2xl border border-zinc-100 dark:border-zinc-800 space-y-1.5">
              <div class="flex justify-between">
                <span class="text-zinc-500">N° Comprobante:</span>
                <span class="font-mono font-bold text-zinc-900 dark:text-zinc-100">{{ operation.receipt_number }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-zinc-500">ID Operación:</span>
                <span class="font-mono text-[11px] text-zinc-600 dark:text-zinc-400">{{ operation.operation_id.substring(0, 18) }}...</span>
              </div>
              <div class="flex justify-between">
                <span class="text-zinc-500">Fecha y Hora:</span>
                <span>{{ operation.created_at | date:'dd/MM/yyyy HH:mm:ss' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-zinc-500">Cajero:</span>
                <span class="font-medium">{{ operation.cashier_name || 'Cajero' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-zinc-500">Modalidad:</span>
                <span class="font-bold text-emerald-600 dark:text-emerald-400 uppercase">
                  {{ operation.type === 'cash_sale' ? 'Venta al Contado (Efectivo)' : 'Reserva Presencial' }}
                </span>
              </div>
            </div>

            <!-- Tabla de prendas -->
            <div class="border border-zinc-200 dark:border-zinc-800 rounded-2xl overflow-hidden">
              <table class="w-full text-left">
                <thead class="bg-zinc-50 dark:bg-zinc-800/80 text-[11px] font-semibold text-zinc-600 dark:text-zinc-400 border-b border-zinc-200 dark:border-zinc-800">
                  <tr>
                    <th class="p-2.5">Prenda / SKU</th>
                    <th class="p-2.5 text-center">Cant.</th>
                    <th class="p-2.5 text-right">P. Unit</th>
                    <th class="p-2.5 text-right">Subtotal</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800">
                  @for (item of operation.items; track item.variant_id) {
                    <tr>
                      <td class="p-2.5">
                        <div class="font-medium text-zinc-900 dark:text-zinc-100">{{ item.product_name }}</div>
                        <div class="text-[10px] text-zinc-400 font-mono">{{ item.variant_sku }}</div>
                      </td>
                      <td class="p-2.5 text-center font-medium">{{ item.quantity }}</td>
                      <td class="p-2.5 text-right font-mono">{{ item.unit_price | number:'1.2-2' }}</td>
                      <td class="p-2.5 text-right font-mono font-semibold">{{ item.subtotal | number:'1.2-2' }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>

            <!-- Totales -->
            <div class="bg-zinc-50 dark:bg-zinc-800/50 p-3.5 rounded-2xl border border-zinc-100 dark:border-zinc-800 space-y-1.5 font-mono">
              <div class="flex justify-between text-zinc-500">
                <span>Subtotal:</span>
                <span>Bs {{ operation.subtotal | number:'1.2-2' }}</span>
              </div>
              @if (operation.discount > 0) {
                <div class="flex justify-between text-emerald-600 dark:text-emerald-400">
                  <span>Descuento:</span>
                  <span>- Bs {{ operation.discount | number:'1.2-2' }}</span>
                </div>
              }
              <div class="flex justify-between text-sm font-bold text-zinc-900 dark:text-zinc-100 pt-1 border-t border-zinc-200 dark:border-zinc-700">
                <span>TOTAL COBRADO:</span>
                <span class="text-primary font-bold">Bs {{ operation.total | number:'1.2-2' }}</span>
              </div>
              @if (operation.cash_received) {
                <div class="flex justify-between text-zinc-600 dark:text-zinc-400 pt-1 text-[11px]">
                  <span>Efectivo recibido:</span>
                  <span>Bs {{ operation.cash_received | number:'1.2-2' }}</span>
                </div>
                <div class="flex justify-between text-zinc-600 dark:text-zinc-400 text-[11px]">
                  <span>Cambio devuelto:</span>
                  <span>Bs {{ (operation.change_returned || 0) | number:'1.2-2' }}</span>
                </div>
              }
            </div>

            <!-- Leyenda legal de contingencia -->
            <div class="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-900 dark:text-amber-200 leading-relaxed">
              <strong>Aviso de Contingencia:</strong> Este documento acredita la operación comercial realizada fuera de línea. La transacción ha quedado resguardada de forma inmutable en la cola local de esta terminal y será sincronizada y consolidada con el servidor central de FashionStore al restablecer la red.
            </div>
          </div>

          <!-- Acciones del pie -->
          <div class="border-t border-zinc-100 dark:border-zinc-800 pt-4 flex items-center justify-between gap-3">
            <button
              type="button"
              (click)="printTicket()"
              class="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-xl border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-800 dark:text-zinc-200 transition cursor-pointer"
            >
              <ng-icon name="lucidePrinter" class="text-sm" />
              Imprimir ticket
            </button>

            <button
              type="button"
              (click)="close.emit()"
              class="px-5 py-2 text-xs font-semibold rounded-xl bg-zinc-900 text-white hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200 transition shadow-sm cursor-pointer"
            >
              Nueva venta
            </button>
          </div>

        </div>
      </div>
    }
  `
})
export class OfflineProvisionalReceiptDialogComponent {
  @Input() operation: OfflineOperation | null = null;
  @Output() close = new EventEmitter<void>();

  printTicket(): void {
    if (typeof window !== 'undefined') {
      window.print();
    }
  }
}
