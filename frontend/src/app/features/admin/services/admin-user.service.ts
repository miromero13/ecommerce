import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { AdminUsuario, ListResponse } from '../models/admin-user.model';
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
}
