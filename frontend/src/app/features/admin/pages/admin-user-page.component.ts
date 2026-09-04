import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

import { AdminActionMenuComponent } from '../components/admin-action-menu.component';
import { AdminUsuario } from '../models/admin-user.model';
import { AdminUserService } from '../services/admin-user.service';
import { SessionService } from '../../shared/services/session.service';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { HlmTable } from '@spartan-ng/helm/table';
import { AdminBranch } from '../models/admin-branch.model';
import { AdminBranchService } from '../services/admin-branch.service';
import { HlmTabsImports } from '../../../components/tabs/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInput } from '../../../components/input/src';

@Component({
  selector: 'app-admin-user-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HlmTable, HlmButton, HlmInput, AdminActionMenuComponent, ...HlmTabsImports, ...HlmCardImports, ...HlmFieldImports],
  templateUrl: './admin-user-page.component.html',
})
export class AdminUserPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(AdminUserService);
  private readonly branchApi = inject(AdminBranchService);
  private readonly session = inject(SessionService);

  protected readonly usuarios = signal<AdminUsuario[]>([]);
  protected readonly usuariosFiltrados = signal<AdminUsuario[]>([]);
  protected readonly branches = signal<AdminBranch[]>([]);
  protected readonly filtroRol = signal<'' | AdminUsuario['rol']>('');
  protected readonly errorMessage = signal('');
  protected readonly successMessage = signal('');
  protected readonly currentUserId = signal(this.session.user()?.id ?? '');
  protected readonly openMenuId = signal<string | null>(null);
  protected readonly modalOpen = signal(false);
  protected readonly modalMode = signal<'edit'>('edit');
  protected readonly editingUserId = signal<string | null>(null);
  protected readonly deleteConfirmOpen = signal(false);
  protected readonly deletingUser = signal<AdminUsuario | null>(null);

  protected readonly userForm = this.fb.nonNullable.group({
    name: ['', [Validators.required]],
    email: ['', [Validators.required, Validators.email]],
    gender: ['masculino', [Validators.required]],
    branch_id: [''],
    is_active: [true],
  });

  protected normalizeEmailInput(event: Event): void {
    const input = event.target as HTMLInputElement | null;
    if (!input) return;

    const value = input.value.trim().toLowerCase();
    this.userForm.controls.email.setValue(value, { emitEvent: false });
  }

  constructor() {
    void this.loadData();
  }

  protected setFiltro(rol: '' | AdminUsuario['rol']): void {
    this.filtroRol.set(rol);
    this.applyFiltro();
  }

  protected selectFiltro(tab: string): void {
    this.setFiltro(tab === 'todos' ? '' : (tab as AdminUsuario['rol']));
  }

  protected async actualizarRol(user: AdminUsuario, rol: AdminUsuario['rol']): Promise<void> {
    if (user.rol === rol || this.currentUserId() === user.id) {
      return;
    }

    this.errorMessage.set('');
    this.successMessage.set('');
    try {
      await firstValueFrom(this.api.updateUsuarioRol(user.id, rol));
      await this.loadData();
      this.successMessage.set('Rol de usuario actualizado correctamente.');
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo actualizar el rol del usuario.'));
    }
  }

  protected async actualizarBranch(user: AdminUsuario, branchId: string): Promise<void> {
    if (this.currentUserId() === user.id) {
      return;
    }

    this.errorMessage.set('');
    this.successMessage.set('');
    try {
      await firstValueFrom(this.api.updateUsuarioBranch(user.id, branchId || null));
      await this.loadData();
      this.successMessage.set('Sucursal de usuario actualizada correctamente.');
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo actualizar la sucursal del usuario.'));
    }
  }

  protected openEditModal(user: AdminUsuario): void {
    if (this.currentUserId() === user.id) {
      return;
    }
    this.closeMenu();
    this.editingUserId.set(user.id);
    this.userForm.reset({
      name: user.name,
      email: user.email,
      gender: user.gender,
      branch_id: user.branch_id || '',
      is_active: user.is_active,
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

  protected toggleMenu(userId: string): void {
    this.openMenuId.set(this.openMenuId() === userId ? null : userId);
  }

  protected async toggleActive(user: AdminUsuario): Promise<void> {
    if (this.currentUserId() === user.id) {
      return;
    }
    this.closeMenu();
    try {
      await firstValueFrom(this.api.updateUsuarioActive(user.id, { is_active: !user.is_active }));
      await this.loadData();
      this.successMessage.set(`Usuario ${!user.is_active ? 'activado' : 'desactivado'} correctamente.`);
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo actualizar el estado del usuario.'));
    }
  }

  protected askDelete(user: AdminUsuario): void {
    if (this.currentUserId() === user.id) {
      return;
    }
    this.closeMenu();
    this.deletingUser.set(user);
    this.deleteConfirmOpen.set(true);
  }

  protected cancelDelete(): void {
    this.deleteConfirmOpen.set(false);
    this.deletingUser.set(null);
  }

  protected async confirmDelete(): Promise<void> {
    const user = this.deletingUser();
    if (!user) return;

    try {
      await firstValueFrom(this.api.deleteUsuario(user.id));
      await this.loadData();
      this.successMessage.set('Usuario eliminado correctamente.');
      this.cancelDelete();
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo eliminar el usuario.'));
    }
  }

  protected async submitUser(): Promise<void> {
    if (this.userForm.invalid || !this.editingUserId()) {
      this.userForm.markAllAsTouched();
      return;
    }

    this.errorMessage.set('');
    this.successMessage.set('');
    try {
      const payload = this.userForm.getRawValue();
      await firstValueFrom(this.api.updateUsuario(this.editingUserId()!, {
        name: payload.name,
        email: payload.email.trim().toLowerCase(),
        gender: payload.gender as AdminUsuario['gender'],
        branch_id: payload.branch_id || null,
        is_active: payload.is_active,
      }));
      await this.loadData();
      this.successMessage.set('Usuario actualizado correctamente.');
      this.closeModal();
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo actualizar el usuario.'));
    }
  }

  protected branchName(branchId: string | null): string {
    if (!branchId) {
      return 'Sin sucursal';
    }

    return this.branches().find((branch) => branch.id === branchId)?.name ?? branchId;
  }

  private async loadData(): Promise<void> {
    this.errorMessage.set('');
    try {
      const [usersResponse, branchesResponse] = await Promise.all([
        firstValueFrom(this.api.listUsuarios()),
        firstValueFrom(this.branchApi.listBranches()),
      ]);

      this.usuarios.set(usersResponse.data ?? []);
      this.branches.set(branchesResponse.data ?? []);
      this.applyFiltro();
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudieron cargar los usuarios.'));
    }
  }

  private applyFiltro(): void {
    const filtro = this.filtroRol();
    const all = this.usuarios();
    this.usuariosFiltrados.set(filtro ? all.filter((u) => u.rol === filtro) : all);
  }

  protected labelRol(rol: AdminUsuario['rol']): string {
    switch (rol) {
      case 'administrador':
        return 'Administrador';
      case 'cliente':
        return 'Cliente';
      case 'proveedor':
        return 'Proveedor';
      case 'encargado':
        return 'Encargado';
      case 'cajero':
        return 'Cajero';
      case 'delivery':
        return 'Delivery';
      default:
        return rol;
    }
  }

  protected labelGenero(gender: AdminUsuario['gender']): string {
    switch (gender) {
      case 'masculino':
        return 'Masculino';
      case 'femenino':
        return 'Femenino';
      default:
        return gender;
    }
  }

  protected canAssignBranch(user: AdminUsuario): boolean {
    return user.rol === 'administrador' || user.rol === 'encargado' || user.rol === 'cajero';
  }

  protected activeLabel(user: AdminUsuario): string {
    return user.is_active ? 'Activo' : 'Inactivo';
  }
}
