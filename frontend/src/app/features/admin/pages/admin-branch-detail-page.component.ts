import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { toast } from '@spartan-ng/brain/sonner';

import { getErrorMessage } from '../../../core/utils/http-error.util';
import { AdminBranch } from '../models/admin-branch.model';
import { AdminUsuario } from '../models/admin-user.model';
import { AdminBranchService } from '../services/admin-branch.service';
import { AdminUserService } from '../services/admin-user.service';
import { CashSession } from '../../shared/models/cash-session.model';
import { DashboardSummary } from '../../shared/models/dashboard.model';
import { InventoryBranchStock } from '../../shared/models/inventory.model';
import { Order } from '../../shared/models/order.model';
import { Reservation } from '../../shared/models/reservation.model';
import { Sale } from '../../shared/models/sale.model';
import { CashSessionApiService } from '../../shared/services/cash-session-api.service';
import { CheckoutApiService } from '../../shared/services/checkout-api.service';
import { DashboardApiService } from '../../shared/services/dashboard-api.service';
import { InventoryApiService } from '../../shared/services/inventory-api.service';
import { ReservationApiService } from '../../shared/services/reservation-api.service';
import { SalesApiService } from '../../shared/services/sales-api.service';

type BranchTab = 'summary' | 'inventory' | 'sales' | 'orders' | 'staff' | 'cash';

const TABS: { key: BranchTab; label: string }[] = [
  { key: 'summary', label: 'Resumen' },
  { key: 'inventory', label: 'Inventario' },
  { key: 'sales', label: 'Ventas' },
  { key: 'orders', label: 'Pedidos y reservas' },
  { key: 'staff', label: 'Personal' },
  { key: 'cash', label: 'Caja' },
];

