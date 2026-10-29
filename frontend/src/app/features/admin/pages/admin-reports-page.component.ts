import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, OnDestroy, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { toast } from '@spartan-ng/brain/sonner';
import { OnBrowserDirective } from '@spartan-ng/helm/utils';
import { BarChartComponent } from 'angular-chrts';

import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmInputImports } from '../../../components/input/src';
import { HlmTable } from '../../../components/table/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { CustomerClusters, DemandForecast, ReportQuery, SmartReportPayload, SmartReportType } from '../../shared/models/report.model';
import { ReportsApiService } from '../../shared/services/reports-api.service';
import { AdminBranch } from '../models/admin-branch.model';
import { AdminBranchService } from '../services/admin-branch.service';

interface SpeechRecognitionEventLike extends Event {
  results: { [index: number]: { [index: number]: { transcript: string } } };
}
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

const LABELS: Record<string, string> = {
  branch_name: 'Sucursal', product_name: 'Producto', variant_sku: 'SKU', type: 'Tipo',
  quantity_sold: 'Unidades vendidas', gross_sales: 'Ventas brutas', total_sales: 'Ventas totales',
  total_orders: 'Operaciones', total_units: 'Unidades', total_units_sold: 'Unidades vendidas',
  average_ticket: 'Ticket promedio', total_lines: 'Líneas', total_stock: 'Stock total',
  total_reserved: 'Stock reservado', total_available: 'Stock disponible', total_units_moved: 'Unidades movidas',
  quantity: 'Cantidad', reserved_quantity: 'Reservado', available_quantity: 'Disponible',
  minimum_stock: 'Stock mínimo', shortage: 'Faltante', deficit: 'Déficit',
  movement_type: 'Movimiento', movements_count: 'Movimientos', payment_method: 'Método de pago',
  payment_status: 'Estado de pago', sale_status: 'Estado de venta', rank: 'Posición',
  low_stock_items: 'Productos con stock bajo', critical_items: 'Productos críticos',
  total_products: 'Productos', total_branches: 'Sucursales', branches_count: 'Sucursales',
};
const VALUES: Record<string, string> = {
  cash: 'Efectivo', stripe: 'Tarjeta', qr: 'QR', paid: 'Pagado', pending: 'Pendiente',
  failed: 'Fallido', refunded: 'Reembolsado', completed: 'Completada', cancelled: 'Cancelada',
  income: 'Entrada', outcome: 'Salida', transfer_in: 'Traspaso recibido', transfer_out: 'Traspaso enviado',
};

@Component({
  selector: 'app-admin-reports-page',
  standalone: true,
  imports: [CommonModule, FormsModule, HlmButton, HlmTable, OnBrowserDirective, BarChartComponent, ...HlmCardImports, ...HlmInputImports],
  templateUrl: './admin-reports-page.component.html',
})
export class AdminReportsPageComponent implements OnDestroy {
  private readonly api = inject(ReportsApiService);
  private readonly branchApi = inject(AdminBranchService);
  private speechRecognition: SpeechRecognitionLike | null = null;

  protected readonly tabs = [
    { key: 'reports', label: 'Lenguaje natural y reportes' },
    { key: 'demand', label: 'Predicción de demanda' },
    { key: 'clusters', label: 'Segmentación' },
  ];
  protected readonly tab = signal('reports');
  protected readonly branches = signal<AdminBranch[]>([]);
  protected readonly loading = signal(false);
  protected readonly exporting = signal(false);
  protected readonly listening = signal(false);
  protected readonly error = signal('');
  protected readonly report = signal<SmartReportPayload | null>(null);
  protected readonly currentQuery = signal<{ type: SmartReportType; filters: ReportQuery } | null>(null);
  protected readonly forecast = signal<DemandForecast | null>(null);
  protected readonly clusters = signal<CustomerClusters | null>(null);
  protected readonly interpretation = signal('');
  private readonly requestedColumns = signal<string[] | null>(null);
  protected readonly reportTypes: Array<{ key: SmartReportType; label: string }> = [
    { key: 'sales', label: 'Ventas por sucursal' },
    { key: 'top_products', label: 'Top 10 productos' },
    { key: 'critical_inventory', label: 'Inventario crítico' },
    { key: 'branch_comparison', label: 'Comparativa de sucursales' },
  ];
  protected reportType: SmartReportType = 'sales';
  protected branchId = '';
  protected fromDate = '';
  protected toDate = '';
  protected naturalQuery = '';
  protected weeks = 4;

