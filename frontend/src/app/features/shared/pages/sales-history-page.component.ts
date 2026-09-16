import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { toast } from '@spartan-ng/brain/sonner';

import { HlmCardImports } from '../../../components/card/src';
import { HlmButton } from '../../../components/button/src';
import { HlmSelectImports } from '../../../components/select/src';
import { HlmTable } from '../../../components/table/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { CatalogBranch, CatalogProduct } from '../models/catalog.model';
import { Sale } from '../models/sale.model';
import { CatalogApiService } from '../services/catalog-api.service';
import { ReportsApiService } from '../services/reports-api.service';
import { SalesApiService } from '../services/sales-api.service';
import { SessionService } from '../services/session.service';

type ReportFormat = 'pdf' | 'html' | 'csv';
type ReportColumn = { key: string; label: string };

const SALES_REPORT_COLUMNS: ReportColumn[] = [
  { key: 'branch_name', label: 'Sucursal' },
  { key: 'product_name', label: 'Producto' },
  { key: 'variant_sku', label: 'SKU' },
  { key: 'type', label: 'Tipo' },
  { key: 'quantity_sold', label: 'Cantidad' },
  { key: 'gross_sales', label: 'Ventas brutas' },
  { key: 'payment_method', label: 'Método de pago' },
  { key: 'payment_status', label: 'Estado de pago' },
  { key: 'sale_status', label: 'Estado de venta' },
];

@Component({
  selector: 'app-sales-history-page',
  standalone: true,
  imports: [CommonModule, HlmButton, HlmTable, ...HlmCardImports, ...HlmSelectImports],
  templateUrl: './sales-history-page.component.html',
})
export class SalesHistoryPageComponent {
  private readonly salesApi = inject(SalesApiService);
  private readonly catalogApi = inject(CatalogApiService);
  private readonly reportsApi = inject(ReportsApiService);
  private readonly session = inject(SessionService);

  protected readonly sales = signal<Sale[]>([]);
  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly selectedBranchId = signal('');
  protected readonly loading = signal(false);
  protected readonly reportModalOpen = signal(false);
  protected readonly reportFormat = signal<ReportFormat>('pdf');
  protected readonly reportBranchId = signal('');
  protected readonly reportProductId = signal('');
  protected readonly reportFromDate = signal('');
  protected readonly reportToDate = signal('');
  protected readonly reportColumns = signal<string[]>(SALES_REPORT_COLUMNS.map((column) => column.key));
  protected readonly salesReportColumns = SALES_REPORT_COLUMNS;
  protected readonly reportProducts = signal<CatalogProduct[]>([]);
  protected readonly reportLoading = signal(false);
  protected readonly isAdmin = () => this.session.user()?.rol === 'administrador';
  protected readonly branchSelectLabel = (branchId: string | null | undefined): string => {
    if (!branchId) return 'Todas las sucursales';
    return this.branches().find((branch) => branch.id === branchId)?.name ?? branchId;
  };

  constructor() {
    if (this.isAdmin()) void this.loadBranches();
    void this.loadSales();
  }

