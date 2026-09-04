import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

import { AdminActionMenuComponent } from '../components/admin-action-menu.component';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInput } from '../../../components/input/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { AdminBranch } from '../models/admin-branch.model';
import { AdminBranchService } from '../services/admin-branch.service';
import { AdminProvider, ProviderStatus } from '../models/admin-provider.model';
import { AdminProviderService } from '../services/admin-provider.service';

@Component({
  selector: 'app-admin-provider-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HlmButton, HlmInput, AdminActionMenuComponent, ...HlmCardImports, ...HlmFieldImports],
  templateUrl: './admin-provider-page.component.html',
})
export class AdminProviderPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly providerApi = inject(AdminProviderService);
  private readonly branchApi = inject(AdminBranchService);

  protected readonly providers = signal<AdminProvider[]>([]);
  protected readonly branches = signal<AdminBranch[]>([]);
  protected readonly errorMessage = signal('');
  protected readonly successMessage = signal('');
  protected readonly loading = signal(false);
  protected readonly modalOpen = signal(false);
  protected readonly modalMode = signal<'create' | 'edit'>('create');
  protected readonly editingProviderId = signal<string | null>(null);
  protected readonly deleteConfirmOpen = signal(false);
  protected readonly deletingProvider = signal<AdminProvider | null>(null);
  protected readonly openMenuId = signal<string | null>(null);

  protected readonly form = this.fb.nonNullable.group({
    business_name: ['', [Validators.required]],
    contact_name: ['', [Validators.required]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.minLength(6)]],
    gender: ['masculino', [Validators.required]],
    phone: [''],
    branch_id: [''],
    status: ['active', [Validators.required]],
    is_active: [true],
  });

  constructor() {
    void this.loadData();
  }

  protected openModal(): void {
    this.modalMode.set('create');
    this.editingProviderId.set(null);
    this.form.reset({
      business_name: '',
      contact_name: '',
      email: '',
      password: '',
      gender: 'masculino',
      phone: '',
      branch_id: '',
      status: 'active',
      is_active: true,
    });
    this.errorMessage.set('');
    this.successMessage.set('');
    this.modalOpen.set(true);
  }

  protected editProvider(provider: AdminProvider): void {
    this.modalMode.set('edit');
    this.editingProviderId.set(provider.id);
    this.form.reset({
      business_name: provider.business_name,
      contact_name: provider.contact_name,
      email: provider.email,
      password: '',
      gender: provider.gender,
      phone: provider.phone || '',
      branch_id: provider.branch_id || '',
      status: provider.status,
      is_active: provider.is_active,
    });
    this.errorMessage.set('');
    this.successMessage.set('');
    this.modalOpen.set(true);
  }

  protected closeModal(): void {
    this.modalOpen.set(false);
  }

  protected closeMenu(): void {
    this.openMenuId.set(null);
  }

  protected toggleMenu(providerId: string): void {
    this.openMenuId.set(this.openMenuId() === providerId ? null : providerId);
  }

  protected async toggleActive(provider: AdminProvider): Promise<void> {
    this.closeMenu();
    try {
      await firstValueFrom(this.providerApi.updateProviderActive(provider.id, { is_active: !provider.is_active }));
      await this.loadData();
      this.successMessage.set(`Proveedor ${!provider.is_active ? 'activado' : 'desactivado'} correctamente.`);
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo actualizar el estado del proveedor.'));
    }
  }

  protected askDelete(provider: AdminProvider): void {
    this.closeMenu();
    this.deletingProvider.set(provider);
    this.deleteConfirmOpen.set(true);
  }

  protected cancelDelete(): void {
    this.deleteConfirmOpen.set(false);
    this.deletingProvider.set(null);
  }

  protected async confirmDelete(): Promise<void> {
    const provider = this.deletingProvider();
    if (!provider) return;

    try {
      await firstValueFrom(this.providerApi.deleteProvider(provider.id));
      await this.loadData();
      this.successMessage.set('Proveedor eliminado correctamente.');
      this.cancelDelete();
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo eliminar el proveedor.'));
    }
  }

  protected async submit(): Promise<void> {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');
    try {
      const payload = this.form.getRawValue();
      const request = {
        business_name: payload.business_name,
        contact_name: payload.contact_name,
        email: payload.email,
        password: payload.password || null,
        gender: payload.gender as 'masculino' | 'femenino',
        phone: payload.phone || null,
        branch_id: payload.branch_id || null,
        status: payload.status as ProviderStatus,
        is_active: payload.is_active,
      };

      if (this.modalMode() === 'edit' && this.editingProviderId()) {
        await firstValueFrom(this.providerApi.updateProvider(this.editingProviderId()!, request));
        this.successMessage.set('Proveedor actualizado correctamente.');
      } else {
        if (!payload.password) {
          throw new Error('La contraseña es obligatoria para crear un proveedor.');
        }
        await firstValueFrom(
          this.providerApi.createProvider({
            business_name: request.business_name,
            contact_name: request.contact_name,
            email: request.email,
            password: payload.password,
            gender: request.gender,
            phone: request.phone,
            branch_id: request.branch_id,
          }),
        );
        this.successMessage.set('Proveedor creado correctamente.');
      }

      this.form.reset({ business_name: '', contact_name: '', email: '', password: '', gender: 'masculino', phone: '', branch_id: '', status: 'active', is_active: true });
      await this.loadData();
      this.closeModal();
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo guardar el proveedor.'));
    } finally {
      this.loading.set(false);
    }
  }

  protected async updateStatus(provider: AdminProvider, status: ProviderStatus): Promise<void> {
    if (provider.status === status) {
      return;
    }

    this.errorMessage.set('');
    this.successMessage.set('');
    try {
      await firstValueFrom(this.providerApi.updateProviderStatus(provider.id, status));
      await this.loadData();
      this.successMessage.set('Estado del proveedor actualizado.');
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo actualizar el proveedor.'));
    }
  }

  protected branchName(branchId: string | null): string {
    if (!branchId) {
      return 'Sin sucursal';
    }

    return this.branches().find((branch) => branch.id === branchId)?.name ?? branchId;
  }

  protected statusLabel(status: ProviderStatus): string {
    return status === 'active' ? 'Activo' : 'Suspendido';
  }

  protected isActiveLabel(provider: AdminProvider): string {
    return provider.is_active ? 'Activo' : 'Inactivo';
  }

  private async loadData(): Promise<void> {
    try {
      const [providersResponse, branchesResponse] = await Promise.all([
        firstValueFrom(this.providerApi.listProviders()),
        firstValueFrom(this.branchApi.listBranches()),
      ]);

      this.providers.set(providersResponse.data ?? []);
      this.branches.set(branchesResponse.data ?? []);
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudieron cargar los proveedores.'));
    }
  }
}
