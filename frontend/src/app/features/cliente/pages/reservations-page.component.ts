import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  lucideArrowRight,
  lucideBookmark,
  lucideCalendar,
  lucideCheckCircle2,
  lucideClock,
  lucideMapPin,
  lucideStore,
  lucideTrash2,
} from '@ng-icons/lucide';

import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInput } from '../../../components/input/src';
import { HlmSelectImports } from '../../../components/select/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { requestWithToast } from '../../../core/utils/request-toast.util';
import { CatalogBranch } from '../../shared/models/catalog.model';
import { CreateReservationRequest } from '../../shared/models/reservation.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { ReservationApiService } from '../../shared/services/reservation-api.service';
import { ReservationDraftService } from '../../shared/services/reservation-draft.service';

@Component({
  selector: 'app-reservations-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    ReactiveFormsModule,
    NgIcon,
    HlmButton,
    HlmInput,
    ...HlmBadgeImports,
    ...HlmCardImports,
    ...HlmFieldImports,
    ...HlmSelectImports,
  ],
  providers: [
    provideIcons({
      lucideCalendar,
      lucideClock,
      lucideMapPin,
      lucideBookmark,
      lucideTrash2,
      lucideCheckCircle2,
      lucideArrowRight,
      lucideStore,
    }),
  ],
  templateUrl: './reservations-page.component.html',
})
export class ReservationsPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly catalogApi = inject(CatalogApiService);
  private readonly reservationApi = inject(ReservationApiService);
  protected readonly reservationDraft = inject(ReservationDraftService);
  private readonly router = inject(Router);

  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly loadingBranches = signal(false);
  protected readonly submitting = signal(false);
  protected readonly reservationSuccess = signal(false);

  protected readonly form = this.fb.nonNullable.group({
    branch_id: [this.reservationDraft.selectedBranchId() || '', Validators.required],
    visit_date: ['', Validators.required],
  });

  protected readonly branchSelectLabel = (branchId: string | null | undefined): string => {
    if (!branchId) return 'Seleccionar sucursal';
    const branch = this.branches().find((item) => item.id === branchId);
    return branch ? `${branch.name} — ${branch.city}` : branchId;
  };

  protected itemSubtotal(item: { unit_price: string; quantity: number }): number {
    return Number(item.unit_price || 0) * item.quantity;
  }

  constructor() {
    void this.loadBranches();
  }

  protected selectedBranch(): CatalogBranch | null {
    const branchId = this.form.controls.branch_id.value;
    return this.branches().find((b) => b.id === branchId) ?? null;
  }

  protected onBranchChange(branchId: string | null | undefined): void {
    const val = branchId || '';
    this.form.controls.branch_id.setValue(val);
    this.reservationDraft.setBranchId(val);
  }

  protected canSubmit(): boolean {
    return (
      this.form.valid &&
      this.reservationDraft.items().length > 0 &&
      !this.submitting()
    );
  }

  protected async submitReservation(): Promise<void> {
    if (!this.form.controls.branch_id.value) {
      toast.warning('Selecciona la sucursal física para tu visita.');
      return;
    }

    if (!this.form.controls.visit_date.value) {
      toast.warning('Ingresa la fecha y hora de tu visita.');
      return;
    }

    if (this.reservationDraft.items().length === 0) {
      toast.warning('Tu borrador no tiene prendas. Agrega prendas desde el catálogo.');
      return;
    }

    this.submitting.set(true);
    try {
      const formValue = this.form.getRawValue();
      const visitDateStr = formValue.visit_date
        ? formValue.visit_date.includes('T')
          ? formValue.visit_date.split('T')[0]
          : formValue.visit_date
        : '';
      const payload: CreateReservationRequest = {
        branch_id: formValue.branch_id,
        visit_date: visitDateStr || formValue.visit_date,
        items: this.reservationDraft.items().map((item) => ({
          variant_id: item.variant_id,
          quantity: item.quantity,
        })),
      };

      await requestWithToast(
        this.reservationApi.createReservation(payload),
        {
          loading: 'Confirmando tu reserva...',
          success: 'Reserva creada. Paga el anticipo del 50 % en Mis reservas para confirmarla.',
          error: 'No se pudo crear la reserva.',
        },
      );

      this.reservationDraft.clearDraft();
      this.form.reset({ branch_id: '', visit_date: '' });
      // D1: the reservation only holds the visit after the 50 % deposit is paid.
      await this.router.navigate(['/app/cliente/my-reservations']);
    } catch {
      // Toast handled by requestWithToast.
    } finally {
      this.submitting.set(false);
    }
  }

  private async loadBranches(): Promise<void> {
    this.loadingBranches.set(true);
    try {
      const response = await firstValueFrom(this.catalogApi.listPublicBranches());
      const branchList = response.data ?? [];
      this.branches.set(branchList);

      const draftBranch = this.reservationDraft.selectedBranchId();
      if (draftBranch && branchList.some((b) => b.id === draftBranch)) {
        this.form.controls.branch_id.setValue(draftBranch);
      } else if (!this.form.controls.branch_id.value && branchList.length > 0) {
        const defaultB = branchList.find((b) => b.is_default) ?? branchList[0];
        if (defaultB) {
          this.form.controls.branch_id.setValue(defaultB.id);
          this.reservationDraft.setBranchId(defaultB.id);
        }
      }
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar las sucursales.'));
    } finally {
      this.loadingBranches.set(false);
    }
  }
}
