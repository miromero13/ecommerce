import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { toast } from '@spartan-ng/brain/sonner';
import { OnBrowserDirective } from '@spartan-ng/helm/utils';
import { BarChartComponent, DonutChartComponent, LineChartComponent } from 'angular-chrts';

import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmInputImports } from '../../../components/input/src';
import { HlmTable } from '../../../components/table/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { VoiceInputButtonComponent } from '../../shared/components/voice-input-button.component';
import {
  AnalyticsColumn, AnalyticsDimension, AnalyticsMetric, AnalyticsPayment, AnalyticsPreset, AnalyticsQuery, AnalyticsResult,
  CustomerClusters, DemandForecast, ReportKind, ReportQuery, SmartReportPayload, SmartReportType,
} from '../../shared/models/report.model';
import { REPORT_EXAMPLES, QUICK_EXAMPLES, kindSummary, specForKind } from './analytics-kind.util';
import { ReportsApiService } from '../../shared/services/reports-api.service';
import { AdminBranch } from '../models/admin-branch.model';
import { AdminBranchService } from '../services/admin-branch.service';

const KINDS: Array<{ key: ReportKind; label: string }> = [
  { key: 'sales', label: 'Ventas' }, { key: 'inventory', label: 'Inventario' },
  { key: 'critical_stock', label: 'Stock crítico' }, { key: 'movements', label: 'Movimientos de inventario' },
];
const PAYMENTS: Array<{ key: AnalyticsPayment; label: string }> = [
  { key: 'cash', label: 'Efectivo' }, { key: 'card', label: 'Tarjeta' }, { key: 'qr', label: 'QR' }, { key: 'wallet', label: 'Billetera' },
];
const HELP_KEY = 'reports-help-closed';
const METRICS: Array<{ key: AnalyticsMetric; label: string }> = [
  { key: 'units', label: 'Unidades' }, { key: 'revenue', label: 'Ingresos' },
  { key: 'orders', label: 'Pedidos' }, { key: 'avg_ticket', label: 'Ticket promedio' },
  { key: 'customers', label: 'Clientes distintos' },
];
const DIMENSIONS: Array<{ key: AnalyticsDimension; label: string }> = [
  { key: 'product', label: 'Producto' }, { key: 'variant', label: 'Variante' }, { key: 'category', label: 'Categoría' },
  { key: 'branch', label: 'Sucursal' }, { key: 'size', label: 'Talla' }, { key: 'color', label: 'Color' },
  { key: 'channel', label: 'Canal' }, { key: 'payment_method', label: 'Método de pago' }, { key: 'customer', label: 'Cliente' },
  { key: 'day', label: 'Día' }, { key: 'week', label: 'Semana' }, { key: 'month', label: 'Mes' },
];
const PRESETS: Array<{ key: AnalyticsPreset; label: string }> = [
  { key: 'today', label: 'Hoy' }, { key: 'yesterday', label: 'Ayer' }, { key: 'this_week', label: 'Esta semana' }, { key: 'last_week', label: 'Semana pasada' },
  { key: 'last_n_days', label: 'Últimos N días' }, { key: 'this_month', label: 'Este mes' }, { key: 'last_month', label: 'Mes pasado' },
  { key: 'last_n_months', label: 'Últimos N meses' }, { key: 'this_quarter', label: 'Este trimestre' },
  { key: 'last_quarter', label: 'Trimestre pasado' }, { key: 'this_year', label: 'Este año' }, { key: 'last_year', label: 'Año pasado' }, { key: 'custom', label: 'Rango personalizado' },
];
const CHART_COLORS = ['#10b981', '#8b5cf6', '#0ea5e9', '#f59e0b', '#f43f5e', '#14b8a6', '#6366f1', '#84cc16', '#ec4899', '#64748b'];
const MAX_CHART_ROWS = 20;

export interface AnalyticsSection { label: string | null; rows: Array<Record<string, string | number | null>>; subtotal: Record<string, number> | null }

