import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

import { toast } from '@spartan-ng/brain/sonner';

import { AdminActionMenuComponent } from '../components/admin-action-menu.component';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInput } from '../../../components/input/src';
import { HlmSelectImports } from '../../../components/select/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { requestWithToast } from '../../../core/utils/request-toast.util';
import { AdminBranch } from '../models/admin-branch.model';
import { AdminBranchService } from '../services/admin-branch.service';
import { AdminProvider, ProviderStatus } from '../models/admin-provider.model';
import { AdminProviderService } from '../services/admin-provider.service';

@Component({
  selector: 'app-admin-provider-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HlmButton, HlmInput, AdminActionMenuComponent, ...HlmCardImports, ...HlmFieldImports, ...HlmSelectImports],
  templateUrl: './admin-provider-page.component.html',
})
export class AdminProviderPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly providerApi = inject(AdminProviderService);
  private readonly branchApi = inject(AdminBranchService);

  protected readonly providers = signal<AdminProvider[]>([]);
  protected readonly branches = signal<AdminBranch[]>([]);
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
  });

  protected normalizeEmailInput(event: Event): void {
    const input = event.target as HTMLInputElement | null;
    if (!input) return;

    const value = input.value.trim().toLowerCase();
    this.form.controls.email.setValue(value, { emitEvent: false });
  }

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
    });
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
    });
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
      await requestWithToast(
        this.providerApi.deleteProvider(provider.id),
        { loading: 'Eliminando proveedor...', success: 'Proveedor eliminado correctamente.', error: 'No se pudo eliminar el proveedor.' },
      );
      await this.loadData();
      this.cancelDelete();
    } catch {
      // El toast de error ya se mostró con requestWithToast
    }
  }

  protected async submit(): Promise<void> {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    try {
      const payload = this.form.getRawValue();
      const request = {
        business_name: payload.business_name,
        contact_name: payload.contact_name,
        email: payload.email.trim().toLowerCase(),
        gender: payload.gender as 'masculino' | 'femenino',
        phone: payload.phone || null,
        branch_id: payload.branch_id || null,
        status: payload.status as ProviderStatus,
      };

      if (this.modalMode() === 'edit' && this.editingProviderId()) {
        await requestWithToast(
          this.providerApi.updateProvider(this.editingProviderId()!, request),
          { loading: 'Guardando proveedor...', success: 'Proveedor actualizado correctamente.', error: 'No se pudo guardar el proveedor.' },
        );
      } else {
        if (!payload.password) {
          toast.warning('La contraseña es obligatoria para crear un proveedor.');
          return;
        }
        await requestWithToast(
          this.providerApi.createProvider({
            business_name: request.business_name,
            contact_name: request.contact_name,
            email: request.email,
            password: payload.password,
            gender: request.gender,
            phone: request.phone,
            branch_id: request.branch_id,
          }),
          { loading: 'Guardando proveedor...', success: 'Proveedor creado correctamente.', error: 'No se pudo guardar el proveedor.' },
        );
      }

      this.form.reset({ business_name: '', contact_name: '', email: '', password: '', gender: 'masculino', phone: '', branch_id: '', status: 'active' });
      await this.loadData();
      this.closeModal();
    } catch {
      // El toast de error ya se mostró con requestWithToast
    } finally {
      this.loading.set(false);
    }
  }

  protected async updateStatus(provider: AdminProvider, status: ProviderStatus): Promise<void> {
    if (provider.status === status) {
      return;
    }

    try {
      await requestWithToast(
        this.providerApi.updateProviderStatus(provider.id, status),
        { loading: 'Actualizando estado...', success: 'Estado del proveedor actualizado.', error: 'No se pudo actualizar el proveedor.' },
      );
      await this.loadData();
    } catch {
      // El toast de error ya se mostró con requestWithToast
    }
  }

  protected async toggleStatus(provider: AdminProvider): Promise<void> {
    this.closeMenu();
    await this.updateStatus(provider, provider.status === 'active' ? 'suspended' : 'active');
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

  private async loadData(): Promise<void> {
    try {
      const [providersResponse, branchesResponse] = await Promise.all([
        firstValueFrom(this.providerApi.listProviders()),
        firstValueFrom(this.branchApi.listBranches()),
      ]);

      this.providers.set(providersResponse.data ?? []);
      this.branches.set(branchesResponse.data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar los proveedores.'));
    }
  }
}
