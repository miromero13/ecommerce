import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmCalendarImports } from '../../../components/calendar/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInputImports } from '../../../components/input/src';
import { HlmSelectImports } from '../../../components/select/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { requestWithToast } from '../../../core/utils/request-toast.util';
import { SessionService } from '../services/session.service';
import { PromotionApiService } from '../services/promotion-api.service';
import { PromotionCode } from '../models/promotion.model';

@Component({
  selector: 'app-promotions-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HlmButton, ...HlmCardImports, ...HlmCalendarImports, ...HlmFieldImports, ...HlmInputImports, ...HlmSelectImports],
  templateUrl: './promotions-page.component.html',
})
export class PromotionsPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(PromotionApiService);
  private readonly session = inject(SessionService);
  protected readonly codes = signal<PromotionCode[]>([]);
  protected readonly loading = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly validUntilError = signal(false);
  protected readonly modalOpen = signal(false);
  protected readonly calendarDate = signal<Date | undefined>(undefined);
  protected readonly calendarOpen = signal(false);
  protected readonly noExpiration = signal(false);
  protected readonly isAdmin = computed(() => this.session.user()?.rol === 'administrador');
  protected readonly discountTypeSelectLabel = (discountType: string | null | undefined): string => {
    return discountType === 'fixed' ? 'Monto fijo' : 'Porcentaje';
  };
  protected readonly form = this.fb.nonNullable.group({
    code: ['', [Validators.required]],
    discount_type: ['percentage' as 'percentage' | 'fixed', [Validators.required]],
    discount_value: ['', [Validators.required, Validators.min(0)]],
    valid_until: [''],
  });

  constructor() { void this.load(); }

  protected openModal(): void {
    this.form.reset({ code: '', discount_type: 'percentage', discount_value: '', valid_until: '' });
    this.calendarDate.set(undefined);
    this.calendarOpen.set(false);
    this.noExpiration.set(false);
    this.validUntilError.set(false);
    this.error.set(null);
    this.modalOpen.set(true);
  }

  protected closeModal(): void {
    this.modalOpen.set(false);
    this.calendarOpen.set(false);
  }

  protected toggleCalendar(): void {
    if (this.noExpiration()) return;
    this.calendarOpen.update((open) => !open);
  }

  protected toggleNoExpiration(value: boolean): void {
    this.noExpiration.set(value);
    this.calendarOpen.set(false);
    this.validUntilError.set(false);
    if (value) {
      this.calendarDate.set(undefined);
      this.form.controls.valid_until.setValue('');
    }
  }

  protected selectValidUntil(date: Date | undefined): void {
    this.noExpiration.set(false);
    this.validUntilError.set(false);
    this.calendarDate.set(date);
    this.form.controls.valid_until.setValue(date ? this.toDateTimeLocal(date) : '');
    this.calendarOpen.set(false);
  }

  private toDateTimeLocal(date: Date): string {
    const localDate = new Date(date);
    localDate.setHours(23, 59, 0, 0);
    const offsetDate = new Date(localDate.getTime() - localDate.getTimezoneOffset() * 60000);
    return offsetDate.toISOString().slice(0, 16);
  }

  protected async load(): Promise<void> {
    try {
      const response = await firstValueFrom(this.api.list());
      this.codes.set(response.data ?? []);
    } catch (error) {
      this.error.set(getErrorMessage(error, 'No se pudieron cargar los códigos.'));
    }
  }

  protected async create(): Promise<void> {
    const requiresValidUntil = !this.noExpiration() && !this.form.controls.valid_until.value;
    this.validUntilError.set(requiresValidUntil);
    if (this.form.invalid || requiresValidUntil) return;
    this.loading.set(true);
    try {
      const value = this.form.getRawValue();
      await requestWithToast(this.api.create({
        code: value.code,
        discount_type: value.discount_type,
        discount_value: value.discount_value,
        valid_until: value.valid_until ? new Date(value.valid_until).toISOString() : null,
        branch_id: this.isAdmin() ? null : this.session.user()?.branch_id ?? null,
      }), { loading: 'Creando código...', success: 'Código creado.', error: 'No se pudo crear el código.' });
      this.form.reset({ code: '', discount_type: 'percentage', discount_value: '', valid_until: '' });
      this.calendarDate.set(undefined);
      this.calendarOpen.set(false);
      this.noExpiration.set(false);
      this.validUntilError.set(false);
      await this.load();
      this.closeModal();
    } catch {
      // toast handled by requestWithToast
    } finally {
      this.loading.set(false);
    }
  }
}
