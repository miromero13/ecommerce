import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
} from '../models/auth.model';

@Injectable({ providedIn: 'root' })
export class AuthApiService {
  private readonly api = inject(ApiService);

  login(payload: LoginRequest) {
    return this.api.post<ApiResponse<AuthResponse>>('/auth/login', payload);
  }

  register(payload: RegisterRequest) {
    return this.api.post<ApiResponse<AuthResponse>>('/auth/register', payload);
  }

}
