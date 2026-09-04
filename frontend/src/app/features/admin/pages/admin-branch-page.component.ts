import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

import { AdminActionMenuComponent } from '../components/admin-action-menu.component';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInput } from '../../../components/input/src';
import { AdminBranch } from '../models/admin-branch.model';
import { AdminBranchService } from '../services/admin-branch.service';
import { getErrorMessage } from '../../../core/utils/http-error.util';

@Component({
  selector: 'app-admin-branch-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HlmButton, HlmInput, AdminActionMenuComponent, ...HlmCardImports, ...HlmFieldImports],
  templateUrl: './admin-branch-page.component.html',
})
export class AdminBranchPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(AdminBranchService);

  protected readonly branches = signal<AdminBranch[]>([]);
  protected readonly errorMessage = signal('');
  protected readonly successMessage = signal('');
  protected readonly loading = signal(false);
  protected readonly modalOpen = signal(false);
  protected readonly modalMode = signal<'create' | 'edit'>('create');
  protected readonly editingBranchId = signal<string | null>(null);
  protected readonly deleteConfirmOpen = signal(false);
  protected readonly deletingBranch = signal<AdminBranch | null>(null);
  protected readonly openMenuId = signal<string | null>(null);

  protected readonly form = this.fb.nonNullable.group({
    name: ['', [Validators.required]],
    city: ['', [Validators.required]],
    is_default: [false],
    is_active: [true],
  });

  constructor() {
    void this.loadBranches();
  }

  protected openModal(): void {
    this.modalMode.set('create');
    this.editingBranchId.set(null);
    this.form.reset({ name: '', city: '', is_default: false, is_active: true });
    this.errorMessage.set('');
    this.successMessage.set('');
    this.modalOpen.set(true);
  }

  protected editBranch(branch: AdminBranch): void {
    this.modalMode.set('edit');
    this.editingBranchId.set(branch.id);
    this.form.reset({ name: branch.name, city: branch.city, is_default: branch.is_default, is_active: branch.is_active });
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

  protected toggleMenu(branchId: string): void {
    this.openMenuId.set(this.openMenuId() === branchId ? null : branchId);
  }

  protected async toggleActive(branch: AdminBranch): Promise<void> {
    this.closeMenu();
    try {
      await firstValueFrom(this.api.updateBranchActive(branch.id, { is_active: !branch.is_active }));
      await this.loadBranches();
      this.successMessage.set(`Sucursal ${!branch.is_active ? 'activada' : 'desactivada'} correctamente.`);
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo actualizar el estado de la sucursal.'));
    }
  }

  protected askDelete(branch: AdminBranch): void {
    this.closeMenu();
    this.deletingBranch.set(branch);
    this.deleteConfirmOpen.set(true);
  }

  protected cancelDelete(): void {
    this.deleteConfirmOpen.set(false);
    this.deletingBranch.set(null);
  }

  protected async confirmDelete(): Promise<void> {
    const branch = this.deletingBranch();
    if (!branch) return;

    try {
      await firstValueFrom(this.api.deleteBranch(branch.id));
      await this.loadBranches();
      this.successMessage.set('Sucursal eliminada correctamente.');
      this.cancelDelete();
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo eliminar la sucursal.'));
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
      if (this.modalMode() === 'edit' && this.editingBranchId()) {
        await firstValueFrom(this.api.updateBranch(this.editingBranchId()!, payload));
        this.successMessage.set('Sucursal actualizada correctamente.');
      } else {
        await firstValueFrom(this.api.createBranch(payload));
        this.successMessage.set('Sucursal creada correctamente.');
      }
      this.form.reset({ name: '', city: '', is_default: false, is_active: true });
      await this.loadBranches();
      this.closeModal();
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo guardar la sucursal.'));
    } finally {
      this.loading.set(false);
    }
  }

  private async loadBranches(): Promise<void> {
    try {
      const response = await firstValueFrom(this.api.listBranches());
      this.branches.set(response.data ?? []);
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudieron cargar las sucursales.'));
    }
  }
}
