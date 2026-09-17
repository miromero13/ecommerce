import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { toast } from '@spartan-ng/brain/sonner';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideMic, lucideSquare } from '@ng-icons/lucide';

import { HlmCardImports } from '../../../components/card/src';
import { HlmButton } from '../../../components/button/src';
import { HlmSelectImports } from '../../../components/select/src';
import { HlmTable } from '../../../components/table/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { downloadSimplePdf } from '../../../core/utils/simple-pdf.util';
import { CatalogBranch, CatalogProduct } from '../models/catalog.model';
import { Sale } from '../models/sale.model';
import { CatalogApiService } from '../services/catalog-api.service';
import { ReportsApiService } from '../services/reports-api.service';
import { SalesApiService } from '../services/sales-api.service';
import { SessionService } from '../services/session.service';

type ReportFormat = 'pdf' | 'html' | 'csv';
type ReportColumn = { key: string; label: string };

interface SpeechRecognitionResultLike { [index: number]: { transcript: string }; }
interface SpeechRecognitionEventLike extends Event { results: { [index: number]: SpeechRecognitionResultLike }; }
interface SpeechRecognitionLike {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}
interface SpeechRecognitionWindow extends Window {
  SpeechRecognition?: new () => SpeechRecognitionLike;
  webkitSpeechRecognition?: new () => SpeechRecognitionLike;
}

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
  imports: [CommonModule, NgIcon, HlmButton, HlmTable, ...HlmCardImports, ...HlmSelectImports],
  providers: [provideIcons({ lucideMic, lucideSquare })],
  templateUrl: './sales-history-page.component.html',
})
export class SalesHistoryPageComponent {
  private readonly salesApi = inject(SalesApiService);
  private readonly catalogApi = inject(CatalogApiService);
  private readonly reportsApi = inject(ReportsApiService);
  private readonly session = inject(SessionService);
  private speechRecognition: SpeechRecognitionLike | null = null;

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
  protected readonly naturalQuery = signal('');
  protected readonly listening = signal(false);
  protected readonly isAdmin = () => this.session.user()?.rol === 'administrador';
  protected readonly isManager = () => this.session.user()?.rol === 'encargado';
  protected readonly branchSelectLabel = (branchId: string | null | undefined): string => {
    if (!branchId) return 'Todas las sucursales';
    return this.branches().find((branch) => branch.id === branchId)?.name ?? branchId;
  };

  constructor() {
    if (this.isAdmin() || this.isManager()) void this.loadBranches();
    if (this.isManager()) this.selectedBranchId.set(this.session.user()?.branch_id ?? '');
    void this.loadSales();
  }

  protected async loadSales(): Promise<void> {
    this.loading.set(true);
    try {
      const branchId = this.isAdmin() || this.isManager() ? this.selectedBranchId() || undefined : undefined;
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
    pdf: 'PDF (descarga directa)', html: 'HTML (abrir documento)', csv: 'CSV (descargar)',
  }[format ?? 'pdf']);

  protected openReportModal(): void {
    this.reportBranchId.set(this.isManager() ? this.selectedBranchId() : '');
    this.reportProductId.set('');
    this.reportFromDate.set('');
    this.reportToDate.set('');
    this.reportFormat.set('pdf');
    this.reportColumns.set(SALES_REPORT_COLUMNS.map((column) => column.key));
    this.reportModalOpen.set(true);
    void this.loadReportProducts();
  }

