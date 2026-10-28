import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { toast } from '@spartan-ng/brain/sonner';

import { HlmButton } from '../../../components/button/src';
import { HlmInput } from '../../../components/input/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { CashSessionApiService } from '../../shared/services/cash-session-api.service';

/** 1P-CU18: open the drawer with a starting amount, register deposits/withdrawals and close it counting the cash. */
@Component({
  selector: 'app-cash-drawer-panel',
  standalone: true,
  imports: [CommonModule, HlmButton, HlmInput],
  template: `
    <section class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm text-slate-700">
      @if (cash.current(); as drawer) {
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 class="text-lg font-semibold">Caja abierta · {{ drawer.branch_name }}</h2>
            <p class="text-xs text-slate-500">Abierta {{ drawer.opened_at | date: 'dd/MM/yyyy HH:mm' }} con {{ drawer.opening_amount }} Bs. · {{ drawer.sales_count }} ventas</p>
          </div>
          <div class="text-right">
            <p class="text-xs text-slate-500">Efectivo esperado en caja</p>
            <p class="text-2xl font-semibold text-slate-900">{{ drawer.expected_amount }} Bs.</p>
          </div>
        </div>
        <dl class="mt-3 grid grid-cols-2 gap-2 text-sm sm:grid-cols-3 lg:grid-cols-5">
          <div class="rounded-lg bg-slate-50 p-2"><dt class="text-xs text-slate-500">Inicial</dt><dd class="font-medium">{{ drawer.opening_amount }}</dd></div>
          <div class="rounded-lg bg-slate-50 p-2"><dt class="text-xs text-slate-500">Ventas efectivo</dt><dd class="font-medium">+{{ drawer.cash_sales }}</dd></div>
          <div class="rounded-lg bg-slate-50 p-2"><dt class="text-xs text-slate-500">Ingresos</dt><dd class="font-medium">+{{ drawer.deposits }}</dd></div>
          <div class="rounded-lg bg-slate-50 p-2"><dt class="text-xs text-slate-500">Retiros</dt><dd class="font-medium">-{{ drawer.withdrawals }}</dd></div>
          <div class="rounded-lg bg-slate-50 p-2"><dt class="text-xs text-slate-500">Vuelto entregado</dt><dd class="font-medium">{{ drawer.change_given }}</dd></div>
        </dl>
        <p class="mt-1 text-[11px] text-slate-500">Ventas por QR: {{ drawer.qr_sales }} Bs. (no entran en el efectivo de la caja).</p>

        <div class="mt-3 flex flex-wrap gap-2">
          <button hlmBtn type="button" variant="outline" size="sm" (click)="mode.set(mode() === 'movement' ? null : 'movement')">Ingreso / retiro</button>
          <button hlmBtn type="button" variant="outline" size="sm" (click)="mode.set(mode() === 'close' ? null : 'close')">Cerrar caja</button>
        </div>

        @if (mode() === 'movement') {
          <div class="mt-3 grid gap-2 rounded-xl border border-slate-200 p-3 sm:grid-cols-[auto_8rem_1fr_auto]">
            <select class="h-9 rounded-md border border-slate-300 bg-white px-2 text-sm" [value]="movementType()" (change)="movementType.set($any($event.target).value)">
              <option value="deposit">Ingreso</option>
              <option value="withdrawal">Retiro</option>
            </select>
            <input hlmInput type="number" min="0.01" step="0.01" placeholder="Monto" [value]="movementAmount()" (input)="movementAmount.set($any($event.target).value)" />
            <input hlmInput placeholder="Motivo (ej. depósito bancario, sencillo)" [value]="movementReason()" (input)="movementReason.set($any($event.target).value)" />
            <button hlmBtn type="button" size="sm" [disabled]="busy()" (click)="saveMovement()">Registrar</button>
          </div>
        }
        @if (mode() === 'close') {
          <div class="mt-3 grid gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 sm:grid-cols-[10rem_1fr_auto]">
            <input hlmInput type="number" min="0" step="0.01" placeholder="Efectivo contado" [value]="countedAmount()" (input)="countedAmount.set($any($event.target).value)" />
            <input hlmInput placeholder="Observación (opcional)" [value]="closingNote()" (input)="closingNote.set($any($event.target).value)" />
            <button hlmBtn type="button" size="sm" [disabled]="busy()" (click)="closeDrawer()">Cerrar caja</button>
            <p class="text-xs text-amber-900 sm:col-span-3">Cuenta el efectivo de la caja. Se registrará la diferencia con lo esperado (sobrante o faltante).</p>
          </div>
        }
      } @else {
        <div class="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 class="text-lg font-semibold">Caja cerrada</h2>
            <p class="text-sm text-slate-500">Abre tu caja con el monto inicial en efectivo para registrar ventas.</p>
            @if (lastClosing(); as closing) {
              <p class="mt-1 text-xs text-slate-600">Último cierre: esperado {{ closing.expected_amount }} Bs., contado {{ closing.counted_amount }} Bs., diferencia {{ closing.difference }} Bs.</p>
            }
          </div>
          <div class="flex gap-2">
            <input hlmInput class="w-36" type="number" min="0" step="0.01" placeholder="Monto inicial" [value]="openingAmount()" (input)="openingAmount.set($any($event.target).value)" />
            <button hlmBtn type="button" [disabled]="busy()" (click)="openDrawer()">Abrir caja</button>
          </div>
        </div>
      }
    </section>
  `,
})
export class CashDrawerPanelComponent implements OnInit {
  protected readonly cash = inject(CashSessionApiService);
  protected readonly mode = signal<'movement' | 'close' | null>(null);
  protected readonly busy = signal(false);
  protected readonly openingAmount = signal('');
  protected readonly movementType = signal<'deposit' | 'withdrawal'>('deposit');
  protected readonly movementAmount = signal('');
  protected readonly movementReason = signal('');
  protected readonly countedAmount = signal('');
  protected readonly closingNote = signal('');
  protected readonly lastClosing = signal<{ expected_amount: string; counted_amount: string | null; difference: string | null } | null>(null);

