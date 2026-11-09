import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

import { toast } from '@spartan-ng/brain/sonner';

import { AdminActionMenuComponent } from '../components/admin-action-menu.component';
import { AdminUsuario } from '../models/admin-user.model';
import { AdminUserService } from '../services/admin-user.service';
import { SessionService } from '../../shared/services/session.service';
import { RbacApiService } from '../../shared/services/rbac-api.service';
import { Role } from '../../shared/models/rbac.model';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { requestWithToast } from '../../../core/utils/request-toast.util';
import { HlmTable } from '@spartan-ng/helm/table';
import { AdminBranch } from '../models/admin-branch.model';
import { AdminBranchService } from '../services/admin-branch.service';
import { HlmTabsImports } from '../../../components/tabs/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInput } from '../../../components/input/src';
import { HlmSelectImports } from '../../../components/select/src';

export interface RoleOption {
  id: string;
  name: string;
  baseRol: Exclude<AdminUsuario['rol'], 'cliente' | 'proveedor'>;
  customRoleId?: string;
  requiresBranch: boolean;
}

@Component({
  selector: 'app-admin-user-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HlmTable, HlmButton, HlmInput, AdminActionMenuComponent, ...HlmTabsImports, ...HlmCardImports, ...HlmFieldImports, ...HlmSelectImports],
  templateUrl: './admin-user-page.component.html',
})
export class AdminUserPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(AdminUserService);
  private readonly branchApi = inject(AdminBranchService);
  private readonly rbacApi = inject(RbacApiService);
  private readonly session = inject(SessionService);

  protected readonly usuarios = signal<AdminUsuario[]>([]);
  protected readonly usuariosFiltrados = signal<AdminUsuario[]>([]);
  protected readonly branches = signal<AdminBranch[]>([]);
  protected readonly availableRoles = signal<Role[]>([]);
  protected readonly filtroRol = signal<'' | AdminUsuario['rol']>('');
  protected readonly currentUserId = signal(this.session.user()?.id ?? '');
  protected readonly openMenuId = signal<string | null>(null);
  protected readonly modalOpen = signal(false);
  protected readonly modalMode = signal<'create' | 'edit'>('edit');
  protected readonly editingUserId = signal<string | null>(null);
  protected readonly editingUser = signal<AdminUsuario | null>(null);
  protected readonly deleteConfirmOpen = signal(false);
  protected readonly deletingUser = signal<AdminUsuario | null>(null);

  protected readonly roleOptions = computed<RoleOption[]>(() => {
    const options: RoleOption[] = [
      { id: 'administrador', name: 'Administrador', baseRol: 'administrador', requiresBranch: false },
      { id: 'encargado', name: 'Encargado de Sucursal', baseRol: 'encargado', requiresBranch: true },
      { id: 'cajero', name: 'Cajero', baseRol: 'cajero', requiresBranch: true },
    ];

    for (const r of this.availableRoles()) {
      if (!r.is_system) {
        options.push({
          id: r.id,
          name: r.name,
          baseRol: 'cajero',
          customRoleId: r.id,
          requiresBranch: true,
        });
      }
    }
    return options;
  });

  protected readonly genderSelectLabel = (gender: string | null | undefined): string => {
    if (!gender) return 'Género';
    return this.labelGenero(gender as AdminUsuario['gender']);
  };

  protected readonly roleSelectLabel = (roleKey: string | null | undefined): string => {
    if (!roleKey) return 'Selecciona un rol';
    const match = this.roleOptions().find((opt) => opt.id === roleKey);
    return match ? match.name : roleKey;
  };

  protected readonly branchSelectLabel = (branchId: string | null | undefined): string => {
    if (!branchId) return 'Sin sucursal';
    const branch = this.branches().find((item) => item.id === branchId);
    return branch ? `${branch.name} - ${branch.city}` : branchId;
  };

  protected readonly activeSelectLabel = (value: boolean | null | undefined): string => (value ? 'Activo' : 'Inactivo');

  protected readonly userForm = this.fb.nonNullable.group({
    name: ['', [Validators.required]],
    email: ['', [Validators.required, Validators.email]],
    password: [''],
    gender: ['masculino', [Validators.required]],
    selected_role: ['administrador', [Validators.required]],
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

  protected openCreateModal(): void {
    this.closeMenu();
    this.modalMode.set('create');
    this.editingUserId.set(null);
    this.editingUser.set(null);
    this.userForm.reset({
      name: '',
      email: '',
      password: '',
      gender: 'masculino',
      selected_role: 'administrador',
      branch_id: '',
      is_active: true,
    });
    this.modalOpen.set(true);
  }

  protected openEditModal(user: AdminUsuario): void {
    if (this.currentUserId() === user.id) {
      return;
    }
    this.closeMenu();
    this.modalMode.set('edit');
    this.editingUserId.set(user.id);
    this.editingUser.set(user);
    const selectedRole = user.custom_roles && user.custom_roles.length > 0
      ? user.custom_roles[0].id
      : user.rol;
    this.userForm.reset({
      name: user.name,
      email: user.email,
      password: '',
      gender: user.gender,
      selected_role: selectedRole,
      branch_id: user.rol === 'administrador' ? '' : (user.branch_id || ''),
      is_active: user.is_active,
    });
    this.modalOpen.set(true);
  }

  protected closeModal(): void {
    this.modalOpen.set(false);
    this.editingUser.set(null);
    this.modalMode.set('edit');
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
      await requestWithToast(
        this.api.updateUsuarioActive(user.id, { is_active: !user.is_active }),
        { loading: 'Actualizando estado...', success: `Usuario ${!user.is_active ? 'activado' : 'desactivado'} correctamente.`, error: 'No se pudo actualizar el estado del usuario.' },
      );
      await this.loadData();
    } catch {
      // El toast de error ya se mostró con requestWithToast
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
      await requestWithToast(
        this.api.deleteUsuario(user.id),
        { loading: 'Eliminando usuario...', success: 'Usuario eliminado correctamente.', error: 'No se pudo eliminar el usuario.' },
      );
      await this.loadData();
      this.cancelDelete();
    } catch {
      // El toast de error ya se mostró con requestWithToast
    }
  }

  // [CU03 - Secuencia: Paso 3] El Administrador del tenant ejecuta submitUser() en AdminUserPageComponent
  protected async submitUser(): Promise<void> {
    if (this.userForm.invalid || (!this.isCreateMode() && !this.editingUserId())) {
      this.userForm.markAllAsTouched();
      return;
    }

    try {
      const payload = this.userForm.getRawValue();
      const roleOpt = this.roleOptions().find((opt) => opt.id === payload.selected_role);
      const baseRol = roleOpt?.baseRol ?? 'cajero';
      const customRoleId = roleOpt?.customRoleId ?? null;

      if (this.modalMode() === 'create') {
        if (payload.password.length < 8) {
          toast.error('La contraseña debe tener al menos 8 caracteres.');
          return;
        }

        await requestWithToast(
          this.api.createUsuario({
            name: payload.name,
            email: payload.email.trim().toLowerCase(),
            password: payload.password,
            gender: payload.gender as AdminUsuario['gender'],
            rol: baseRol,
            role_id: customRoleId,
            branch_id: this.roleRequiresBranch() ? (payload.branch_id || null) : null,
            is_active: payload.is_active,
          }),
          { loading: 'Creando usuario...', success: 'Usuario creado correctamente.', error: 'No se pudo crear el usuario.' },
        );
      } else {
        await requestWithToast(
          this.api.updateUsuario(this.editingUserId()!, {
            name: payload.name,
            email: payload.email.trim().toLowerCase(),
            gender: payload.gender as AdminUsuario['gender'],
            rol: baseRol,
            role_id: customRoleId,
            branch_id: this.roleRequiresBranch() ? (payload.branch_id || null) : null,
            is_active: payload.is_active,
          }),
          { loading: 'Guardando usuario...', success: 'Usuario actualizado correctamente.', error: 'No se pudo actualizar el usuario.' },
        );
      }
      await this.loadData();
      this.closeModal();
    } catch {
      // El toast de error ya se mostró con requestWithToast
    }
  }

  protected isCreateMode(): boolean {
    return this.modalMode() === 'create';
  }

  protected roleRequiresBranch(): boolean {
    const currentKey = this.userForm.controls.selected_role.value;
    const match = this.roleOptions().find((opt) => opt.id === currentKey);
    return match ? match.requiresBranch : false;
  }

  protected branchName(branchId: string | null, role?: AdminUsuario['rol']): string {
    if (role === 'administrador') {
      return 'Global';
    }

    if (!branchId) {
      return 'Sin sucursal';
    }

    return this.branches().find((branch) => branch.id === branchId)?.name ?? branchId;
  }

  private async loadData(): Promise<void> {
    try {
      const [usersResponse, branchesResponse, rolesResponse] = await Promise.all([
        firstValueFrom(this.api.listUsuarios()),
        firstValueFrom(this.branchApi.listBranches()),
        firstValueFrom(this.rbacApi.getRoles()),
      ]);

      this.usuarios.set(usersResponse.data ?? []);
      this.branches.set(branchesResponse.data ?? []);
      this.availableRoles.set(rolesResponse.data ?? []);
      this.applyFiltro();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar los usuarios.'));
    }
  }

  private applyFiltro(): void {
    const filtro = this.filtroRol();
    const all = this.usuarios();
    this.usuariosFiltrados.set(filtro ? all.filter((u) => u.rol === filtro) : all);
  }

  protected getUserRoleLabel(user: AdminUsuario): string {
    if (user.custom_roles && user.custom_roles.length > 0) {
      return user.custom_roles[0].name;
    }
    return this.labelRol(user.rol);
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

  protected activeLabel(user: AdminUsuario): string {
    return user.is_active ? 'Activo' : 'Inactivo';
  }
}