  protected async loadSales(): Promise<void> {
    this.loading.set(true);
    try {
      const branchId = this.isAdmin() ? this.selectedBranchId() || undefined : undefined;
      const response = await firstValueFrom(this.salesApi.listBranchSales(branchId));
      this.sales.set(response.data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar las ventas.'));
      this.sales.set([]);
    } finally {
      this.loading.set(false);
    }
  }

  protected branchChanged(value: string | null | undefined): void {
    this.selectedBranchId.set(value ?? '');
    void this.loadSales();
  }

  protected readonly reportBranchSelectLabel = (branchId: string | null | undefined): string => {
    if (!branchId) return 'Todas las sucursales';
    return this.branches().find((branch) => branch.id === branchId)?.name ?? branchId;
  };

  protected readonly reportProductSelectLabel = (productId: string | null | undefined): string => {
    if (!productId) return 'Todos los productos';
    return this.reportProducts().find((product) => product.id === productId)?.name ?? productId;
  };

  protected readonly reportFormatSelectLabel = (format: ReportFormat | null | undefined): string => ({
    pdf: 'PDF (imprimir o guardar)', html: 'HTML (abrir documento)', csv: 'CSV (descargar)',
  }[format ?? 'pdf']);

  protected openReportModal(): void {
    this.reportBranchId.set('');
    this.reportProductId.set('');
    this.reportFromDate.set('');
    this.reportToDate.set('');
    this.reportFormat.set('pdf');
    this.reportColumns.set(SALES_REPORT_COLUMNS.map((column) => column.key));
    this.reportModalOpen.set(true);
    void this.loadReportProducts();
  }

  protected closeReportModal(): void { this.reportModalOpen.set(false); }
  protected setReportBranch(value: string | null | undefined): void { this.reportBranchId.set(value ?? ''); }
  protected setReportProduct(value: string | null | undefined): void { this.reportProductId.set(value ?? ''); }
  protected setReportFormat(value: ReportFormat | null | undefined): void {
    if (value === 'pdf' || value === 'html' || value === 'csv') this.reportFormat.set(value);
  }
  protected setReportFromDate(event: Event): void { this.reportFromDate.set((event.target as HTMLInputElement).value); }
  protected setReportToDate(event: Event): void { this.reportToDate.set((event.target as HTMLInputElement).value); }
  protected isReportColumnSelected(key: string): boolean { return this.reportColumns().includes(key); }
  protected toggleReportColumn(key: string, selected: boolean): void {
    this.reportColumns.update((columns) => selected ? [...columns, key] : columns.filter((column) => column !== key));
  }

  protected async generateReport(): Promise<void> {
    const fromDate = this.reportFromDate();
    const toDate = this.reportToDate();
    if (fromDate && toDate && fromDate > toDate) {
      toast.error('La fecha desde no puede ser posterior a la fecha hasta.');
      return;
    }
    if (!this.reportColumns().length) {
      toast.error('Selecciona al menos una columna para exportar.');
      return;
    }

    this.reportLoading.set(true);
    try {
      const response = await firstValueFrom(this.reportsApi.getSalesReport({
        branch_id: this.reportBranchId() || null,
        product_id: this.reportProductId() || null,
        from_date: fromDate || null,
        to_date: toDate || null,
      }));
      const columns = SALES_REPORT_COLUMNS.filter((column) => this.reportColumns().includes(column.key));
      const rows = (response.data?.rows ?? []) as unknown as Array<Record<string, unknown>>;
      const html = this.reportDocumentHtml(columns, rows);
      if (this.reportFormat() === 'csv') this.downloadReportCsv(columns, rows);
      else this.openReportDocument(html, this.reportFormat() === 'pdf');
      this.closeReportModal();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo generar el reporte.'));
    } finally {
      this.reportLoading.set(false);
    }
  }

  protected itemSummary(sale: Sale): string {
    return sale.items.map((item) => `${item.quantity} × ${item.product_name}`).join(', ');
  }

  protected paymentLabel(method: Sale['payment_method']): string {
    return method === 'stripe' ? 'Tarjeta' : 'Efectivo';
  }

  private async loadBranches(): Promise<void> {
    try {
      const response = await firstValueFrom(this.catalogApi.listPublicBranches());
      this.branches.set(response.data ?? []);
    } catch {
      this.branches.set([]);
    }
  }

  private async loadReportProducts(): Promise<void> {
    try {
      const response = await firstValueFrom(this.catalogApi.listAdminProducts());
      this.reportProducts.set(response.data ?? []);
    } catch {
      this.reportProducts.set([]);
    }
  }

  private reportDocumentHtml(columns: ReportColumn[], rows: Array<Record<string, unknown>>): string {
    const header = columns.map((column) => `<th>${this.escapeHtml(column.label)}</th>`).join('');
    const body = rows.map((row) => `<tr>${columns.map((column) => `<td>${this.escapeHtml(this.reportCellValue(row[column.key]))}</td>`).join('')}</tr>`).join('');
    return `<!doctype html><html><head><meta charset="utf-8"><title>Reporte de ventas</title><style>body{font:14px Arial,sans-serif;color:#172033;padding:24px}h1{font-size:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #cbd5e1;padding:8px;text-align:left}th{background:#e2e8f0}@media print{body{padding:0}}</style></head><body><h1>Reporte de ventas</h1><p>Generado: ${new Date().toLocaleString('es-BO')}</p><table><thead><tr>${header}</tr></thead><tbody>${body || `<tr><td colspan="${columns.length}">No hay datos para los filtros seleccionados.</td></tr>`}</tbody></table></body></html>`;
  }

  private downloadReportCsv(columns: ReportColumn[], rows: Array<Record<string, unknown>>): void {
    const csv = [columns.map((column) => this.csvCell(column.label)), ...rows.map((row) => columns.map((column) => this.csvCell(this.reportCellValue(row[column.key]))))]
      .map((line) => line.join(',')).join('\r\n');
    const url = URL.createObjectURL(new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'sales-report.csv';
    link.click();
    URL.revokeObjectURL(url);
  }

  private openReportDocument(html: string, print: boolean): void {
    const reportWindow = window.open('', '_blank');
    if (!reportWindow) {
      toast.error('El navegador bloqueó la ventana del reporte. Permite las ventanas emergentes e inténtalo de nuevo.');
      return;
    }
    reportWindow.document.write(html);
    reportWindow.document.close();
    if (print) reportWindow.setTimeout(() => reportWindow.print(), 250);
  }

  private reportCellValue(value: unknown): string { return value === null || value === undefined ? '' : String(value); }
  private csvCell(value: string): string { return `"${value.replaceAll('"', '""')}"`; }
  private escapeHtml(value: string): string {
    return value.replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character] ?? character);
  }
}
