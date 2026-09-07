import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmTable } from '../../../components/table/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { CatalogBranch } from '../../shared/models/catalog.model';
import { Reservation } from '../../shared/models/reservation.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { ReservationApiService } from '../../shared/services/reservation-api.service';
import { SessionService } from '../../shared/services/session.service';

@Component({
  selector: 'app-encargado-reservations-page',
  standalone: true,
  imports: [CommonModule, HlmButton, HlmTable, ...HlmBadgeImports, ...HlmCardImports],
  templateUrl: './reservations-page.component.html',
})
export class ReservationsPageComponent {
  private readonly catalogApi = inject(CatalogApiService);
  private readonly reservationApi = inject(ReservationApiService);
  private readonly session = inject(SessionService);

  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly reservations = signal<Reservation[]>([]);
  protected readonly loading = signal(false);

  constructor() {
    void this.loadData();
  }

  protected get branchId(): string | null {
    return this.session.user()?.branch_id ?? null;
  }

  protected get total(): number {
    return this.reservations().length;
  }

  protected get pending(): number {
    return this.reservations().filter((item) => item.status === 'pending' || item.status === 'confirmed').length;
  }

  protected get expired(): number {
    return this.reservations().filter((item) => item.status === 'expired').length;
  }

  protected branchName(branchId: string | null | undefined): string {
    if (!branchId) return 'Sin sucursal';
    return this.branches().find((branch) => branch.id === branchId)?.name ?? branchId;
  }

  protected reservationStatusLabel(status: Reservation['status']): string {
    switch (status) {
      case 'pending': return 'Pendiente';
      case 'confirmed': return 'Confirmada';
      case 'attended': return 'Atendida';
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
      case 'cancelled': return 'bg-rose-100 text-rose-700';
      case 'expired': return 'bg-slate-100 text-slate-700';
      default: return 'bg-slate-100 text-slate-700';
    }
  }

  protected async refresh(): Promise<void> {
    await this.loadReservations();
  }

  private async loadData(): Promise<void> {
    this.loading.set(true);
    try {
      const [branches] = await Promise.all([firstValueFrom(this.catalogApi.listPublicBranches())]);
      this.branches.set(branches.data ?? []);
      await this.loadReservations();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar las reservas de sucursal.'));
    } finally {
      this.loading.set(false);
    }
  }

  private async loadReservations(): Promise<void> {
    const branchId = this.branchId;
    if (!branchId) {
      this.reservations.set([]);
      return;
    }

    try {
      const response = await firstValueFrom(this.reservationApi.listBranchReservations(branchId));
      this.reservations.set((response.data ?? []) as Reservation[]);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar las reservas.'));
      this.reservations.set([]);
    }
  }
}
