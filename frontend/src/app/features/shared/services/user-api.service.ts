import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { PerfilUsuario } from '../models/user.model';
import { UpdateProfileRequest } from '../models/auth.model';
import { ApiService } from '../../../core/services/api.service';

@Injectable({ providedIn: 'root' })
export class UserApiService {
  private readonly api = inject(ApiService);

  getMe() {
    return this.api.get<ApiResponse<PerfilUsuario>>('/users/me');
  }

  updateMe(payload: UpdateProfileRequest) {
    return this.api.put<ApiResponse<PerfilUsuario>>('/users/me', payload);
  }
}
