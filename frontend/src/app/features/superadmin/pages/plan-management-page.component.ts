import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { toast } from '@spartan-ng/brain/sonner';
import { firstValueFrom } from 'rxjs';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideLayers, lucidePencil, lucidePlus, lucidePower } from '@ng-icons/lucide';

import { HlmButtonImports } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInput } from '../../../components/input/src';
import { HlmTableImports } from '../../../components/table/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { PLAN_FEATURES, SubscriptionPlan, SubscriptionPlanPayload } from '../../shared/models/subscription.model';
import { SubscriptionApiService } from '../../shared/services/subscription-api.service';

@Component({
  selector: 'app-plan-management-page',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    NgIcon,
    HlmInput,
    ...HlmButtonImports,
    ...HlmCardImports,
    ...HlmFieldImports,
    ...HlmTableImports,
  ],
  providers: [provideIcons({ lucideLayers, lucidePencil, lucidePlus, lucidePower })],
  templateUrl: './plan-management-page.component.html',
})
export class PlanManagementPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(SubscriptionApiService);

  protected readonly features = PLAN_FEATURES;
  protected readonly plans = signal<SubscriptionPlan[]>([]);
  protected readonly loading = signal(false);
  protected readonly modalOpen = signal(false);
  protected readonly submitting = signal(false);
  protected readonly errorMessage = signal<string | null>(null);
  /** Plan being edited; null while creating a new one. */
  protected readonly editing = signal<SubscriptionPlan | null>(null);
  protected readonly selectedFeatures = signal<string[]>([]);

  protected readonly form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(100)]],
    slug: ['', [Validators.required, Validators.maxLength(45), Validators.pattern(/^[a-z0-9]+(?:-[a-z0-9]+)*$/)]],
    description: [''],
    price_monthly: [0, [Validators.required, Validators.min(0)]],
    price_yearly: [0, [Validators.required, Validators.min(0)]],
    max_branches: [1, [Validators.required, Validators.min(1)]],
    max_garments: [1, [Validators.required, Validators.min(1)]],
    is_active: [true],
  });

  constructor() {
    void this.loadPlans();
  }

  protected async loadPlans(): Promise<void> {
    this.loading.set(true);
    try {
      const res = await firstValueFrom(this.api.getAllPlans());
      this.plans.set(res.data ?? []);
    } catch (err) {
      toast.error(getErrorMessage(err, 'No se pudieron cargar los planes.'));
    } finally {
      this.loading.set(false);
    }
  }

  protected openCreate(): void {
    this.editing.set(null);
    this.errorMessage.set(null);
    this.form.reset({
      name: '', slug: '', description: '', price_monthly: 0, price_yearly: 0,
      max_branches: 1, max_garments: 100, is_active: true,
    });
    this.form.controls.slug.enable();
    this.selectedFeatures.set(['catalog', 'pos', 'inventory', 'reservations', 'standard_reports']);
    this.modalOpen.set(true);
  }

  protected openEdit(plan: SubscriptionPlan): void {
    this.editing.set(plan);
    this.errorMessage.set(null);
    this.form.reset({
      name: plan.name, slug: plan.slug, description: plan.description ?? '',
      price_monthly: plan.price_monthly, price_yearly: plan.price_yearly,
      max_branches: plan.max_branches, max_garments: plan.max_garments, is_active: plan.is_active,
    });
    // The slug defines the plan id, so it cannot change after creation.
    this.form.controls.slug.disable();
    this.selectedFeatures.set([...plan.features]);
    this.modalOpen.set(true);
  }

  protected closeModal(): void {
    this.modalOpen.set(false);
  }

  protected hasFeature(key: string): boolean {
    return this.selectedFeatures().includes(key);
  }

  protected toggleFeature(key: string): void {
    this.selectedFeatures.update((keys) => (keys.includes(key) ? keys.filter((item) => item !== key) : [...keys, key]));
  }

  protected featureLabel(key: string): string {
    return this.features.find((feature) => feature.key === key)?.label ?? key;
  }

  protected async save(): Promise<void> {
    if (this.form.invalid || this.submitting()) {
      this.form.markAllAsTouched();
      return;
    }
    const value = this.form.getRawValue();
    const payload: SubscriptionPlanPayload = {
      name: value.name.trim(),
      description: value.description.trim() || null,
      price_monthly: Number(value.price_monthly),
      price_yearly: Number(value.price_yearly),
      max_branches: Number(value.max_branches),
      max_garments: Number(value.max_garments),
      // Keep the catalog order so every screen lists modules the same way.
      features: this.features.map((feature) => feature.key).filter((key) => this.hasFeature(key)),
      is_active: value.is_active,
    };
    const editing = this.editing();
    this.submitting.set(true);
    this.errorMessage.set(null);
    try {
      const res = await firstValueFrom(
        editing ? this.api.updatePlan(editing.id, payload) : this.api.createPlan({ ...payload, slug: value.slug.trim() }),
      );
      toast.success(res.message);
      this.modalOpen.set(false);
      await this.loadPlans();
    } catch (err) {
      this.errorMessage.set(getErrorMessage(err, 'No se pudo guardar el plan.'));
    } finally {
      this.submitting.set(false);
    }
  }

  protected async toggleActive(plan: SubscriptionPlan): Promise<void> {
    try {
      const res = await firstValueFrom(this.api.updatePlan(plan.id, { is_active: !plan.is_active }));
      toast.success(res.message);
      await this.loadPlans();
    } catch (err) {
      toast.error(getErrorMessage(err, 'No se pudo cambiar el estado del plan.'));
    }
  }
}
