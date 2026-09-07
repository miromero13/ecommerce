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

export interface DashboardInventoryPoint {
  branch_name: string;
  product_name: string;
  variant_sku: string;
  quantity: number;
  reserved_quantity: number;
  available_quantity: number;
}

export interface DashboardData {
  filters: DashboardQuery;
  summary: DashboardSummary;
  sales_series: DashboardSeriesPoint[];
  movement_series: DashboardMovementPoint[];
  branch_kpis: DashboardBranchKpi[];
  top_products: DashboardProductKpi[];
  low_stock: DashboardInventoryPoint[];
}

export type DashboardResponse = ApiResponse<DashboardData>;