  protected closeReportModal(): void {
    this.speechRecognition?.stop();
    this.reportModalOpen.set(false);
  }
  protected setNaturalQuery(event: Event): void { this.naturalQuery.set((event.target as HTMLTextAreaElement).value); }
  protected setReportBranch(value: string | null | undefined): void {
    if (this.isAdmin()) this.reportBranchId.set(value ?? '');
  }
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
      const rows = this.resolveReportBranchNames((response.data?.rows ?? []) as unknown as Array<Record<string, unknown>>);
      const html = this.reportDocumentHtml(columns, rows);
      if (this.reportFormat() === 'csv') this.downloadReportCsv(columns, rows);
      else if (this.reportFormat() === 'pdf') this.downloadReportPdf(columns, rows);
      else this.downloadHtmlReport(html);
      this.closeReportModal();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo generar el reporte.'));
    } finally {
      this.reportLoading.set(false);
    }
  }

  protected startListening(): void {
    if (this.listening()) {
      this.speechRecognition?.stop();
      return;
    }
    const speechWindow = window as SpeechRecognitionWindow;
    const SpeechRecognition = speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      toast.error('El reconocimiento de voz no está disponible en este navegador.');
      return;
    }
    const recognition = new SpeechRecognition();
    this.speechRecognition = recognition;
    recognition.lang = 'es-BO';
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onresult = (event) => this.naturalQuery.set(event.results[0][0].transcript);
    recognition.onerror = () => toast.error('No se pudo reconocer la voz. Puedes escribir la solicitud.');
    recognition.onend = () => this.listening.set(false);
    this.listening.set(true);
    try { recognition.start(); } catch { this.listening.set(false); }
  }

  protected async generateNaturalReport(): Promise<void> {
    const query = this.naturalQuery().trim();
    if (!query) {
      toast.error('Escribe o dicta una solicitud de reporte.');
      return;
    }
    this.reportLoading.set(true);
    try {
      const response = await firstValueFrom(this.reportsApi.queryNaturalLanguage(query));
      const data = response.data;
      if (!data || data.report_type !== 'sales') {
        toast.error('Esta pantalla solo puede generar reportes de ventas.');
        return;
      }
      const filters = data.filters;
      this.reportBranchId.set(filters.branch_id ?? '');
      this.reportProductId.set(filters.product_id ?? '');
      this.reportFromDate.set(filters.from_date ?? '');
      this.reportToDate.set(filters.to_date ?? '');
      this.reportFormat.set(data.format === 'html' || data.format === 'csv' ? data.format : 'pdf');
      const requestedColumns = data.columns ?? [];
      const selectedColumns = requestedColumns.length
        ? SALES_REPORT_COLUMNS.filter((column) => requestedColumns.includes(column.key))
        : SALES_REPORT_COLUMNS;
      const columns = selectedColumns.length ? selectedColumns : SALES_REPORT_COLUMNS;
      this.reportColumns.set(columns.map((column) => column.key));
      const rows = this.resolveReportBranchNames((data.report.rows ?? []) as unknown as Array<Record<string, unknown>>);
      const html = this.reportDocumentHtml(columns, rows);
      if (this.reportFormat() === 'csv') this.downloadReportCsv(columns, rows);
      else if (this.reportFormat() === 'html') this.downloadHtmlReport(html);
      else this.downloadReportPdf(columns, rows);
      this.closeReportModal();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo interpretar el reporte.'));
    } finally {
      this.reportLoading.set(false);
    }
  }

  protected itemSummary(sale: Sale): string {
    return sale.items.map((item) => `${item.quantity} × ${item.product_name}`).join(', ');
  }

  protected paymentLabel(method: Sale['payment_method']): string { return this.translateValue(method, { cash: 'Efectivo', stripe: 'Tarjeta' }); }
  protected paymentStatusLabel(status: Sale['payment_status']): string { return this.translateValue(status, { paid: 'Pagado', pending: 'Pendiente', failed: 'Fallido', refunded: 'Reembolsado' }); }
  protected saleStatusLabel(status: Sale['status']): string { return this.translateValue(status, { completed: 'Completada', pending: 'Pendiente', cancelled: 'Cancelada' }); }
  protected saleTypeLabel(type: Sale['type']): string { return this.translateValue(type, { in_person: 'Presencial', online: 'Online', 'venta presencial': 'Presencial', 'venta virtual': 'Online' }); }
  protected saleBranchName(sale: Sale): string { return this.branchName(sale.branch_id ?? sale.branch_name, sale.branch_name); }

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
    const body = rows.map((row) => `<tr>${columns.map((column) => `<td>${this.escapeHtml(this.reportCellValue(row[column.key], column.key))}</td>`).join('')}</tr>`).join('');
    const filters = this.reportFilterRows();
    const filterHtml = filters.map(([label, value]) => `<dt>${this.escapeHtml(label)}</dt><dd>${this.escapeHtml(value)}</dd>`).join('');
    return `<!doctype html><html><head><meta charset="utf-8"><title>Reporte de ventas</title><style>body{font:14px Arial,sans-serif;color:#172033;padding:24px}h1{font-size:20px}dl{display:grid;grid-template-columns:max-content 1fr;gap:6px 12px;margin:18px 0}dt{font-weight:700}dd{margin:0}table{border-collapse:collapse;width:100%}th,td{border:1px solid #cbd5e1;padding:8px;text-align:left}th{background:#e2e8f0}@media print{body{padding:0}}</style></head><body><h1>Reporte de ventas</h1><p>Generado: ${this.escapeHtml(new Date().toLocaleString('es-BO'))}</p><section><h2>Filtros aplicados</h2><dl>${filterHtml}</dl></section><table><thead><tr>${header}</tr></thead><tbody>${body || `<tr><td colspan="${columns.length}">No hay datos para los filtros seleccionados.</td></tr>`}</tbody></table></body></html>`;
  }

  private downloadReportCsv(columns: ReportColumn[], rows: Array<Record<string, unknown>>): void {
    const filterRows = this.reportFilterRows().map(([label, value]) => [this.csvCell(label), this.csvCell(value)]);
    const csv = [...filterRows, [], columns.map((column) => this.csvCell(column.label)), ...rows.map((row) => columns.map((column) => this.csvCell(this.reportCellValue(row[column.key], column.key))))]
      .map((line) => line.join(',')).join('\r\n');
    const url = URL.createObjectURL(new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'sales-report.csv';
    link.click();
    URL.revokeObjectURL(url);
  }

  private downloadHtmlReport(html: string): void {
    try {
      const url = URL.createObjectURL(new Blob([html], { type: 'text/html;charset=utf-8' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = 'sales-report.html';
      link.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 0);
    } catch {
      toast.error('El navegador bloqueó la descarga del reporte. Inténtalo de nuevo.');
    }
  }

  private downloadReportPdf(columns: ReportColumn[], rows: Array<Record<string, unknown>>): void {
    downloadSimplePdf({
      filename: 'sales-report.pdf',
      title: 'Reporte de ventas',
      generatedAt: new Date().toLocaleString('es-BO'),
      filters: this.reportFilterRows(),
      columns: columns.map((column) => column.label),
      rows: rows.map((row) => columns.map((column) => this.reportCellValue(row[column.key], column.key))),
    });
  }

  private reportCellValue(value: unknown, key?: string): string {
    if (value === null || value === undefined) return '';
    if (typeof value !== 'string') return String(value);
    if (key === 'payment_method') return this.paymentLabel(value as Sale['payment_method']);
    if (key === 'payment_status') return this.paymentStatusLabel(value as Sale['payment_status']);
    if (key === 'sale_status') return this.saleStatusLabel(value as Sale['status']);
    if (key === 'type') return this.saleTypeLabel(value as Sale['type']);
    return value;
  }
  private reportFilterRows(): string[][] {
    return [
      ['Filtros aplicados', ''],
      ['Sucursal', this.reportBranchSelectLabel(this.reportBranchId())],
      ['Producto', this.reportProductSelectLabel(this.reportProductId())],
      ['Desde', this.reportFromDate() || 'Sin límite'],
      ['Hasta', this.reportToDate() || 'Sin límite'],
    ];
  }
  private branchName(branchId: string | null | undefined, fallback = ''): string {
    if (!branchId) return fallback || 'Sin sucursal';
    return this.branches().find((branch) => branch.id === branchId)?.name ?? (fallback || branchId);
  }
  private resolveReportBranchNames(rows: Array<Record<string, unknown>>): Array<Record<string, unknown>> {
    return rows.map((row) => {
      const branchName = String(row['branch_name'] ?? '');
      const branchId = String(row['branch_id'] || branchName || this.reportBranchId() || '');
      return { ...row, branch_name: this.branchName(branchId, branchName) };
    });
  }
  private translateValue(value: string, translations: Record<string, string>): string { return translations[value] ?? this.humanize(value); }
  private humanize(value: string): string { return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase()); }
  private csvCell(value: string): string { return `"${value.replaceAll('"', '""')}"`; }
  private escapeHtml(value: string): string {
    return value.replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character] ?? character);
  }

}
