import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { CreateReservationRequest, Reservation, ReservationListResponse, ReservationResponse } from '../models/reservation.model';
import { CartResponse } from '../models/cart.model';

@Injectable({ providedIn: 'root' })
export class ReservationApiService {
  private readonly api = inject(ApiService);

  listMyReservations() {
    return this.api.get<ReservationListResponse>('/reservations/me');
  }

  listBranchReservations(branchId?: string) {
    const query = branchId ? `?branch_id=${encodeURIComponent(branchId)}` : '';
    return this.api.get<ApiResponse<Reservation[]>>(`/reservations/branch${query}`);
  }

  createReservation(payload: CreateReservationRequest) {
    return this.api.post<ReservationResponse>('/reservations', payload);
  }

  cancelReservation(reservationId: string) {
    return this.api.patch<ReservationResponse>(`/reservations/${reservationId}/cancel`, {});
  }

  decideReservation(reservationId: string, purchase: boolean) {
    return this.api.patch<ReservationResponse>(`/reservations/${reservationId}/decision`, { purchase });
  }

  transferToCart(reservationId: string) {
    return this.api.post<CartResponse>(`/reservations/${reservationId}/to-cart`, {});
  }

  confirmArrival(reservationId: string, branchId?: string) {
    const query = branchId ? `?branch_id=${encodeURIComponent(branchId)}` : '';
    return this.api.patch<ReservationResponse>(`/reservations/${reservationId}/arrival${query}`, {});
  }

  attendReservation(reservationId: string, branchId?: string) {
    const query = branchId ? `?branch_id=${encodeURIComponent(branchId)}` : '';
    return this.api.patch<ReservationResponse>(`/reservations/${reservationId}/attend${query}`, {});
  }

  cancelBranchReservation(reservationId: string, branchId?: string) {
    const query = branchId ? `?branch_id=${encodeURIComponent(branchId)}` : '';
    return this.api.patch<ReservationResponse>(`/reservations/${reservationId}/branch-cancel${query}`, {});
  }
}