/** The administrator works inside ONE branch: every list below is requested with this branch's id only. */
@Component({
  selector: 'app-admin-branch-detail-page',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <section class="space-y-5 text-slate-700">
      <header class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <a routerLink="/app/admin/branch" class="text-sm text-emerald-700 hover:underline">← Volver a todas las sucursales</a>
          <h1 class="mt-1 text-2xl font-semibold text-slate-900">{{ branch()?.name ?? 'Sucursal' }}</h1>
          <p class="text-sm text-slate-500">{{ branch()?.city }} · Solo se muestra la información de esta sucursal.</p>
        </div>
        @if (branch(); as b) {
          <span class="rounded-full px-3 py-1 text-xs font-medium" [class.bg-emerald-100]="b.is_active" [class.text-emerald-800]="b.is_active"
            [class.bg-slate-100]="!b.is_active" [class.text-slate-600]="!b.is_active">{{ b.is_active ? 'Activa' : 'Inactiva' }}</span>
        }
      </header>

      @if (notFound()) {
        <p class="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">La sucursal no existe o no pertenece a tu empresa.</p>
      } @else {
        <nav class="flex flex-wrap gap-2 border-b border-slate-200 pb-2" aria-label="Secciones de la sucursal">
          @for (tab of tabs; track tab.key) {
            <button type="button" class="cursor-pointer rounded-md px-3 py-1.5 text-sm font-medium"
              [class.bg-emerald-700]="activeTab() === tab.key" [class.text-white]="activeTab() === tab.key"
              [class.hover:bg-slate-100]="activeTab() !== tab.key" (click)="activeTab.set(tab.key)">{{ tab.label }}</button>
          }
        </nav>

        @switch (activeTab()) {
          @case ('summary') {
            @if (summary(); as s) {
              <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
                <div class="rounded-xl border border-slate-200 bg-white p-4"><p class="text-xs text-slate-500">Ventas</p><p class="text-xl font-semibold">{{ s.total_sales }}</p></div>
                <div class="rounded-xl border border-slate-200 bg-white p-4"><p class="text-xs text-slate-500">Operaciones</p><p class="text-xl font-semibold">{{ s.total_orders }}</p></div>
                <div class="rounded-xl border border-slate-200 bg-white p-4"><p class="text-xs text-slate-500">Ticket promedio</p><p class="text-xl font-semibold">{{ s.average_ticket }}</p></div>
                <div class="rounded-xl border border-slate-200 bg-white p-4"><p class="text-xs text-slate-500">Unidades vendidas</p><p class="text-xl font-semibold">{{ s.total_units_sold }}</p></div>
                <div class="rounded-xl border border-slate-200 bg-white p-4"><p class="text-xs text-slate-500">Stock disponible</p><p class="text-xl font-semibold">{{ s.total_available_stock }} / {{ s.total_stock }}</p></div>
                <div class="rounded-xl border border-slate-200 bg-white p-4"><p class="text-xs text-slate-500">Prendas con stock bajo</p><p class="text-xl font-semibold">{{ s.low_stock_items }}</p></div>
                <div class="rounded-xl border border-slate-200 bg-white p-4"><p class="text-xs text-slate-500">Reservas pendientes</p><p class="text-xl font-semibold">{{ s.pending_reservations }}</p></div>
                <div class="rounded-xl border border-slate-200 bg-white p-4"><p class="text-xs text-slate-500">Cajas abiertas</p><p class="text-xl font-semibold">{{ openDrawers() }}</p></div>
              </div>
            } @else {
              <p class="text-sm text-slate-500">Cargando resumen...</p>
            }
          }
          @case ('inventory') {
            <div class="overflow-x-auto rounded-xl border border-slate-200 bg-white">
              <table class="w-full text-sm">
                <thead class="bg-slate-50 text-left text-xs uppercase text-slate-500"><tr><th class="p-3">Prenda</th><th class="p-3">Talla / color</th><th class="p-3">SKU</th><th class="p-3 text-right">Stock</th><th class="p-3 text-right">Apartado</th><th class="p-3 text-right">Disponible</th><th class="p-3 text-right">Mínimo</th></tr></thead>
                <tbody>
                  @for (item of stock(); track item.variant_id) {
                    <tr class="border-t border-slate-100" [class.bg-amber-50]="item.available_quantity <= item.minimum_stock">
                      <td class="p-3 font-medium text-slate-900">{{ item.product_name }}</td>
                      <td class="p-3">{{ item.size_name || 'Única' }} · {{ item.color_name || 'Sin color' }}</td>
                      <td class="p-3 font-mono text-xs">{{ item.variant_sku }}</td>
                      <td class="p-3 text-right">{{ item.quantity }}</td>
                      <td class="p-3 text-right">{{ item.reserved_quantity }}</td>
                      <td class="p-3 text-right font-semibold">{{ item.available_quantity }}</td>
                      <td class="p-3 text-right">{{ item.minimum_stock }}</td>
                    </tr>
                  } @empty { <tr><td colspan="7" class="p-4 text-slate-500">Esta sucursal no tiene inventario.</td></tr> }
                </tbody>
              </table>
            </div>
          }
          @case ('sales') {
            <div class="overflow-x-auto rounded-xl border border-slate-200 bg-white">
              <table class="w-full text-sm">
                <thead class="bg-slate-50 text-left text-xs uppercase text-slate-500"><tr><th class="p-3">Fecha</th><th class="p-3">Tipo</th><th class="p-3">Medio</th><th class="p-3 text-right">Ítems</th><th class="p-3 text-right">Total</th></tr></thead>
                <tbody>
                  @for (sale of sales(); track sale.id) {
                    <tr class="border-t border-slate-100">
                      <td class="p-3">{{ sale.created_at | date: 'dd/MM/yyyy HH:mm' }}</td>
                      <td class="p-3">{{ sale.type === 'venta virtual' ? 'Pedido web' : 'Caja' }}</td>
                      <td class="p-3">{{ paymentLabel(sale.payment_method) }}</td>
                      <td class="p-3 text-right">{{ sale.items.length }}</td>
                      <td class="p-3 text-right font-semibold">{{ sale.total_amount }}</td>
                    </tr>
                  } @empty { <tr><td colspan="5" class="p-4 text-slate-500">Sin ventas registradas en esta sucursal.</td></tr> }
                </tbody>
              </table>
            </div>
          }
          @case ('orders') {
            <h2 class="text-sm font-semibold uppercase text-slate-500">Pedidos web para retirar o enviar desde esta sucursal</h2>
            <div class="overflow-x-auto rounded-xl border border-slate-200 bg-white">
              <table class="w-full text-sm">
                <thead class="bg-slate-50 text-left text-xs uppercase text-slate-500"><tr><th class="p-3">Fecha</th><th class="p-3">Entrega</th><th class="p-3">Pago</th><th class="p-3">Estado</th><th class="p-3 text-right">Total</th></tr></thead>
                <tbody>
                  @for (order of orders(); track order.id) {
                    <tr class="border-t border-slate-100">
                      <td class="p-3">{{ order.created_at | date: 'dd/MM/yyyy HH:mm' }}</td>
                      <td class="p-3">{{ order.fulfillment_type === 'delivery' ? 'Envío a domicilio' : 'Retiro en tienda' }}</td>
                      <td class="p-3">{{ paymentLabel(order.payment_method) }} · {{ order.payment_status === 'paid' ? 'pagado' : order.payment_status === 'pending' ? 'pendiente' : 'fallido' }}</td>
                      <td class="p-3">{{ order.fulfillment_status }}</td>
                      <td class="p-3 text-right font-semibold">{{ order.total_amount }}</td>
                    </tr>
                  } @empty { <tr><td colspan="5" class="p-4 text-slate-500">Sin pedidos para esta sucursal.</td></tr> }
                </tbody>
              </table>
            </div>
            <h2 class="text-sm font-semibold uppercase text-slate-500">Reservas</h2>
            <div class="overflow-x-auto rounded-xl border border-slate-200 bg-white">
              <table class="w-full text-sm">
                <thead class="bg-slate-50 text-left text-xs uppercase text-slate-500"><tr><th class="p-3">Cliente</th><th class="p-3">Visita</th><th class="p-3">Estado</th><th class="p-3 text-right">Prendas</th><th class="p-3 text-right">Total</th></tr></thead>
                <tbody>
                  @for (reservation of reservations(); track reservation.id) {
                    <tr class="border-t border-slate-100">
                      <td class="p-3">{{ reservation.user_name }}</td>
                      <td class="p-3">{{ reservation.visit_date | date: 'dd/MM/yyyy' }}</td>
                      <td class="p-3">{{ reservation.status }}</td>
                      <td class="p-3 text-right">{{ reservation.item_count }}</td>
                      <td class="p-3 text-right">{{ reservation.total_amount }}</td>
                    </tr>
                  } @empty { <tr><td colspan="5" class="p-4 text-slate-500">Sin reservas en esta sucursal.</td></tr> }
                </tbody>
              </table>
            </div>
          }
          @case ('staff') {
            <div class="overflow-x-auto rounded-xl border border-slate-200 bg-white">
              <table class="w-full text-sm">
                <thead class="bg-slate-50 text-left text-xs uppercase text-slate-500"><tr><th class="p-3">Nombre</th><th class="p-3">Correo</th><th class="p-3">Rol</th><th class="p-3">Estado</th></tr></thead>
                <tbody>
                  @for (person of staff(); track person.id) {
                    <tr class="border-t border-slate-100">
                      <td class="p-3 font-medium text-slate-900">{{ person.name }}</td>
                      <td class="p-3">{{ person.email }}</td>
                      <td class="p-3 capitalize">{{ person.rol }}</td>
                      <td class="p-3">{{ person.is_active ? 'Activo' : 'Inactivo' }}</td>
                    </tr>
                  } @empty { <tr><td colspan="4" class="p-4 text-slate-500">No hay personal asignado a esta sucursal.</td></tr> }
                </tbody>
              </table>
            </div>
          }
          @case ('cash') {
            <div class="flex flex-wrap items-end gap-2">
              <label class="text-xs font-medium uppercase text-slate-500">Día
                <input type="date" class="mt-1 block h-9 rounded-md border border-slate-300 px-2 text-sm" [value]="cashDay()" (change)="setCashDay($any($event.target).value)" />
              </label>
              <p class="pb-2 text-xs text-slate-500">Cajas de los cajeros de esta sucursal únicamente.</p>
            </div>
            <div class="overflow-x-auto rounded-xl border border-slate-200 bg-white">
              <table class="w-full text-sm">
                <thead class="bg-slate-50 text-left text-xs uppercase text-slate-500"><tr><th class="p-3">Cajero</th><th class="p-3">Apertura</th><th class="p-3">Cierre</th><th class="p-3 text-right">Inicial</th><th class="p-3 text-right">Esperado</th><th class="p-3 text-right">Contado</th><th class="p-3 text-right">Diferencia</th><th class="p-3"></th></tr></thead>
                <tbody>
                  @for (drawer of cashSessions(); track drawer.id) {
                    <tr class="border-t border-slate-100">
                      <td class="p-3 font-medium text-slate-900">{{ drawer.cashier_name }}</td>
                      <td class="p-3">{{ drawer.opened_at | date: 'dd/MM HH:mm' }}</td>
                      <td class="p-3">{{ drawer.status === 'open' ? 'Abierta' : (drawer.closed_at | date: 'dd/MM HH:mm') }}</td>
                      <td class="p-3 text-right">{{ drawer.opening_amount }}</td>
                      <td class="p-3 text-right">{{ drawer.expected_amount }}</td>
                      <td class="p-3 text-right">{{ drawer.counted_amount ?? '—' }}</td>
                      <td class="p-3 text-right font-semibold" [class.text-rose-700]="+(drawer.difference ?? 0) < 0" [class.text-emerald-700]="+(drawer.difference ?? 0) > 0">{{ drawer.difference ?? '—' }}</td>
                      <td class="p-3 text-right"><button type="button" class="cursor-pointer text-emerald-700 hover:underline" (click)="toggleDrawer(drawer.id)">{{ openDrawerId() === drawer.id ? 'Ocultar' : 'Detalle' }}</button></td>
                    </tr>
                    @if (openDrawerId() === drawer.id && drawerDetail(); as detail) {
                      <tr class="bg-slate-50"><td colspan="8" class="p-3">
                        <p class="mb-2 text-xs text-slate-600">Ventas efectivo {{ detail.cash_sales }} · QR {{ detail.qr_sales }} · Cobros de pedidos {{ detail.order_collections }} · Ingresos {{ detail.deposits }} · Retiros {{ detail.withdrawals }} · Vuelto entregado {{ detail.change_given }}@if (detail.closing_note) { · Nota: {{ detail.closing_note }} }</p>
                        <ul class="space-y-1 text-xs">
                          @for (m of detail.movements ?? []; track m.id) {
                            <li>{{ m.created_at | date: 'HH:mm' }} · {{ movementLabel(m.type) }} {{ m.method === 'qr' ? '(QR)' : '' }} · {{ m.amount }}@if (m.cash_received) { · recibido {{ m.cash_received }}, cambio {{ m.change_given }} }@if (m.reason) { · {{ m.reason }} }</li>
                          } @empty { <li class="text-slate-500">Sin movimientos.</li> }
                        </ul>
                      </td></tr>
                    }
                  } @empty { <tr><td colspan="8" class="p-4 text-slate-500">No hay cajas para este día en esta sucursal.</td></tr> }
                </tbody>
              </table>
            </div>
          }
        }
      }
    </section>
  `,
})
export class AdminBranchDetailPageComponent {
  private readonly branchApi = inject(AdminBranchService);
  private readonly userApi = inject(AdminUserService);
  private readonly dashboardApi = inject(DashboardApiService);
  private readonly inventoryApi = inject(InventoryApiService);
  private readonly salesApi = inject(SalesApiService);
  private readonly ordersApi = inject(CheckoutApiService);
  private readonly reservationsApi = inject(ReservationApiService);
  private readonly cashApi = inject(CashSessionApiService);

  protected readonly tabs = TABS;
  protected readonly branchId = inject(ActivatedRoute).snapshot.paramMap.get('branchId') ?? '';
  protected readonly activeTab = signal<BranchTab>('summary');
  protected readonly branch = signal<AdminBranch | null>(null);
  protected readonly notFound = signal(false);
  protected readonly summary = signal<DashboardSummary | null>(null);
  protected readonly stock = signal<InventoryBranchStock[]>([]);
  protected readonly sales = signal<Sale[]>([]);
  protected readonly orders = signal<Order[]>([]);
  protected readonly reservations = signal<Reservation[]>([]);
  protected readonly staff = signal<AdminUsuario[]>([]);
  protected readonly cashSessions = signal<CashSession[]>([]);
  protected readonly cashDay = signal(new Date().toLocaleDateString('en-CA', { timeZone: 'America/La_Paz' }));
  protected readonly openDrawerId = signal<string | null>(null);
  protected readonly drawerDetail = signal<CashSession | null>(null);
  protected readonly openDrawers = computed(() => this.cashSessions().filter((s) => s.status === 'open').length);

  constructor() {
    void this.load();
  }

  protected paymentLabel(method: string): string {
    return ({ cash: 'Efectivo', qr: 'QR', stripe: 'Tarjeta' } as Record<string, string>)[method] ?? method;
  }

  protected movementLabel(type: string): string {
    return ({ sale: 'Venta', order: 'Cobro de pedido', deposit: 'Ingreso', withdrawal: 'Retiro' } as Record<string, string>)[type] ?? type;
  }

  protected setCashDay(day: string): void {
    this.cashDay.set(day);
    this.openDrawerId.set(null);
    void this.loadCash();
  }

  protected async toggleDrawer(sessionId: string): Promise<void> {
    if (this.openDrawerId() === sessionId) {
      this.openDrawerId.set(null);
      return;
    }
    try {
      this.drawerDetail.set((await firstValueFrom(this.cashApi.get(sessionId))).data ?? null);
      this.openDrawerId.set(sessionId);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo cargar el detalle de la caja.'));
    }
  }

  private async load(): Promise<void> {
    try {
      const branches = (await firstValueFrom(this.branchApi.listBranches())).data ?? [];
      const branch = branches.find((b) => b.id === this.branchId) ?? null;
      this.branch.set(branch);
      if (!branch) {
        this.notFound.set(true);
        return;
      }
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo cargar la sucursal.'));
      return;
    }
    // Every request carries this branch's id; the backend also checks it belongs to the company.
    const id = this.branchId;
    await Promise.all([
      this.fetch(async () => this.summary.set((await firstValueFrom(this.dashboardApi.getDashboard({ branch_id: id }))).data?.summary ?? null), 'el resumen'),
      this.fetch(async () => this.stock.set((await firstValueFrom(this.inventoryApi.getBranchStock(id))).data ?? []), 'el inventario'),
      this.fetch(async () => this.sales.set((await firstValueFrom(this.salesApi.listBranchSales(id))).data ?? []), 'las ventas'),
      this.fetch(async () => this.orders.set((await firstValueFrom(this.ordersApi.listBranchOrders(id))).data ?? []), 'los pedidos'),
      this.fetch(async () => this.reservations.set((await firstValueFrom(this.reservationsApi.listBranchReservations(id))).data ?? []), 'las reservas'),
      this.fetch(async () => this.staff.set(((await firstValueFrom(this.userApi.listUsuarios())).data ?? []).filter((u) => u.branch_id === id)), 'el personal'),
      this.loadCash(),
    ]);
  }

  private loadCash(): Promise<void> {
    return this.fetch(async () => this.cashSessions.set(
      (await firstValueFrom(this.cashApi.list({ branch_id: this.branchId, day: this.cashDay() }))).data ?? []), 'las cajas');
  }

  /** One failing section must not hide the others. */
  private async fetch(action: () => Promise<void>, what: string): Promise<void> {
    try {
      await action();
    } catch (error) {
      toast.error(getErrorMessage(error, `No se pudo cargar ${what} de la sucursal.`));
    }
  }
}
