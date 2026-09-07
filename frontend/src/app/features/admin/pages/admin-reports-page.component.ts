import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Observable, firstValueFrom } from 'rxjs';

import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmInputImports } from '../../../components/input/src';
import { HlmTable } from '../../../components/table/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { requestWithToast } from '../../../core/utils/request-toast.util';
import { CatalogBranch, CatalogProduct } from '../../shared/models/catalog.model';
import { InventoryReportRow, MovementReportRow, ReportPayload, ReportQuery, ReportResponse, ReportType, SalesReportRow } from '../../shared/models/report.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { ReportsApiService } from '../../shared/services/reports-api.service';

type ReportState = ReportPayload<SalesReportRow | InventoryReportRow | MovementReportRow>;

@Component({
  selector: 'app-admin-reports-page',
  standalone: true,
  imports: [CommonModule, RouterLink, HlmButton, HlmTable, ...HlmBadgeImports, ...HlmCardImports, ...HlmInputImports],
  templateUrl: './admin-reports-page.component.html',
})
export class AdminReportsPageComponent {
  private readonly catalogApi = inject(CatalogApiService);
  private readonly reportsApi = inject(ReportsApiService);

  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly products = signal<CatalogProduct[]>([]);
  protected readonly loading = signal(false);
  protected readonly exporting = signal(false);
  protected readonly selectedReport = signal<ReportType>('sales');
  protected readonly selectedBranchId = signal('');
  protected readonly selectedProductId = signal('');
  protected readonly fromDate = signal('');
  protected readonly toDate = signal('');
  protected readonly searchTerm = signal('');
  protected readonly reportState = signal<ReportState>({ summary: {}, rows: [] });

  protected readonly branchLabel = computed(() => {
    const branchId = this.selectedBranchId();
    if (!branchId) return 'Todas';
    return this.branches().find((branch) => branch.id === branchId)?.name ?? branchId;
  });

  protected readonly productLabel = computed(() => {
    const productId = this.selectedProductId();
    if (!productId) return 'Todos';
    return this.products().find((product) => product.id === productId)?.name ?? productId;
  });

  protected readonly columnCount = computed(() => 6);

  constructor() {
    void this.loadData();
  }

  protected async refresh(): Promise<void> {
    await this.loadReport();
  }

  protected async selectReport(report: ReportType): Promise<void> {
    this.selectedReport.set(report);
    await this.loadReport();
  }

  protected async exportCsv(): Promise<void> {
    this.exporting.set(true);
    try {
      const blob = await requestWithToast(
        this.reportsApi.exportReport(this.selectedReport(), this.filters()),
        { loading: 'Exportando reporte...', success: 'Reporte exportado.', error: 'No se pudo exportar el reporte.' },
      );
      this.downloadBlob(blob, `${this.selectedReport()}-report.csv`);
    } catch {
      // toast handled by requestWithToast
    } finally {
      this.exporting.set(false);
    }
  }

  protected async applyFilters(): Promise<void> {
    await this.loadReport();
  }

  protected onBranchChange(event: Event): void {
    this.selectedBranchId.set((event.target as HTMLSelectElement).value);
  }

  protected onProductChange(event: Event): void {
    this.selectedProductId.set((event.target as HTMLSelectElement).value);
  }

  protected onFromDateChange(event: Event): void {
    this.fromDate.set((event.target as HTMLInputElement).value);
  }

  protected onToDateChange(event: Event): void {
    this.toDate.set((event.target as HTMLInputElement).value);
  }

  protected onSearchChange(event: Event): void {
    this.searchTerm.set((event.target as HTMLInputElement).value);
  }

  protected reportTitle(): string {
    switch (this.selectedReport()) {
      case 'inventory': return 'Inventario';
      case 'movements': return 'Movimientos';
      default: return 'Ventas';
    }
  }

