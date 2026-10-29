import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

import { toast } from '@spartan-ng/brain/sonner';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInput } from '../../../components/input/src';
import { HlmBadge } from '../../../components/badge/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { Permission, Role, RoleCreate, RoleUpdate } from '../../shared/models/rbac.model';
import { RbacApiService } from '../../shared/services/rbac-api.service';
import { AdminUserService } from '../services/admin-user.service';
import { AdminUsuario } from '../models/admin-user.model';

@Component({
  selector: 'app-rbac-roles-page',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    HlmButton,
    HlmInput,
    ...HlmCardImports,
    ...HlmFieldImports,
  ],
  templateUrl: './rbac-roles-page.component.html',
})
export class RbacRolesPageComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly rbacApi = inject(RbacApiService);
  private readonly userApi = inject(AdminUserService);

  protected readonly roles = signal<Role[]>([]);
  protected readonly permissions = signal<Permission[]>([]);
  protected readonly users = signal<AdminUsuario[]>([]);
  protected readonly isLoading = signal(false);

  // Modal create/edit role
  protected readonly isModalOpen = signal(false);
  protected readonly modalMode = signal<'create' | 'edit'>('create');
  protected readonly editingRoleId = signal<string | null>(null);
  protected readonly selectedPermissionIds = signal<Set<string>>(new Set());

  // User assignment section
  protected readonly selectedUserId = signal<string>('');
  protected readonly selectedUserRoles = signal<Set<string>>(new Set());
  protected readonly isAssigning = signal(false);

  protected readonly roleForm = this.fb.group({
    name: ['', [Validators.required, Validators.maxLength(100)]],
    code: ['', [Validators.required, Validators.maxLength(64)]],
  });

  // Group permissions by module
  protected readonly permissionsByModule = computed(() => {
    const map = new Map<string, Permission[]>();
    for (const p of this.permissions()) {
      const list = map.get(p.module) ?? [];
      list.push(p);
      map.set(p.module, list);
    }
    return Array.from(map.entries()).map(([module, perms]) => ({
      module,
      moduleLabel: this.getModuleLabel(module),
      permissions: perms,
    }));
  });

  async ngOnInit(): Promise<void> {
    await this.loadData();
  }

  async loadData(): Promise<void> {
    this.isLoading.set(true);
    try {
      const [permsRes, rolesRes, usersRes] = await Promise.all([
        firstValueFrom(this.rbacApi.getPermissions()),
        firstValueFrom(this.rbacApi.getRoles()),
        firstValueFrom(this.userApi.listUsuarios()),
      ]);

      this.permissions.set(permsRes.data ?? []);
      this.roles.set(rolesRes.data ?? []);
      // Only company staff can get custom roles (administrators already have every permission).
      this.users.set((usersRes.data ?? []).filter((user) => ['encargado', 'cajero', 'proveedor'].includes(user.rol)));
    } catch (err) {
      toast.error(getErrorMessage(err, 'No se pudo cargar la información de roles y permisos'));
    } finally {
      this.isLoading.set(false);
    }
  }

  openCreateModal(): void {
    this.modalMode.set('create');
    this.editingRoleId.set(null);
    this.roleForm.reset({ name: '', code: '' });
    this.roleForm.get('code')?.enable();
    this.selectedPermissionIds.set(new Set());
    this.isModalOpen.set(true);
  }

  openEditModal(role: Role): void {
    if (role.is_system) {
      toast.error('No se pueden modificar roles del sistema');
      return;
    }
    this.modalMode.set('edit');
    this.editingRoleId.set(role.id);
    this.roleForm.reset({ name: role.name, code: role.code });
    this.roleForm.get('code')?.disable();
    const permIds = new Set(role.permissions.map((p) => p.id));
    this.selectedPermissionIds.set(permIds);
    this.isModalOpen.set(true);
  }

  closeModal(): void {
    this.isModalOpen.set(false);
  }

  togglePermission(permId: string): void {
    const updated = new Set(this.selectedPermissionIds());
    if (updated.has(permId)) {
      updated.delete(permId);
    } else {
      updated.add(permId);
    }
    this.selectedPermissionIds.set(updated);
  }

  toggleModule(modulePerms: Permission[]): void {
    const updated = new Set(this.selectedPermissionIds());
    const allSelected = modulePerms.every((p) => updated.has(p.id));
    for (const p of modulePerms) {
      if (allSelected) {
        updated.delete(p.id);
      } else {
        updated.add(p.id);
      }
    }
    this.selectedPermissionIds.set(updated);
  }

  isModuleAllSelected(modulePerms: Permission[]): boolean {
    return modulePerms.every((p) => this.selectedPermissionIds().has(p.id));
  }

  async saveRole(): Promise<void> {
    if (this.roleForm.invalid) {
      this.roleForm.markAllAsTouched();
      return;
    }
    const permIds = Array.from(this.selectedPermissionIds());
    if (permIds.length === 0) {
      toast.error('Debe asignar al menos un permiso al rol');
      return;
    }

    const { name, code } = this.roleForm.getRawValue();

    try {
      if (this.modalMode() === 'create') {
        const payload: RoleCreate = {
          name: name?.trim() ?? '',
          code: code?.trim().toLowerCase() ?? '',
          permission_ids: permIds,
        };
        const res = await firstValueFrom(this.rbacApi.createRole(payload));
        toast.success(res.message);
      } else {
        const roleId = this.editingRoleId();
        if (!roleId) return;
        const payload: RoleUpdate = {
          name: name?.trim(),
          permission_ids: permIds,
        };
        const res = await firstValueFrom(this.rbacApi.updateRole(roleId, payload));
        toast.success(res.message);
      }

      this.closeModal();
      await this.loadData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Error al guardar el rol'));
    }
  }

  onSelectUser(userId: string): void {
    this.selectedUserId.set(userId);
    // User custom roles
    const user = this.users().find((u) => u.id === userId);
    // Find matching roles from custom_roles if available, or reset
    this.selectedUserRoles.set(new Set());
  }

  toggleUserRole(roleId: string): void {
    const updated = new Set(this.selectedUserRoles());
    if (updated.has(roleId)) {
      updated.delete(roleId);
    } else {
      updated.add(roleId);
    }
    this.selectedUserRoles.set(updated);
  }

  async saveUserRoles(): Promise<void> {
    const userId = this.selectedUserId();
    if (!userId) {
      toast.error('Selecciona un usuario primero');
      return;
    }
    this.isAssigning.set(true);
    try {
      const roleIds = Array.from(this.selectedUserRoles());
      const res = await firstValueFrom(
        this.rbacApi.assignUserRoles(userId, { role_ids: roleIds })
      );
      toast.success(res.message);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Error al asignar roles al usuario'));
    } finally {
      this.isAssigning.set(false);
    }
  }

  getModuleLabel(module: string): string {
    const labels: Record<string, string> = {
      inventory: 'Inventario y Almacén',
      sales: 'Ventas y Caja',
      reports: 'Reportes e Inteligencia',
      catalog: 'Catálogo de Prendas',
      users: 'Gestión de Usuarios',
      rbac: 'Roles y Permisos',
      replenishment: 'Reabastecimiento',
      promotions: 'Promociones y Cupones',
      orders: 'Pedidos de Clientes',
      reservations: 'Reservas de Prendas',
    };
    return labels[module] ?? module.toUpperCase();
  }
}
