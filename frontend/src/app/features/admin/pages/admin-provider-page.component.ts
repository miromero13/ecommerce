import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

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
  imports: [CommonModule, ReactiveFormsModule, HlmButton, HlmInput, ...HlmCardImports, ...HlmFieldImports],
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

  protected readonly form = this.fb.nonNullable.group({
    business_name: ['', [Validators.required]],
    contact_name: ['', [Validators.required]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
    gender: ['masculino', [Validators.required]],
    phone: [''],
    branch_id: [''],
  });

  constructor() {
    void this.loadData();
  }

  protected openModal(): void {
    this.errorMessage.set('');
    this.successMessage.set('');
    this.modalOpen.set(true);
  }

  protected closeModal(): void {
    this.modalOpen.set(false);
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
      await firstValueFrom(
        this.providerApi.createProvider({
          business_name: payload.business_name,
          contact_name: payload.contact_name,
          email: payload.email,
          password: payload.password,
          gender: payload.gender as 'masculino' | 'femenino',
          phone: payload.phone || null,
          branch_id: payload.branch_id || null,
        }),
      );
      this.form.reset({ business_name: '', contact_name: '', email: '', password: '', gender: 'masculino', phone: '', branch_id: '' });
      await this.loadData();
      this.successMessage.set('Proveedor creado correctamente.');
      this.closeModal();
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo crear el proveedor.'));
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
