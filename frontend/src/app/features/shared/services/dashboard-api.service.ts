import { Injectable, inject } from '@angular/core';

import { ApiService } from '../../../core/services/api.service';
import { DashboardQuery, DashboardResponse } from '../models/dashboard.model';

@Injectable({ providedIn: 'root' })
export class DashboardApiService {
  private readonly api = inject(ApiService);

  getDashboard(filters: DashboardQuery) {
    return this.api.get<DashboardResponse>(`/dashboard${this.query(filters)}`);
  }

  private query(filters: DashboardQuery): string {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    const query = params.toString();
    return query ? `?${query}` : '';
  }
}