  // Only presentation columns: internal identifiers never become table columns.
  protected readonly columns = computed(() => {
    const keys = new Set((this.report()?.rows ?? []).flatMap((row) => Object.keys(row)));
    const selected = this.requestedColumns();
    const candidates = selected?.length ? [...new Set(selected)] : Object.keys(LABELS);
    return candidates.filter((key) => Object.hasOwn(LABELS, key) && keys.has(key))
      .map((key) => ({ key, label: LABELS[key] }));
  });
  protected readonly summary = computed(() => Object.entries(this.report()?.summary ?? {})
    .filter(([key]) => !!LABELS[key]).map(([key, value]) => ({ label: LABELS[key], value })));
  protected readonly forecastChart = computed(() => (this.forecast()?.forecast ?? []).map((point) => ({ label: String(point.week), units: point.predicted_units })));
  protected readonly clustersChart = computed(() => (this.clusters()?.segments ?? []).map((segment) => ({ label: segment.name, customers: segment.size })));
  protected readonly demandCategories = { units: { name: 'Unidades previstas', color: '#10b981' } };
  protected readonly clusterCategories = { customers: { name: 'Clientes simulados', color: '#8b5cf6' } };

  constructor() { void this.loadBranches(); }

  ngOnDestroy(): void {
    if (!this.speechRecognition) return;
    this.speechRecognition.onresult = null;
    this.speechRecognition.onerror = null;
    this.speechRecognition.onend = null;
    this.speechRecognition.stop();
  }

  protected async generateReport(natural = false): Promise<void> {
    if (this.loading()) return;
    if (natural && !this.naturalQuery.trim()) {
      this.error.set('Escribe o dicta una solicitud de reporte.');
      return;
    }
    if (!natural && this.fromDate && this.toDate && this.fromDate > this.toDate) {
      this.error.set('La fecha desde no puede ser posterior a la fecha hasta.');
      return;
    }
    this.loading.set(true);
    this.error.set('');
    this.report.set(null);
    this.currentQuery.set(null);
    this.interpretation.set('');
    this.requestedColumns.set(null);
    try {
      if (natural) {
        const { data, message } = await firstValueFrom(this.api.queryNaturalLanguage(this.naturalQuery.trim()));
        if (!data) throw new Error('Respuesta vacía');
        this.report.set(data.report as unknown as SmartReportPayload);
        this.currentQuery.set({ type: data.report_type, filters: { ...data.filters } });
        this.interpretation.set(data.interpretation);
        this.requestedColumns.set(data.columns ?? null);
        toast.success(message);
      } else {
        const filters: ReportQuery = { branch_id: this.branchId || null, from_date: this.fromDate || null, to_date: this.toDate || null };
        const type = this.reportType;
        const { data, message } = await firstValueFrom(this.api.getSmartReport(type, filters));
        if (!data) throw new Error('Respuesta vacía');
        this.report.set(data);
        this.currentQuery.set({ type, filters });
        toast.success(message);
      }
    } catch (error) {
      this.error.set(getErrorMessage(error, 'No se pudo generar el reporte.'));
    } finally { this.loading.set(false); }
  }

  // CU8: models train on the company's real sales/customers (completed with synthetic data when
  // there are too few); demo mode trains on synthetic data only.
  protected readonly demoMode = signal(false);

