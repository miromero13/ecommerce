import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { AdminUsuario, ListResponse, UpdateUsuarioActiveRequest, UpdateUsuarioRequest } from '../models/admin-user.model';
import { ApiService } from '../../../core/services/api.service';

@Injectable({ providedIn: 'root' })
export class AdminUserService {
  private readonly api = inject(ApiService);

  listUsuarios(skip = 0, limit = 100) {
    return this.api.get<ListResponse<AdminUsuario>>(`/users/?skip=${skip}&limit=${limit}`);
  }

  updateUsuarioRol(userId: string, rol: AdminUsuario['rol']) {
    return this.api.patch<ApiResponse<AdminUsuario>>(`/users/${userId}/rol`, { rol });
  }

  updateUsuarioBranch(userId: string, branchId: string | null) {
    return this.api.patch<ApiResponse<AdminUsuario>>(`/users/${userId}/branch`, { branch_id: branchId });
  }

  updateUsuario(userId: string, payload: UpdateUsuarioRequest) {
    return this.api.put<ApiResponse<AdminUsuario>>(`/users/${userId}`, payload);
  }

  updateUsuarioActive(userId: string, payload: UpdateUsuarioActiveRequest) {
    return this.api.patch<ApiResponse<AdminUsuario>>(`/users/${userId}/active`, payload);
  }

  deleteUsuario(userId: string) {
    return this.api.delete<ApiResponse<{ id: string }>>(`/users/${userId}`);
  }
}
