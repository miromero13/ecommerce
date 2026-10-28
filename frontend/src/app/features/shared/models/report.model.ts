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
  forecast: Array<{ week: string | number; predicted_units: number; confidence_lower: number; confidence_upper: number }>;
  data_source: ReportDataSource;
}

export interface CustomerClusters {
  model_type: string;
  clusters_count: 3;
  evaluation_metrics: { silhouette_score: number };
  segments: Array<{ cluster_id: number; name: string; size: number; avg_spend: number; real_customers: number; synthetic_customers: number }>;
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

export interface NaturalReportPayload {
  report_type: SmartReportType;
  format: 'pdf' | 'html' | 'csv';
  columns?: string[];
  filters: ReportQuery;
  interpretation: string;
  report: ReportPayload<SalesReportRow> | ReportPayload<InventoryReportRow> | ReportPayload<MovementReportRow> | SmartReportPayload;
}

export type NaturalReportResponse = ApiResponse<NaturalReportPayload>;
