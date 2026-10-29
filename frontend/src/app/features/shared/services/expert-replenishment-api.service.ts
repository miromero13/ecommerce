import { HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import {
  ApplyTransfersRequest,
  ExpertRule,
  ExpertRuleUpdate,
  ExpertSuggestion,
} from '../models/expert-replenishment.model';

@Injectable({ providedIn: 'root' })
export class ExpertReplenishmentApiService {
  private readonly api = inject(ApiService);
  private readonly endpoint = '/inventory/expert-replenishment';

  getRules(): Observable<ApiResponse<ExpertRule>> {
    return this.api.get<ApiResponse<ExpertRule>>(`${this.endpoint}/rules`);
  }

  updateRules(payload: ExpertRuleUpdate): Observable<ApiResponse<ExpertRule>> {
    return this.api.put<ApiResponse<ExpertRule>>(`${this.endpoint}/rules`, payload);
  }

  evaluate(): Observable<ApiResponse<ExpertSuggestion[]>> {
    return this.api.post<ApiResponse<ExpertSuggestion[]>>(`${this.endpoint}/evaluate`, {});
  }

  getSuggestions(status?: string): Observable<ApiResponse<ExpertSuggestion[]>> {
    let params = new HttpParams();
    if (status) {
      params = params.set('status', status);
    }
    return this.api.get<ApiResponse<ExpertSuggestion[]>>(`${this.endpoint}/suggestions`, { params });
  }

  applyTransfers(payload: ApplyTransfersRequest): Observable<ApiResponse<{ applied_count: number }>> {
    return this.api.post<ApiResponse<{ applied_count: number }>>(`${this.endpoint}/apply-transfers`, payload);
  }
}
