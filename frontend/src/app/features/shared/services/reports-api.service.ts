import { Injectable, inject } from '@angular/core';

import { ApiService } from '../../../core/services/api.service';
import {
  InventoryReportResponse,
  MovementsReportResponse,
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

  exportReport(type: ReportType, filters: ReportQuery) {
    return this.api.get<Blob>(`/reports/${type}/export${this.query(filters)}`, { responseType: 'blob' as const });
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