// Groups rows by the first text column when the result has two dimensions; subtotals sum counts and money (never averages).
export function groupAnalyticsRows(columns: AnalyticsColumn[], rows: Array<Record<string, string | number | null>>): AnalyticsSection[] {
  const text = columns.filter((column) => column.type === 'text');
  if (text.length < 2) return [{ label: null, rows, subtotal: null }];
  const sections: AnalyticsSection[] = [];
  for (const row of rows) {
    const label = String(row[text[0].key] ?? '—');
    let section = sections.find((item) => item.label === label);
    if (!section) { section = { label, rows: [], subtotal: {} }; sections.push(section); }
    section.rows.push(row);
    for (const column of columns) {
      if (column.type === 'text' || column.key === 'avg_ticket') continue;
      section.subtotal![column.key] = (section.subtotal![column.key] ?? 0) + Number(row[column.key] ?? 0);
    }
  }
  return sections;
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
  imports: [CommonModule, FormsModule, HlmButton, HlmTable, OnBrowserDirective, BarChartComponent, DonutChartComponent, LineChartComponent, VoiceInputButtonComponent, ...HlmCardImports, ...HlmInputImports],
  templateUrl: './admin-reports-page.component.html',
})
export class AdminReportsPageComponent {
  private readonly api = inject(ReportsApiService);
  private readonly branchApi = inject(AdminBranchService);
  private readonly route = inject(ActivatedRoute);
  private runId = 0;

  protected readonly tabs = [
    { key: 'reports', label: 'Lenguaje natural y reportes' },
    { key: 'demand', label: 'Predicción de demanda' },
    { key: 'clusters', label: 'Segmentación' },
  ];
  protected readonly tab = signal('reports');
  protected readonly branches = signal<AdminBranch[]>([]);
  protected readonly loading = signal(false);
  protected readonly exporting = signal(false);
  protected readonly error = signal('');
  protected readonly report = signal<SmartReportPayload | null>(null);
  protected readonly currentQuery = signal<{ type: SmartReportType; filters: ReportQuery } | null>(null);
  protected readonly forecast = signal<DemandForecast | null>(null);
  protected readonly clusters = signal<CustomerClusters | null>(null);
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
  protected weeks = 4;

  // CU08: consulta analítica (interpretar una vez, luego editar los chips sin volver a interpretar).
  protected readonly quickExamples = QUICK_EXAMPLES;
  protected readonly exampleGroups = REPORT_EXAMPLES;
  protected readonly kinds = KINDS;
  protected readonly payments = PAYMENTS;
  protected readonly voiceTips = [
    'Habla natural, con frases completas.',
    'Puedes decir el período, la sucursal y cómo agrupar: «ventas por sucursal de la semana pasada».',
    'Si no te entiende, repite con otras palabras o usa un ejemplo.',
  ];
  protected readonly helpOpen = signal(this.readHelpOpen());
  protected readonly warnings = signal<string[]>([]);
  protected readonly suggestions = signal<string[]>([]);
  private suggestionOffset = 0;
  protected readonly metrics = METRICS;
  protected readonly dimensions = DIMENSIONS;
  protected readonly presets = PRESETS;
  protected question = '';
  protected readonly asking = signal(false);
  protected readonly running = signal(false);
  protected readonly exportingAnalytics = signal(false);
  protected readonly analyticsError = signal('');
  protected readonly interpretationText = signal('');
  protected readonly interpretedBy = signal<'local' | 'groq'>('local');
  protected readonly spec = signal<AnalyticsQuery | null>(null);
  protected readonly result = signal<AnalyticsResult | null>(null);
  private readonly resultMetric = signal<AnalyticsMetric>('units');
  private readonly resultKind = signal<ReportKind>('sales');

