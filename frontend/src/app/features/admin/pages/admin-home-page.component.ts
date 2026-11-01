import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { toast } from '@spartan-ng/brain/sonner';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideBrainCircuit, lucideUsers } from '@ng-icons/lucide';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmInputImports } from '../../../components/input/src';
import { HlmSelectImports } from '../../../components/select/src';
import { OnBrowserDirective } from '@spartan-ng/helm/utils';
import { AreaChartComponent, BarChartComponent, DonutChartComponent } from 'angular-chrts';
import type { BulletLegendItemInterface } from '@unovis/ts';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { CatalogBranch } from '../../shared/models/catalog.model';
import { DashboardData, DashboardPeriod, DashboardQuery } from '../../shared/models/dashboard.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { DashboardApiService } from '../../shared/services/dashboard-api.service';
import { VoiceInputButtonComponent } from '../../shared/components/voice-input-button.component';
import { AdminBranchService } from '../services/admin-branch.service';

function localDate(offsetDays: number): string {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

type MovementTab = 'income' | 'outcome' | 'transfers';

@Component({
  selector: 'app-admin-home-page',
  standalone: true,
  imports: [CommonModule, RouterLink, NgIcon, HlmButton, OnBrowserDirective, AreaChartComponent, BarChartComponent, DonutChartComponent, VoiceInputButtonComponent, ...HlmBadgeImports, ...HlmCardImports, ...HlmInputImports, ...HlmSelectImports],
  providers: [provideIcons({ lucideBrainCircuit, lucideUsers })],
  templateUrl: './admin-home-page.component.html',
})
export class AdminHomePageComponent {
  private readonly catalogApi = inject(CatalogApiService);
  private readonly dashboardApi = inject(DashboardApiService);
  private readonly branchApi = inject(AdminBranchService);
  private readonly router = inject(Router);

  protected readonly quickQuestion = signal('');
  protected readonly quickExamples = [
    'top 10 productos más vendidos de los últimos 3 meses por sucursal',
    'ventas por categoría del último mes',
    'ventas online vs tienda de esta semana',
  ];

  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly selectedBranchId = signal('');
  // Últimos 30 días por defecto para que la comparación con el período anterior esté disponible
  protected readonly fromDate = signal(localDate(-29));
  protected readonly toDate = signal(localDate(0));
  protected readonly period = signal<DashboardPeriod>('day');
  protected readonly branchSelectLabel = (branchId: string | null | undefined): string => {
    if (!branchId) return 'Todas las sucursales';
    const branch = this.branches().find((item) => item.id === branchId);
    return branch ? `${branch.name} - ${branch.city}` : branchId;
  };
  protected readonly periodSelectLabel = (period: DashboardPeriod | null | undefined): string => ({ day: 'Día', week: 'Semana', month: 'Mes' }[period ?? 'day']);
  protected readonly activeMovementTab = signal<MovementTab>('income');
  protected readonly movementTabs: Array<{ key: MovementTab; label: string }> = [
    { key: 'income', label: 'Entradas' },
    { key: 'outcome', label: 'Salidas' },
    { key: 'transfers', label: 'Traspasos' },
  ];
  protected readonly loading = signal(false);
  protected readonly dashboard = signal<DashboardData>({
    filters: {},
    summary: {
      total_sales: '0.00',
      total_orders: 0,
      total_units_sold: 0,
      average_ticket: '0.00',
      total_stock: 0,
      total_available_stock: 0,
      low_stock_items: 0,
      total_reservations: 0,
      pending_reservations: 0,
      confirmed_reservations: 0,
      attended_reservations: 0,
      cancelled_reservations: 0,
    },
    sales_series: [],
    movement_series: [],
    movement_by_branch: [],
    branch_kpis: [],
    top_products: [],
    low_stock: [],
  });

  protected readonly branchLabel = computed(() => {
    const branchId = this.selectedBranchId();
    if (!branchId) return 'Todas';
    return this.branches().find((branch) => branch.id === branchId)?.name ?? branchId;
  });

  protected readonly salesCategories: Record<string, BulletLegendItemInterface> = { sales: { name: 'Ventas', color: '#10b981' } };
  protected readonly salesChartData = computed(() => this.dashboard().sales_series.map((point) => ({ ...point, sales: Number(point.sales || 0) })));
  protected readonly topProductsChartData = computed(() => this.dashboard().top_products.map((product) => ({ label: product.product_name, sales: Number(product.total_sales || 0) })));
  protected readonly branchPerformanceChartData = computed(() => this.dashboard().branch_kpis.map((branch) => ({ label: branch.branch_name, sales: Number(branch.total_sales || 0) })));
  protected readonly movementDistribution = computed(() => {
    const totals = new Map<string, { name: string; value: number }>();
    for (const point of this.dashboard().movement_by_branch) {
      const tab = this.activeMovementTab();
      const rawValue = tab === 'transfers' ? Number(point.transfer_in || 0) + Number(point.transfer_out || 0) : Number(point[tab] || 0);
      const value = Number.isFinite(rawValue) ? Math.max(rawValue, 0) : 0;
      const key = point.branch_id || point.branch_name;
      if (!key || value === 0) continue;
      const current = totals.get(key);
      if (current) current.value += value;
      else totals.set(key, { name: point.branch_name || key, value });
    }
    return [...totals.entries()].map(([key, item]) => ({ key, ...item }));
  });
  protected readonly channelDistribution = computed(() => (this.dashboard().channel_split ?? []).map((c) => ({ name: c.channel_label, value: Number(c.sales || 0) })).filter((c) => c.value > 0));
  protected readonly channelDonutData = computed(() => this.channelDistribution().map((c) => c.value));
  protected readonly channelDonutCategories = computed<Record<string, BulletLegendItemInterface>>(() =>
    Object.fromEntries(this.channelDistribution().map((c, index) => [`c${index}`, { name: c.name, color: ['#0ea5e9', '#10b981'][index % 2] }])));
  protected readonly topCategoriesChartData = computed(() => (this.dashboard().top_categories ?? []).map((c) => ({ label: c.category_name, sales: Number(c.sales || 0) })));
  protected readonly lowStockRows = computed(() => this.dashboard().low_stock ?? []);
  protected readonly movementDonutData = computed(() => this.movementDistribution().map((item) => item.value));
  protected readonly movementDonutCategories = computed<Record<string, BulletLegendItemInterface>>(() =>
    Object.fromEntries(this.movementDistribution().map((item, index) => [item.key, { name: item.name, color: ['#10b981', '#f43f5e', '#0ea5e9', '#8b5cf6', '#f59e0b'][index % 5] }])));

  constructor() {
    void this.loadData();
  }

  // [CU13 - Secuencia: Paso 1] El Administrador del tenant ejecuta refresh() en AdminHomePageComponent
  protected async refresh(): Promise<void> {
    this.loading.set(true);
    try {
      await this.loadDashboard();
    } finally {
      this.loading.set(false);
    }
  }

  // [CU13 - Secuencia: Paso 2] El Administrador del tenant ejecuta applyFilters() en AdminHomePageComponent
  protected async applyFilters(): Promise<void> {
    this.loading.set(true);
    try {
      await this.loadDashboard();
    } finally {
      this.loading.set(false);
    }
  }

  protected onBranchChange(value: string | null | undefined): void {
    this.selectedBranchId.set(value ?? '');
  }

  protected setActiveMovementTab(tab: MovementTab): void {
    this.activeMovementTab.set(tab);
  }

  protected onPeriodChange(value: DashboardPeriod | null | undefined): void {
    if (value === 'day' || value === 'week' || value === 'month') this.period.set(value);
  }

  protected onFromDateChange(event: Event): void {
    this.fromDate.set((event.target as HTMLInputElement).value);
  }

  protected onToDateChange(event: Event): void {
    this.toDate.set((event.target as HTMLInputElement).value);
  }

  protected askQuick(text: string = this.quickQuestion()): void {
    const q = text.trim();
    if (!q) return;
    this.quickQuestion.set(q);
    void this.router.navigate(['/app/admin/reports'], { queryParams: { q } });
  }

  protected deltaView(delta: number | null | undefined): { text: string; tone: string; aria: string } | null {
    if (delta === null || delta === undefined || !Number.isFinite(Number(delta))) return null;
    const n = Number(delta);
    const abs = Math.abs(n).toLocaleString('es-BO', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
    if (n > 0) return { text: `▲ ${abs} %`, tone: 'text-emerald-600', aria: `Aumentó ${abs} % frente al período anterior` };
    if (n < 0) return { text: `▼ ${abs} %`, tone: 'text-rose-600', aria: `Disminuyó ${abs} % frente al período anterior` };
    return { text: '0,0 %', tone: 'text-slate-500', aria: 'Sin cambios frente al período anterior' };
  }

  protected summaryCards(): Array<{ label: string; value: string | number; tone: string; delta?: { text: string; tone: string; aria: string } | null }> {
    const summary = this.dashboard().summary;
    const cmp = this.dashboard().comparison;
    return [
      { label: 'Ventas', value: summary.total_sales, tone: 'text-emerald-600', delta: this.deltaView(cmp?.sales_delta_pct) },
      { label: 'Órdenes', value: summary.total_orders, tone: 'text-sky-600', delta: this.deltaView(cmp?.orders_delta_pct) },
      { label: 'Unidades', value: summary.total_units_sold, tone: 'text-violet-600', delta: this.deltaView(cmp?.units_delta_pct) },
      { label: 'Ticket promedio', value: summary.average_ticket, tone: 'text-amber-600', delta: this.deltaView(cmp?.avg_ticket_delta_pct) },
      { label: 'Stock total', value: summary.total_stock, tone: 'text-slate-900' },
      { label: 'Disponible', value: summary.total_available_stock, tone: 'text-slate-900' },
      { label: 'Bajo stock', value: summary.low_stock_items, tone: 'text-rose-600' },
      { label: 'Reservas', value: summary.total_reservations, tone: 'text-cyan-600' },
    ];
  }

  private async loadData(): Promise<void> {
    this.loading.set(true);
    try {
      const branchesResponse = await firstValueFrom(this.branchApi.listBranches());
      this.branches.set((branchesResponse.data ?? []) as unknown as CatalogBranch[]);

      // Por defecto siempre 'Todas las sucursales' ('')
      this.selectedBranchId.set('');

      await this.loadDashboard();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo cargar el dashboard.'));
    } finally {
      this.loading.set(false);
    }
  }

  private async loadDashboard(): Promise<void> {
    try {
      const response = await firstValueFrom(this.dashboardApi.getDashboard(this.filters()));
      this.dashboard.set(response.data ?? this.dashboard());
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo cargar el dashboard.'));
    }
  }

  private filters(): DashboardQuery {
    return {
      branch_id: this.selectedBranchId() || null,
      from_date: this.fromDate() || null,
      to_date: this.toDate() || null,
      period: this.period(),
    };
  }
}
