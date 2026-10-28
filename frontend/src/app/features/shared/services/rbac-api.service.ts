import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ApiService } from '../../../core/services/api.service';
import { ApiResponse } from '../../../core/models/api.model';
import {
  Permission,
  Role,
  RoleCreate,
  RoleUpdate,
  UserRolesAssign,
} from '../models/rbac.model';

@Injectable({ providedIn: 'root' })
export class RbacApiService {
  private readonly api = inject(ApiService);

  getPermissions(): Observable<ApiResponse<Permission[]>> {
    return this.api.get<ApiResponse<Permission[]>>('/rbac/permissions');
  }

  getRoles(): Observable<ApiResponse<Role[]>> {
    return this.api.get<ApiResponse<Role[]>>('/rbac/roles');
  }

  createRole(payload: RoleCreate): Observable<ApiResponse<Role>> {
    return this.api.post<ApiResponse<Role>>('/rbac/roles', payload);
  }

  updateRole(roleId: string, payload: RoleUpdate): Observable<ApiResponse<Role>> {
    return this.api.put<ApiResponse<Role>>(`/rbac/roles/${roleId}`, payload);
  }

  assignUserRoles(userId: string, payload: UserRolesAssign): Observable<ApiResponse<Role[]>> {
    return this.api.post<ApiResponse<Role[]>>(`/rbac/users/${userId}/roles`, payload);
  }
}