  protected readonly sections = computed(() => {
    const result = this.result();
    return result ? groupAnalyticsRows(result.columns, result.rows) : [];
  });
  protected readonly cards = computed(() => {
    const result = this.result();
    if (!result) return [];
    if (this.resultKind() !== 'sales') return [];
    const { totals, delta_pct } = result;
    const cards = [
      { label: 'Unidades', value: this.format(totals.units, 'number'), delta: delta_pct?.units ?? null },
      { label: 'Ingresos Bs.', value: this.format(totals.revenue, 'money'), delta: delta_pct?.revenue ?? null },
      { label: 'Pedidos', value: this.format(totals.orders, 'number'), delta: delta_pct?.orders ?? null },
      { label: 'Ticket promedio', value: this.format(totals.avg_ticket, 'money'), delta: delta_pct?.avg_ticket ?? null },
    ];
    if (totals.customers !== null && totals.customers !== undefined) cards.push({ label: 'Clientes distintos', value: this.format(totals.customers, 'number'), delta: delta_pct?.customers ?? null });
    return cards;
  });
  protected readonly kindLine = computed(() => {
    const result = this.result();
    const kind = this.resultKind();
    return result && kind !== 'sales' ? kindSummary(kind, result.totals).map((item) => `${item.label}: ${this.format(item.value, 'number')}`).join(' · ') : '';
  });
  // With two dimensions the chart only stays readable up to MAX_CHART_ROWS rows (one bar per combination).
  protected readonly chart = computed(() => {
    const result = this.result();
    if (!result || result.chart === 'table' || !result.rows.length) return null;
    const textColumns = result.columns.filter((column) => column.type === 'text');
    if (textColumns.length > 1 && result.rows.length > MAX_CHART_ROWS) return null;
    const metric = result.columns.find((column) => column.key === this.resultMetric()) ?? result.columns.find((column) => column.type !== 'text');
    if (!metric) return null;
    const labels = result.rows.map((row) => textColumns.map((column) => String(row[column.key] ?? '—')).join(' · '));
    const values = result.rows.map((row) => Number(row[metric.key] ?? 0));
    return {
      kind: result.chart,
      labels,
      values,
      data: labels.map((label, index) => ({ label, value: values[index] })),
      categories: { value: { name: metric.label, color: CHART_COLORS[0] } },
      donutCategories: Object.fromEntries(labels.map((label, index) => ['c' + index, { name: label, color: CHART_COLORS[index % CHART_COLORS.length] }])),
    };
  });
  protected readonly xLabel = (tick: number | Date): string => this.chart()?.labels[Math.round(Number(tick))] ?? '';

  // Only presentation columns: internal identifiers never become table columns.
  protected readonly columns = computed(() => {
    const keys = new Set((this.report()?.rows ?? []).flatMap((row) => Object.keys(row)));
    return Object.keys(LABELS).filter((key) => Object.hasOwn(LABELS, key) && keys.has(key))
      .map((key) => ({ key, label: LABELS[key] }));
  });
  protected readonly summary = computed(() => Object.entries(this.report()?.summary ?? {})
    .filter(([key]) => !!LABELS[key]).map(([key, value]) => ({ label: LABELS[key], value })));
  protected readonly forecastChart = computed(() => (this.forecast()?.forecast ?? []).map((point) => ({ label: String(point.week), units: point.predicted_units })));
  protected readonly clustersChart = computed(() => (this.clusters()?.segments ?? []).map((segment) => ({ label: segment.name, customers: segment.size })));
  protected readonly demandCategories = { units: { name: 'Unidades previstas', color: '#10b981' } };
  protected readonly clusterCategories = { customers: { name: 'Clientes simulados', color: '#8b5cf6' } };

  constructor() {
    void this.loadBranches();
    const q = this.route.snapshot.queryParamMap.get('q')?.trim();
    if (q) { this.question = q; void this.ask(); }
  }

