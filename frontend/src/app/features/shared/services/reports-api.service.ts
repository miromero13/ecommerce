import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import {
  CustomerClusters,
  DemandForecast,
  DemandForecastRequest,
  SmartReportResponse,
  SmartReportType,
  InventoryReportResponse,
  MovementsReportResponse,
  NaturalReportResponse,
  ReportQuery,
  SalesReportResponse,
  ReportType,
} from '../models/report.model';

@Injectable({ providedIn: 'root' })
export class ReportsApiService {
  private readonly api = inject(ApiService);

  getSalesReport(filters: ReportQuery) {
    return this.api.get<SalesReportResponse>(`/reports/sales${this.query(filters)}`);
  }

  getInventoryReport(filters: ReportQuery) {
    return this.api.get<InventoryReportResponse>(`/reports/inventory${this.query(filters)}`);
  }

  getMovementsReport(filters: ReportQuery) {
    return this.api.get<MovementsReportResponse>(`/reports/movements${this.query(filters)}`);
  }

  queryNaturalLanguage(query: string) {
    return this.api.post<NaturalReportResponse>('/reports/query', { query });
  }

  exportReport(type: ReportType, filters: ReportQuery) {
    return this.api.get<Blob>(`/reports/${type}/export${this.query(filters)}`, { responseType: 'blob' as const });
  }

  getSmartReport(type: SmartReportType, filters: ReportQuery) {
    const paths: Record<SmartReportType, string> = {
      sales: 'sales', inventory: 'inventory', movements: 'movements',
      top_products: 'top-products', branch_comparison: 'branch-comparison', critical_inventory: 'critical-inventory',
    };
    return this.api.get<SmartReportResponse>(`/reports/${paths[type]}${this.query(filters)}`);
  }

  predictDemand(payload: DemandForecastRequest) {
    return this.api.post<ApiResponse<DemandForecast>>('/reports/ml/predict-demand', payload);
  }

  customerClusters(useSyntheticData = false) {
    return this.api.post<ApiResponse<CustomerClusters>>('/reports/ml/customer-clusters', { use_synthetic_data: useSyntheticData });
  }

  exportExcel(type: SmartReportType, filters: ReportQuery) {
    return this.api.get<Blob>(`/reports/export/excel${this.exportQuery(type, filters)}`, { responseType: 'blob' as const });
  }

  exportPdf(type: SmartReportType, filters: ReportQuery) {
    return this.api.get<Blob>(`/reports/export/pdf${this.exportQuery(type, filters)}`, { responseType: 'blob' as const });
  }

  private exportQuery(type: SmartReportType, filters: ReportQuery): string {
    const query = this.query(filters);
    return `?type=${type}${query ? `&${query.slice(1)}` : ''}`;
  }

  private query(filters: ReportQuery): string {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    const query = params.toString();
    return query ? `?${query}` : '';
  }
}
