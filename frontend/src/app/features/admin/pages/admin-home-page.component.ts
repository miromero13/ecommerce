import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmInputImports } from '../../../components/input/src';
import { HlmSelectImports } from '../../../components/select/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { CatalogBranch } from '../../shared/models/catalog.model';
import { DashboardBranchKpi, DashboardData, DashboardMovementPoint, DashboardPeriod, DashboardProductKpi, DashboardQuery, DashboardSeriesPoint } from '../../shared/models/dashboard.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { DashboardApiService } from '../../shared/services/dashboard-api.service';

@Component({
  selector: 'app-admin-home-page',
  standalone: true,
  imports: [CommonModule, HlmButton, ...HlmBadgeImports, ...HlmCardImports, ...HlmInputImports, ...HlmSelectImports],
  templateUrl: './admin-home-page.component.html',
})
export class AdminHomePageComponent {
  private readonly catalogApi = inject(CatalogApiService);
  private readonly dashboardApi = inject(DashboardApiService);

  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly selectedBranchId = signal('');
  protected readonly fromDate = signal('');
  protected readonly toDate = signal('');
  protected readonly period = signal<DashboardPeriod>('day');
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
    branch_kpis: [],
    top_products: [],
    low_stock: [],
  });

  protected readonly branchLabel = computed(() => {
    const branchId = this.selectedBranchId();
    if (!branchId) return 'Todas';
    return this.branches().find((branch) => branch.id === branchId)?.name ?? branchId;
  });

  protected readonly maxSalesPoint = computed(() => {
    const values = this.dashboard().sales_series.map((point) => Number(point.sales || 0));
    return Math.max(...values, 1);
  });

  protected readonly maxMovementPoint = computed(() => {
    const values = this.dashboard().movement_series.map((point) => point.income + point.outcome + point.transfer_in + point.transfer_out);
    return Math.max(...values, 1);
  });

  protected readonly maxProductSales = computed(() => {
    const values = this.dashboard().top_products.map((product) => Number(product.total_sales || 0));
    return Math.max(...values, 1);
  });

  constructor() {
    void this.loadData();
  }

  protected async refresh(): Promise<void> {
    this.loading.set(true);
    try {
      await this.loadDashboard();
    } finally {
      this.loading.set(false);
    }
  }

  protected async applyFilters(): Promise<void> {
    this.loading.set(true);
    try {
      await this.loadDashboard();
    } finally {
      this.loading.set(false);
    }
  }

  protected onBranchChange(event: Event): void {
    this.selectedBranchId.set((event.target as HTMLSelectElement).value);
  }

  protected onPeriodChange(event: Event): void {
    this.period.set((event.target as HTMLSelectElement).value as DashboardPeriod);
  }

  protected onFromDateChange(event: Event): void {
    this.fromDate.set((event.target as HTMLInputElement).value);
  }

  protected onToDateChange(event: Event): void {
    this.toDate.set((event.target as HTMLInputElement).value);
  }

  protected summaryCards(): Array<{ label: string; value: string | number; tone: string }> {
    const summary = this.dashboard().summary;
    return [
      { label: 'Ventas', value: summary.total_sales, tone: 'text-emerald-600' },
      { label: 'Órdenes', value: summary.total_orders, tone: 'text-sky-600' },
      { label: 'Unidades', value: summary.total_units_sold, tone: 'text-violet-600' },
      { label: 'Ticket promedio', value: summary.average_ticket, tone: 'text-amber-600' },
      { label: 'Stock total', value: summary.total_stock, tone: 'text-slate-900' },
      { label: 'Disponible', value: summary.total_available_stock, tone: 'text-slate-900' },
      { label: 'Bajo stock', value: summary.low_stock_items, tone: 'text-rose-600' },
      { label: 'Reservas', value: summary.total_reservations, tone: 'text-cyan-600' },
    ];
  }

  protected progressWidth(value: number, max: number): string {
    return `${Math.min((value / max) * 100, 100)}%`;
  }

  protected salesPointWidth(point: DashboardSeriesPoint): string {
    return this.progressWidth(Number(point.sales || 0), this.maxSalesPoint());
  }

  protected productWidth(product: DashboardProductKpi): string {
    return this.progressWidth(Number(product.total_sales || 0), this.maxProductSales());
  }

  protected movementTotal(point: DashboardMovementPoint): number {
    return point.income + point.outcome + point.transfer_in + point.transfer_out;
  }

  protected branchSalesLabel(branch: DashboardBranchKpi): string {
    return `${branch.total_sales} · ${branch.total_orders} órdenes`;
  }

  private async loadData(): Promise<void> {
    this.loading.set(true);
    try {
      const branchesResponse = await firstValueFrom(this.catalogApi.listPublicBranches());
      this.branches.set(branchesResponse.data ?? []);

      if (!this.selectedBranchId()) {
        const defaultBranch = this.branches().find((branch) => branch.is_default) ?? this.branches()[0] ?? null;
        this.selectedBranchId.set(defaultBranch?.id ?? '');
      }

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