  // Reporte descriptivo manual (tipo, sucursal y fechas).
  protected async generateReport(): Promise<void> {
    if (this.loading()) return;
    if (this.fromDate && this.toDate && this.fromDate > this.toDate) {
      this.error.set('La fecha desde no puede ser posterior a la fecha hasta.');
      return;
    }
    this.loading.set(true);
    this.error.set('');
    this.report.set(null);
    this.currentQuery.set(null);
    try {
      const filters: ReportQuery = { branch_id: this.branchId || null, from_date: this.fromDate || null, to_date: this.toDate || null };
      const type = this.reportType;
      const { data, message } = await firstValueFrom(this.api.getSmartReport(type, filters));
      if (!data) throw new Error('Respuesta vacía');
      this.report.set(data);
      this.currentQuery.set({ type, filters });
      toast.success(message);
    } catch (error) {
      this.error.set(getErrorMessage(error, 'No se pudo generar el reporte.'));
    } finally { this.loading.set(false); }
  }

  // [CU08 - Secuencia: Paso 1] El Administrador del tenant ejecuta ask() en AdminReportsPageComponent
  protected async ask(): Promise<void> {
    const query = this.question.trim();
    if (!query) { this.analyticsError.set('Escribe o dicta una consulta.'); return; }
    if (this.asking() || this.running()) return;
    this.asking.set(true);
    this.analyticsError.set('');
    this.result.set(null);
    this.spec.set(null);
    this.interpretationText.set('');
    this.interpretedBy.set('local');
    this.warnings.set([]);
    this.suggestions.set([]);
    try {
      const { data } = await firstValueFrom(this.api.interpret(query));
      if (!data) throw new Error('Respuesta vacía');
      this.spec.set(data.spec);
      this.interpretationText.set(data.interpretation);
      this.interpretedBy.set(data.interpreted_by ?? 'local');
      this.warnings.set(data.warnings ?? []);
    } catch (error) {
      this.fail(error, 'No se pudo interpretar la consulta.');
      if ((error as { status?: number })?.status === 422) this.suggestions.set(this.nextSuggestions());
      return;
    }
    finally { this.asking.set(false); }
    await this.run();
  }

  protected async run(): Promise<void> {
    const spec = this.spec();
    if (!spec) return;
    if (spec.period.preset === 'custom' && !(spec.period.from_date && spec.period.to_date)) return; // wait for both dates
    const id = ++this.runId; // ignores stale responses when chips change quickly
    this.running.set(true);
    this.analyticsError.set('');
    try {
      const { data } = await firstValueFrom(this.api.runAnalytics(spec));
      if (id !== this.runId) return;
      if (!data) throw new Error('Respuesta vacía');
      this.result.set(data);
      this.resultMetric.set(spec.metric);
      this.resultKind.set(spec.kind ?? 'sales');
    } catch (error) { if (id === this.runId) { this.result.set(null); this.fail(error, 'No se pudo generar el reporte.'); } }
    finally { if (id === this.runId) this.running.set(false); }
  }

  protected useExample(text: string): void { this.question = text; void this.ask(); }

  protected patch(changes: Partial<AnalyticsQuery>): void {
    this.spec.update((spec) => spec && { ...spec, ...changes });
    void this.run();
  }

  protected setPreset(preset: AnalyticsPreset): void {
    const period = this.spec()?.period;
    if (!period) return;
    const n = preset === 'last_n_days' ? (period.n ?? 30) : preset === 'last_n_months' ? (period.n ?? 3) : null;
    this.patch({ period: { preset, n, from_date: preset === 'custom' ? period.from_date : null, to_date: preset === 'custom' ? period.to_date : null } });
  }

  protected setPeriod(changes: Partial<AnalyticsQuery['period']>): void {
    const period = this.spec()?.period;
    if (!period) return;
    const next = { ...period, ...changes };
    if (next.n != null) next.n = Math.min(36, Math.max(1, Math.trunc(next.n)));
    if (next.preset === 'custom' && next.from_date && next.to_date && next.from_date > next.to_date) {
      this.analyticsError.set('La fecha desde no puede ser posterior a la fecha hasta.');
      return;
    }
    this.patch({ period: next });
  }

  protected setGroup(index: 0 | 1, value: string): void {
    const current = this.spec()?.group_by ?? [];
    const picked = [index === 0 ? value : current[0], index === 1 ? value : current[1]].filter((item): item is AnalyticsDimension => !!item);
    this.patch({ group_by: [...new Set(picked)] });
  }