  protected summaryEntries(): Array<{ label: string; value: string | number }> {
    const summary = this.reportState().summary;
    if (this.selectedReport() === 'inventory') {
      return [
        { label: 'Líneas', value: summary['total_lines'] ?? 0 },
        { label: 'Stock', value: summary['total_stock'] ?? 0 },
        { label: 'Reservado', value: summary['total_reserved'] ?? 0 },
        { label: 'Disponible', value: summary['total_available'] ?? 0 },
      ];
    }
    if (this.selectedReport() === 'movements') {
      return [
        { label: 'Líneas', value: summary['total_lines'] ?? 0 },
        { label: 'Unidades movidas', value: summary['total_units_moved'] ?? 0 },
      ];
    }
    return [
      { label: 'Órdenes', value: summary['total_orders'] ?? 0 },
      { label: 'Ventas', value: summary['total_sales'] ?? '0.00' },
      { label: 'Unidades', value: summary['total_units'] ?? 0 },
      { label: 'Ticket promedio', value: summary['average_ticket'] ?? '0.00' },
    ];
  }

  protected isSalesRow(row: SalesReportRow | InventoryReportRow | MovementReportRow): row is SalesReportRow {
    return this.selectedReport() === 'sales';
  }

  protected isInventoryRow(row: SalesReportRow | InventoryReportRow | MovementReportRow): row is InventoryReportRow {
    return this.selectedReport() === 'inventory';
  }

  protected isMovementRow(row: SalesReportRow | InventoryReportRow | MovementReportRow): row is MovementReportRow {
    return this.selectedReport() === 'movements';
  }

  protected movementLabel(type: MovementReportRow['movement_type']): string {
    switch (type) {
      case 'income': return 'Ingreso';
      case 'outcome': return 'Salida';
      case 'transfer_in': return 'Traspaso entrada';
      case 'transfer_out': return 'Traspaso salida';
      default: return type;
    }
  }

  protected movementClass(type: MovementReportRow['movement_type']): string {
    switch (type) {
      case 'income': return 'bg-emerald-100 text-emerald-700';
      case 'outcome': return 'bg-rose-100 text-rose-700';
      case 'transfer_in': return 'bg-sky-100 text-sky-700';
      case 'transfer_out': return 'bg-amber-100 text-amber-700';
      default: return 'bg-slate-100 text-slate-700';
    }
  }

  protected async loadData(): Promise<void> {
    this.loading.set(true);
    try {
      const [branchesResponse, productsResponse] = await Promise.all([
        firstValueFrom(this.catalogApi.listPublicBranches()),
        firstValueFrom(this.catalogApi.listProducts()),
      ]);
      this.branches.set(branchesResponse.data ?? []);
      this.products.set(productsResponse.data ?? []);
      await this.loadReport();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar los reportes.'));
      this.reportState.set({ summary: {}, rows: [] });
    } finally {
      this.loading.set(false);
    }
  }

  private async loadReport(): Promise<void> {
    this.loading.set(true);
    try {
      const response = await firstValueFrom(this.reportObservable());
      const payload: ReportState = response.data ?? { summary: {}, rows: [] };
      this.reportState.set(payload);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo cargar el reporte.'));
      this.reportState.set({ summary: {}, rows: [] });
    } finally {
      this.loading.set(false);
    }
  }

  private reportObservable(): Observable<ReportResponse> {
    const filters = this.filters();
    switch (this.selectedReport()) {
      case 'inventory':
        return this.reportsApi.getInventoryReport(filters);
      case 'movements':
        return this.reportsApi.getMovementsReport(filters);
      default:
        return this.reportsApi.getSalesReport(filters);
    }
  }

  private filters(): ReportQuery {
    return {
      branch_id: this.selectedBranchId() || null,
      product_id: this.selectedProductId() || null,
      from_date: this.fromDate() || null,
      to_date: this.toDate() || null,
      q: this.searchTerm() || null,
    };
  }

  private downloadBlob(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    window.URL.revokeObjectURL(url);
  }
}
