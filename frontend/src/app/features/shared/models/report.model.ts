import { ApiResponse } from '../../../core/models/api.model';
import { PaymentMethodEnum, PaymentStatusEnum } from './order.model';

export type ReportType = 'sales' | 'inventory' | 'movements';

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
