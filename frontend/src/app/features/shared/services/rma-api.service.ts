import { Injectable, inject } from '@angular/core';
import { HttpParams } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import {
  CreateRmaRequestPayload,
  EligibleOrder,
  ReviewRmaItemPayload,
  RmaRequest,
} from '../models/rma.model';

@Injectable({ providedIn: 'root' })
export class RmaApiService {
  private readonly api = inject(ApiService);

  getEligibleOrders() {
    return this.api.get<ApiResponse<EligibleOrder[]>>('/rma/eligible-orders');
  }

  createRmaRequest(payload: CreateRmaRequestPayload) {
    return this.api.post<ApiResponse<RmaRequest>>('/rma/requests', payload);
  }

  getRmaRequests(status?: string) {
    const params = status ? new HttpParams().set('status', status) : new HttpParams();
    return this.api.get<ApiResponse<RmaRequest[]>>('/rma/requests', { params });
  }

  getRmaRequest(id: string) {
    return this.api.get<ApiResponse<RmaRequest>>(`/rma/requests/${id}`);
  }

  async downloadRmaPdf(rmaId: string, rmaNumber?: string): Promise<void> {
    const blob = await firstValueFrom(
      this.api.get<Blob>(`/rma/requests/${rmaId}/pdf`, { responseType: 'blob' as const }),
    );
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Ficha_${rmaNumber || rmaId.slice(0, 8)}.pdf`;
    link.click();
    URL.revokeObjectURL(url);
  }

  reviewRmaItem(rmaId: string, itemId: string, payload: ReviewRmaItemPayload) {
    return this.api.patch<ApiResponse<RmaRequest>>(`/rma/requests/${rmaId}/items/${itemId}/review`, payload);
  }

  settleMonthlyWallets() {
    return this.api.post<ApiResponse<{ settled_count: number; total_amount: number }>>('/rma/settle-monthly-wallets', {});
  }
}