  protected async predictDemand(): Promise<void> {
    if (this.loading()) return;
    if (!Number.isInteger(this.weeks) || this.weeks < 1 || this.weeks > 12) {
      this.error.set('Selecciona entre 1 y 12 semanas.');
      return;
    }
    this.loading.set(true);
    this.error.set('');
    this.forecast.set(null);
    try {
      const { data, message } = await firstValueFrom(this.api.predictDemand({ target_period_weeks: this.weeks, use_synthetic_data: this.demoMode() }));
      if (!data) throw new Error('Respuesta vacía');
      this.forecast.set(data);
      toast.success(message);
    } catch (error) { this.error.set(getErrorMessage(error, 'No se pudo predecir la demanda.')); }
    finally { this.loading.set(false); }
  }

  protected async segmentCustomers(): Promise<void> {
    if (this.loading()) return;
    this.loading.set(true);
    this.error.set('');
    this.clusters.set(null);
    try {
      const { data, message } = await firstValueFrom(this.api.customerClusters(this.demoMode()));
      if (!data) throw new Error('Respuesta vacía');
      this.clusters.set(data);
      toast.success(message);
    } catch (error) { this.error.set(getErrorMessage(error, 'No se pudo segmentar a los clientes.')); }
    finally { this.loading.set(false); }
  }

  protected async exportReport(format: 'excel' | 'pdf'): Promise<void> {
    const query = this.currentQuery();
    if (!query || this.exporting() || typeof document === 'undefined') return;
    this.exporting.set(true);
    try {
      const blob = await firstValueFrom(format === 'excel'
        ? this.api.exportExcel(query.type, query.filters) : this.api.exportPdf(query.type, query.filters));
      const url = URL.createObjectURL(blob);
      try {
        const link = document.createElement('a');
        link.href = url;
        link.download = `reporte-${query.type}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
        link.click();
      } finally { window.setTimeout(() => URL.revokeObjectURL(url), 0); }
    } catch (error) {
      // Blob errors must be decoded to preserve plan/permission messages from the API.
      const body = (error as { error?: unknown })?.error;
      let decoded = error;
      if (body instanceof Blob) {
        try { decoded = new HttpErrorResponse({ error: JSON.parse(await body.text()) }); } catch { /* Use the HTTP fallback. */ }
      }
      this.error.set(getErrorMessage(decoded, 'No se pudo exportar el reporte.'));
    } finally { this.exporting.set(false); }
  }

  protected startListening(): void {
    if (this.listening()) { this.speechRecognition?.stop(); return; }
    const speechWindow = typeof window === 'undefined' ? undefined : window as SpeechRecognitionWindow;
    const Recognition = speechWindow?.SpeechRecognition ?? speechWindow?.webkitSpeechRecognition;
    if (!Recognition) { toast.error('El reconocimiento de voz no está disponible en este navegador.'); return; }
    const recognition = new Recognition();
    this.speechRecognition = recognition;
    recognition.lang = 'es-BO';
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onresult = (event) => { this.naturalQuery = event.results[0][0].transcript; };
    recognition.onerror = () => { this.listening.set(false); toast.error('No se pudo reconocer la voz. Puedes escribir la solicitud.'); };
    recognition.onend = () => this.listening.set(false);
    try { recognition.start(); this.listening.set(true); }
    catch { this.listening.set(false); toast.error('No se pudo iniciar el micrófono. Puedes escribir la solicitud.'); }
  }

  protected cell(value: unknown): string {
    if (value === null || value === undefined) return '—';
    return VALUES[String(value)] ?? String(value);
  }

  private async loadBranches(): Promise<void> {
    try {
      const { data } = await firstValueFrom(this.branchApi.listBranches());
      this.branches.set(data ?? []);
    } catch (error) { this.error.set(getErrorMessage(error, 'No se pudieron cargar las sucursales.')); }
  }
}
