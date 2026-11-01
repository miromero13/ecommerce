import { ApiResponse } from '../../../core/models/api.model';
import { PaymentMethodEnum, PaymentStatusEnum } from './order.model';

export type ReportType = 'sales' | 'inventory' | 'movements';
export type SmartReportType = ReportType | 'top_products' | 'branch_comparison' | 'critical_inventory';

export interface SmartReportPayload {
  summary: Record<string, unknown>;
  rows: Array<Record<string, unknown>>;
}
export type SmartReportResponse = ApiResponse<SmartReportPayload>;

export interface ReportDataSource {
  mode: 'real' | 'mixed' | 'synthetic';
  real_samples: number;
  synthetic_samples: number;
  notice: string;
}

export interface DemandForecastRequest {
  use_synthetic_data?: boolean;
  branch_id?: string;
  target_period_weeks: number;
}

export interface DemandForecast {
  model_type: string;
  evaluation_metrics: { r2_score: number; mse: number; test_samples: number };
  forecast: Array<{ week: string | number; week_start?: string | null; predicted_units: number; confidence_lower: number; confidence_upper: number }>;
  data_source: ReportDataSource;
  recent_weekly_average?: number | null;
  products?: Array<{ product_id: string; product_name: string; predicted_units: number; available_stock: number; suggested_restock: number }>;
}

export interface CustomerClusters {
  model_type: string;
  clusters_count: 3;
  evaluation_metrics: { silhouette_score: number };
  segments: Array<{
    cluster_id: number; name: string; size: number; avg_spend: number; real_customers: number; synthetic_customers: number;
    avg_recency_days?: number; avg_orders?: number; recommendation?: string; top_customers?: string[];
  }>;
  data_source: ReportDataSource;
}


export interface ReportQuery {
  branch_id?: string | null;
  product_id?: string | null;
  variant_id?: string | null;
  from_date?: string | null;
  to_date?: string | null;
  q?: string | null;
}

export interface ReportSummary {
  total_orders?: number;
  total_sales?: string;
  total_units?: number;
  average_ticket?: string;
  total_lines?: number;
  total_stock?: number;
  total_reserved?: number;
  total_available?: number;
  total_units_moved?: number;
}

export interface SalesReportRow {
  branch_id: string;
  branch_name: string;
  type: 'venta presencial' | 'venta virtual';
  product_id: string;
  product_name: string;
  variant_id: string;
  variant_sku: string;
  quantity_sold: number;
  gross_sales: string;
  payment_method?: PaymentMethodEnum | null;
  payment_status?: PaymentStatusEnum | null;
  sale_status?: string | null;
}

export interface InventoryReportRow {
  branch_id: string;
  branch_name: string;
  product_id: string;
  product_name: string;
  variant_id: string;
  variant_sku: string;
  quantity: number;
  reserved_quantity: number;
  available_quantity: number;
}

export interface MovementReportRow {
  branch_id: string;
  branch_name: string;
  product_id: string;
  product_name: string;
  variant_id: string;
  variant_sku: string;
  movement_type: 'income' | 'outcome' | 'transfer_in' | 'transfer_out';
  quantity: number;
  movements_count: number;
}

export interface ReportPayload<T> {
  summary: ReportSummary;
  rows: T[];
}

export type SalesReportResponse = ApiResponse<ReportPayload<SalesReportRow>>;
export type InventoryReportResponse = ApiResponse<ReportPayload<InventoryReportRow>>;
export type MovementsReportResponse = ApiResponse<ReportPayload<MovementReportRow>>;
export type ReportResponse = SalesReportResponse | InventoryReportResponse | MovementsReportResponse;

export type ReportKind = 'sales' | 'inventory' | 'critical_stock' | 'movements';
export type AnalyticsMetric = 'units' | 'revenue' | 'orders' | 'avg_ticket' | 'customers';
export type AnalyticsDimension = 'product' | 'variant' | 'category' | 'branch' | 'size' | 'color' | 'channel' | 'payment_method' | 'customer' | 'day' | 'week' | 'month';
export type AnalyticsPreset = 'today' | 'yesterday' | 'this_week' | 'last_week' | 'last_n_days' | 'this_month' | 'last_month' | 'last_n_months' | 'this_quarter' | 'last_quarter' | 'this_year' | 'last_year' | 'custom';
export type AnalyticsPayment = 'cash' | 'card' | 'qr' | 'wallet';
export type AnalyticsChart = 'bar' | 'line' | 'donut' | 'table';

export interface AnalyticsQuery {
  kind: ReportKind;
  metric: AnalyticsMetric;
  group_by: AnalyticsDimension[];
  top_n: number | null;
  order: 'desc' | 'asc';
  period: { preset: AnalyticsPreset; n: number | null; from_date: string | null; to_date: string | null };
  branch_ids: string[];
  product_ids: string[];
  category_ids: string[];
  channel: 'all' | 'store' | 'online';
  payment_methods: AnalyticsPayment[];
  compare_previous: boolean;
  chart: AnalyticsChart | null;
}

export interface AnalyticsColumn { key: string; label: string; type: 'text' | 'number' | 'money' }
export interface AnalyticsTotals {
  units?: number; revenue?: number | string; orders?: number; avg_ticket?: number | string; customers?: number; items?: number;
}

export interface AnalyticsResult {
  title: string;
  period: { from_date: string; to_date: string; label: string };
  columns: AnalyticsColumn[];
  rows: Array<Record<string, string | number | null>>;
  totals: AnalyticsTotals;
  previous_totals: AnalyticsTotals | null;
  delta_pct: Partial<Record<'units' | 'revenue' | 'orders' | 'avg_ticket' | 'customers', number | null>> | null;
  chart: AnalyticsChart;
  message: string | null;
}

export interface AnalyticsInterpretation { spec: AnalyticsQuery; interpretation: string; interpreted_by?: 'local' | 'groq'; warnings?: string[] }
