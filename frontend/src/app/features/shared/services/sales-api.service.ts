import { Injectable, inject } from '@angular/core';

import { ApiService } from '../../../core/services/api.service';
import { ApiResponse } from '../../../core/models/api.model';
import { Reservation } from '../models/reservation.model';
import { CreateSaleRequest, SaleResponse, SalesListResponse } from '../models/sale.model';

@Injectable({ providedIn: 'root' })
export class SalesApiService {
  private readonly api = inject(ApiService);

  listBranchSales(branchId?: string) {
    const query = branchId ? `?branch_id=${encodeURIComponent(branchId)}` : '';
    return this.api.get<SalesListResponse>(`/sales/branch${query}`);
  }

  getSale(saleId: string, branchId?: string) {
    const query = branchId ? `?branch_id=${encodeURIComponent(branchId)}` : '';
    return this.api.get<SaleResponse>(`/sales/${saleId}${query}`);
  }

  createSale(payload: CreateSaleRequest) {
    return this.api.post<SaleResponse>('/sales', payload);
  }

  searchReservation(reservationId: string, branchId?: string) {
    const query = branchId ? `?branch_id=${encodeURIComponent(branchId)}` : '';
    return this.api.get<ApiResponse<Reservation>>(`/reservations/branch/${reservationId}${query}`);
  }
}
