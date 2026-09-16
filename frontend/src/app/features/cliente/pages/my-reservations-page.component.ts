import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { requestWithToast } from '../../../core/utils/request-toast.util';
import { Reservation } from '../../shared/models/reservation.model';
import { ReservationApiService } from '../../shared/services/reservation-api.service';

@Component({
  selector: 'app-my-reservations-page',
  standalone: true,
  imports: [CommonModule, HlmButton, ...HlmBadgeImports, ...HlmCardImports],
  templateUrl: './my-reservations-page.component.html',
})
export class MyReservationsPageComponent {
  private readonly reservationApi = inject(ReservationApiService);

  protected readonly reservations = signal<Reservation[]>([]);

  constructor() {
    void this.loadReservations();
  }

  protected reservationStatusLabel(status: Reservation['status']): string {
    switch (status) {
      case 'pending': return 'Pendiente';
      case 'confirmed': return 'Confirmada';
      case 'attended': return 'Atendida';
      case 'purchase_pending': return 'Compra pendiente';
      case 'sold': return 'Vendida';
      case 'not_sold': return 'No comprada';
      case 'cancelled': return 'Cancelada';
      case 'expired': return 'Vencida';
      default: return status;
    }
  }

  protected reservationStatusClass(status: Reservation['status']): string {
    switch (status) {
      case 'pending': return 'bg-amber-100 text-amber-700';
      case 'confirmed': return 'bg-sky-100 text-sky-700';
      case 'attended': return 'bg-emerald-100 text-emerald-700';
      case 'purchase_pending': return 'bg-violet-100 text-violet-700';
      case 'sold': return 'bg-emerald-100 text-emerald-700';
      case 'not_sold': return 'bg-slate-100 text-slate-700';
      case 'cancelled': return 'bg-rose-100 text-rose-700';
      case 'expired': return 'bg-slate-100 text-slate-700';
      default: return 'bg-slate-100 text-slate-700';
    }
  }

  protected async cancelReservation(reservationId: string): Promise<void> {
    try {
      const response = await requestWithToast(
        this.reservationApi.cancelReservation(reservationId),
        { loading: 'Cancelando reserva...', success: 'Reserva cancelada.', error: 'No se pudo cancelar la reserva.' },
      );
      const updated = response.data;
      if (updated) this.reservations.update((current) => current.map((item) => item.id === updated.id ? updated : item));
    } catch {
      // Toast handled by requestWithToast.
    }
  }

  protected async decideReservation(reservationId: string, purchase: boolean): Promise<void> {
    try {
      const response = await requestWithToast(
        this.reservationApi.decideReservation(reservationId, purchase),
        {
          loading: purchase ? 'Confirmando compra...' : 'Cerrando reserva...',
          success: purchase ? 'Compra de reserva confirmada.' : 'Reserva cerrada sin compra.',
          error: 'No se pudo actualizar la reserva.',
        },
      );
      const updated = response.data;
      if (updated) this.reservations.update((current) => current.map((item) => item.id === updated.id ? updated : item));
    } catch {
      // Toast handled by requestWithToast.
    }
  }

  protected async transferToCart(reservationId: string): Promise<void> {
    try {
      await requestWithToast(
        this.reservationApi.transferToCart(reservationId),
        { loading: 'Pasando prendas al carrito...', success: 'Prendas transferidas al carrito.', error: 'No se pudo transferir la reserva.' },
      );
    } catch {
      // Toast handled by requestWithToast.
    }
  }

  private async loadReservations(): Promise<void> {
    try {
      const response = await firstValueFrom(this.reservationApi.listMyReservations());
      this.reservations.set(response.data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar las reservas.'));
    }
  }
}
