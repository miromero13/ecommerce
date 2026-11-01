import { ApiResponse } from '../../../core/models/api.model';

export type DashboardPeriod = 'day' | 'week' | 'month';

export interface DashboardQuery {
  branch_id?: string | null;
  from_date?: string | null;
  to_date?: string | null;
  period?: DashboardPeriod;
}

export interface DashboardSummary {
  total_sales: string;
  total_orders: number;
  total_units_sold: number;
  average_ticket: string;
  total_stock: number;
  total_available_stock: number;
  low_stock_items: number;
  total_reservations: number;
  pending_reservations: number;
  confirmed_reservations: number;
  attended_reservations: number;
  cancelled_reservations: number;
}

export interface DashboardBranchKpi {
  branch_id: string;
  branch_name: string;
  city: string;
  total_sales: string;
  total_orders: number;
  total_units_sold: number;
  total_stock: number;
  total_available_stock: number;
}

export interface DashboardProductKpi {
  product_id: string;
  product_name: string;
  total_units_sold: number;
  total_sales: string;
  total_stock: number;
  total_available_stock: number;
}

export interface DashboardSeriesPoint {
  label: string;
  sales: string;
  orders: number;
  units: number;
}

export interface DashboardMovementPoint {
  label: string;
  income: number;
  outcome: number;
  transfer_in: number;
  transfer_out: number;
}

export interface DashboardBranchMovementPoint {
  branch_id: string;
  branch_name: string;
  income: number;
  outcome: number;
  transfer_in: number;
  transfer_out: number;
}

export interface DashboardInventoryPoint {
  branch_name: string;
  product_name: string;
  variant_sku: string;
  quantity: number;
  reserved_quantity: number;
  available_quantity: number;
  sku?: string;
  available?: number;
  minimum?: number;
}

export interface DashboardComparison {
  sales_delta_pct: number | null;
  orders_delta_pct: number | null;
  units_delta_pct: number | null;
  avg_ticket_delta_pct: number | null;
}

export interface DashboardChannelSplit {
  channel_label: string;
  sales: number | string;
  orders: number;
}

export interface DashboardTopCategory {
  category_name: string;
  units: number;
  sales: number | string;
}

export interface DashboardData {
  filters: DashboardQuery;
  summary: DashboardSummary;
  sales_series: DashboardSeriesPoint[];
  movement_series: DashboardMovementPoint[];
  movement_by_branch: DashboardBranchMovementPoint[];
  branch_kpis: DashboardBranchKpi[];
  top_products: DashboardProductKpi[];
  low_stock: DashboardInventoryPoint[];
  comparison?: DashboardComparison | null;
  channel_split?: DashboardChannelSplit[];
  top_categories?: DashboardTopCategory[];
}

export type DashboardResponse = ApiResponse<DashboardData>;