  protected setTopN(value: string): void {
    const n = Math.trunc(Number(value));
    this.patch({ top_n: value.trim() && n >= 1 ? Math.min(n, 50) : null });
  }

  // Changing the report type re-runs the analysis without interpreting again.
  protected setKind(kind: ReportKind): void {
    this.spec.update((spec) => spec && specForKind(spec, kind));
    void this.run();
  }

  protected togglePayment(method: AnalyticsPayment, checked: boolean): void {
    const current = this.spec()?.payment_methods ?? [];
    this.patch({ payment_methods: checked ? [...new Set([...current, method])] : current.filter((item) => item !== method) });
  }

  protected toggleHelp(): void {
    const open = !this.helpOpen();
    this.helpOpen.set(open);
    try { localStorage.setItem(HELP_KEY, open ? '' : '1'); } catch { /* Storage may be unavailable. */ }
  }

  private readHelpOpen(): boolean {
    try { return localStorage.getItem(HELP_KEY) !== '1'; } catch { return true; }
  }

  // Rotates through the catalogue so repeated failures offer different examples.
  private nextSuggestions(): string[] {
    const all = REPORT_EXAMPLES.flatMap((group) => group.items);
    const picked = Array.from({ length: 4 }, (_, i) => all[(this.suggestionOffset + i) % all.length]);
    this.suggestionOffset = (this.suggestionOffset + 4) % all.length;
    return picked;
  }

  protected setBranch(id: string): void { this.patch({ branch_ids: id ? [id] : [] }); }

  protected presetUsesN(): boolean {
    const preset = this.spec()?.period.preset;
    return preset === 'last_n_days' || preset === 'last_n_months';
  }

  // [CU08 - Secuencia: Paso 2] El Administrador del tenant ejecuta exportAnalytics(format) en AdminReportsPageComponent
  protected async exportAnalytics(format: 'pdf' | 'excel'): Promise<void> {
    const spec = this.spec();
    if (!spec || this.exportingAnalytics() || typeof document === 'undefined') return;
    this.exportingAnalytics.set(true);
    try {
      const response = await firstValueFrom(this.api.exportAnalytics(spec, format));
      if (!response.body) throw new Error('Respuesta vacía');
      const disposition = response.headers.get('Content-Disposition') ?? '';
      const filename = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposition)?.[1] ?? 'reporte.' + (format === 'excel' ? 'xlsx' : 'pdf');
      const url = URL.createObjectURL(response.body);
      try {
        const link = document.createElement('a');
        link.href = url;
        link.download = decodeURIComponent(filename);
        link.click();
      } finally { window.setTimeout(() => URL.revokeObjectURL(url), 0); }
    } catch (error) {
      // Blob errors must be decoded to preserve plan/permission messages from the API.
      const body = (error as { error?: unknown })?.error;
      let decoded = error;
      if (body instanceof Blob) {
        try { decoded = new HttpErrorResponse({ error: JSON.parse(await body.text()) }); } catch { /* Use the HTTP fallback. */ }
      }
      this.fail(decoded, 'No se pudo exportar el reporte.');
    } finally { this.exportingAnalytics.set(false); }
  }

  protected format(value: unknown, type: AnalyticsColumn['type']): string {
    if (value === null || value === undefined || value === '') return '—';
    if (type === 'text') return String(value);
    const digits = type === 'money' ? 2 : 0;
    return Number(value).toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });
  }

  private fail(error: unknown, fallback: string): void {
    const message = getErrorMessage(error, fallback);
    this.analyticsError.set(message);
    toast.error(message);
  }

  // CU8: models train on the company's real sales/customers (completed with synthetic data when
  // there are too few); demo mode trains on synthetic data only.
  protected readonly demoMode = signal(false);

  // [CU08 - Secuencia: Paso 3] El Administrador del tenant ejecuta predictDemand() en AdminReportsPageComponent
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

  // [CU08 - Secuencia: Paso 4] El Administrador del tenant ejecuta segmentCustomers() en AdminReportsPageComponent
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