  ngOnInit(): void {
    this.cash.loadCurrent().catch((error) => toast.error(getErrorMessage(error, 'No se pudo consultar tu caja.')));
  }

  protected openDrawer(): Promise<void> {
    const amount = Number(this.openingAmount());
    if (this.openingAmount() === '' || !(amount >= 0)) {
      toast.warning('Ingresa el monto inicial en efectivo (puede ser 0).');
      return Promise.resolve();
    }
    return this.run(async () => {
      toast.success(await this.cash.open(amount));
      this.openingAmount.set('');
    }, 'No se pudo abrir la caja.');
  }

  protected saveMovement(): Promise<void> {
    const amount = Number(this.movementAmount());
    if (!(amount > 0) || this.movementReason().trim().length < 3) {
      toast.warning('Ingresa un monto mayor a 0 y el motivo del movimiento.');
      return Promise.resolve();
    }
    return this.run(async () => {
      toast.success(await this.cash.addMovement(this.movementType(), amount, this.movementReason().trim()));
      this.movementAmount.set('');
      this.movementReason.set('');
      this.mode.set(null);
    }, 'No se pudo registrar el movimiento.');
  }

  protected closeDrawer(): Promise<void> {
    const counted = Number(this.countedAmount());
    if (this.countedAmount() === '' || !(counted >= 0)) {
      toast.warning('Ingresa el efectivo contado en la caja.');
      return Promise.resolve();
    }
    return this.run(async () => {
      const { message, session } = await this.cash.close(counted, this.closingNote());
      toast.success(message);
      this.lastClosing.set(session ? { expected_amount: session.expected_amount, counted_amount: session.counted_amount, difference: session.difference } : null);
      this.countedAmount.set('');
      this.closingNote.set('');
      this.mode.set(null);
    }, 'No se pudo cerrar la caja.');
  }

  private async run(action: () => Promise<void>, fallback: string): Promise<void> {
    this.busy.set(true);
    try {
      await action();
    } catch (error) {
      toast.error(getErrorMessage(error, fallback));
    } finally {
      this.busy.set(false);
    }
  }
}
