import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { AdminUsuario } from '../models/admin-user.model';
import { AdminUserService } from '../services/admin-user.service';
import { SessionService } from '../../shared/services/session.service';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { HlmTable } from '@spartan-ng/helm/table';
import { AdminBranch } from '../models/admin-branch.model';
import { AdminBranchService } from '../services/admin-branch.service';
import { HlmTabsImports } from '../../../components/tabs/src';

@Component({
  selector: 'app-admin-user-page',
  standalone: true,
  imports: [CommonModule, HlmTable, ...HlmTabsImports],
  templateUrl: './admin-user-page.component.html',
})
export class AdminUserPageComponent {
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
}
