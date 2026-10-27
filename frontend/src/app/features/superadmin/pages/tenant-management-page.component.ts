import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  lucideBuilding2,
  lucideCheckCircle2,
  lucideGlobe,
  lucidePlus,
  lucideSearch,
  lucideShieldAlert,
  lucideStore,
  lucideUsers,
} from '@ng-icons/lucide';

import { AdminActionMenuComponent } from '../../admin/components/admin-action-menu.component';
import { HlmButtonImports } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInput } from '../../../components/input/src';
import { HlmTableImports } from '../../../components/table/src';
import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmSelectImports } from '../../../components/select/src';
import { Tenant, TenantStatus } from '../../shared/models/tenant.model';
import { TenantApiService } from '../../shared/services/tenant-api.service';
import { SubscriptionApiService } from '../../shared/services/subscription-api.service';
import { SubscriptionPlan } from '../../shared/models/subscription.model';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import {
  COUNTRIES_LIST,
  CURRENCIES_LIST,
  CountryOption,
} from '../../../core/utils/countries-data.util';
import { TenantBrandingEditorComponent } from '../../shared/components/tenant-branding-editor.component';

@Component({
  selector: 'app-tenant-management-page',
  standalone: true,
  imports: [
    TenantBrandingEditorComponent,
    CommonModule,
    ReactiveFormsModule,
    NgIcon,
    HlmInput,
    AdminActionMenuComponent,
    ...HlmButtonImports,
    ...HlmCardImports,
    ...HlmFieldImports,
    ...HlmTableImports,
    ...HlmBadgeImports,
    ...HlmSelectImports,
  ],
  providers: [
    provideIcons({
      lucideBuilding2,
      lucideSearch,
      lucidePlus,
      lucideShieldAlert,
      lucideCheckCircle2,
      lucideStore,
      lucideUsers,
      lucideGlobe,
    }),
  ],
  templateUrl: './tenant-management-page.component.html',
})
export class TenantManagementPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(TenantApiService);
  private readonly subscriptionApi = inject(SubscriptionApiService);

  protected readonly countries: CountryOption[] = COUNTRIES_LIST;
  protected readonly currencies: string[] = CURRENCIES_LIST;

  protected readonly tenants = signal<Tenant[]>([]);
  protected readonly loading = signal<boolean>(false);
  protected readonly searchTerm = signal<string>('');
  protected readonly statusFilter = signal<'all' | 'active' | 'suspended'>('all');
  protected readonly modalOpen = signal<boolean>(false);
  protected readonly submitting = signal<boolean>(false);
  protected readonly errorMessage = signal<string | null>(null);

  protected readonly openMenuId = signal<string | null>(null);
  protected readonly viewModalOpen = signal<boolean>(false);
  protected readonly selectedTenant = signal<Tenant | null>(null);

  protected readonly countrySearch = signal<string>('');

  protected readonly countrySelectLabel = (countryName: string | null | undefined): string => {
    if (!countryName) return 'Seleccionar país';
    const c = this.countries.find((item) => item.name === countryName);
    return c ? `${c.name} (${c.code})` : countryName;
  };

  protected readonly currencySelectLabel = (currency: string | null | undefined): string => {
    return currency || 'Seleccionar moneda';
  };

  protected readonly filteredCountries = computed(() => {
    const search = this.countrySearch().trim().toLowerCase();
    if (!search) {
      return this.countries;
    }
    return this.countries.filter((c) =>
      c.name.toLowerCase().includes(search) || c.code.toLowerCase().includes(search),
    );
  });

  protected readonly createForm = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    slug: ['', [Validators.required, Validators.minLength(2)]],
    contact_email: ['', [Validators.required, Validators.email]],
    country: ['Bolivia', [Validators.required]],
    currency: ['BOB', [Validators.required]],
    admin_name: ['', [Validators.required, Validators.minLength(2)]],
    plan_id: ['plan_basic', [Validators.required]],
    billing_cycle: ['monthly', [Validators.required]],
  });

  protected readonly metrics = computed(() => {
    const all = this.tenants();
    const active = all.filter((t) => t.status === 'active').length;
    const suspended = all.filter((t) => t.status === 'suspended').length;
    return { total: all.length, active, suspended };
  });

  protected readonly filteredTenants = computed(() => {
    let list = this.tenants();
    const search = this.searchTerm().trim().toLowerCase();
    const status = this.statusFilter();

    if (status !== 'all') {
      list = list.filter((t) => t.status === status);
    }

    if (search) {
      list = list.filter(
        (t) =>
          t.name.toLowerCase().includes(search) ||
          t.slug.toLowerCase().includes(search) ||
          t.contact_email.toLowerCase().includes(search),
      );
    }

    return list;
  });

  // Only plans on sale; the superadmin may have created or deactivated some.
  protected readonly plans = signal<SubscriptionPlan[]>([]);

  protected async loadPlans(): Promise<void> {
    try {
      const res = await firstValueFrom(this.subscriptionApi.getPlans());
      this.plans.set(res.data ?? []);
    } catch {
      this.plans.set([]);
    }
  }

  constructor() {
    void this.loadTenants();
    void this.loadPlans();
    this.createForm.controls.country.valueChanges.subscribe((selectedCountryName) => {
      const found = this.countries.find((c) => c.name === selectedCountryName);
      if (found && found.currency) {
        this.createForm.controls.currency.setValue(found.currency);
      }
    });
  }

  protected async loadTenants(): Promise<void> {
    this.loading.set(true);
    try {
      const res = await firstValueFrom(this.api.listTenants({ limit: 100 }));
      this.tenants.set(res.data ?? []);
    } catch {
      this.tenants.set([]);
    } finally {
      this.loading.set(false);
    }
  }

  protected onSearchInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.searchTerm.set(input.value);
  }

  protected setStatusFilter(status: 'all' | 'active' | 'suspended'): void {
    this.statusFilter.set(status);
  }

  protected openCreateModal(): void {
    this.closeMenu();
    this.errorMessage.set(null);
    this.countrySearch.set('');
    this.createForm.reset({
      name: '',
      slug: '',
      contact_email: '',
      country: 'Bolivia',
      currency: 'BOB',
      admin_name: '',
      plan_id: this.plans()[0]?.id ?? '',
      billing_cycle: 'monthly',
    });
    this.modalOpen.set(true);
  }

  protected closeModal(): void {
    this.modalOpen.set(false);
  }

  protected toggleMenu(tenantId: string): void {
    this.openMenuId.set(this.openMenuId() === tenantId ? null : tenantId);
  }

  protected closeMenu(): void {
    this.openMenuId.set(null);
  }

  protected openDetailModal(tenant: Tenant): void {
    this.closeMenu();
    this.selectedTenant.set(tenant);
    this.viewModalOpen.set(true);
  }

  protected closeDetailModal(): void {
    this.viewModalOpen.set(false);
    this.selectedTenant.set(null);
  }

  protected onNameInput(): void {
    const nameVal = this.createForm.controls.name.value;
    const autoSlug = nameVal
      .toLowerCase()
      .trim()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
    this.createForm.controls.slug.setValue(autoSlug);
  }

  /**
   * Cuando el usuario selecciona un país de la librería,
   * automáticamente autocompleta su moneda principal,
   * permitiendo que luego la cambie libremente si lo desea.
   */
  protected onCountryChange(event: Event): void {
    const select = event.target as HTMLSelectElement;
    const selectedCountryName = select.value;
    const found = this.countries.find((c) => c.name === selectedCountryName);
    if (found && found.currency) {
      this.createForm.controls.currency.setValue(found.currency);
    }
  }

  protected async saveTenant(): Promise<void> {
    if (this.createForm.invalid) return;

    this.submitting.set(true);
    this.errorMessage.set(null);

    const val = this.createForm.getRawValue();
    try {
      await firstValueFrom(
        this.subscriptionApi.createTenantWithSubscription({
          name: val.name,
          slug: val.slug,
          contact_email: val.contact_email,
          currency: val.currency,
          country: val.country,
          admin_name: val.admin_name,
          plan_id: val.plan_id,
          billing_cycle: val.billing_cycle as 'monthly' | 'yearly',
          payment_method: 'cash',
        }),
      );
      this.closeModal();
      await this.loadTenants();
    } catch (err: unknown) {
      this.errorMessage.set(getErrorMessage(err, 'No se pudo registrar la empresa'));
    } finally {
      this.submitting.set(false);
    }
  }

  protected async toggleTenantStatus(tenant: Tenant): Promise<void> {
    this.closeMenu();
    const nextStatus: TenantStatus = tenant.status === 'active' ? 'suspended' : 'active';
    try {
      await firstValueFrom(this.api.updateTenantStatus(tenant.id, nextStatus));
      await this.loadTenants();
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'No se pudo actualizar el estado de la empresa'));
    }
  }
}
