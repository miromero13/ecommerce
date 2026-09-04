import { computed, inject, Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { ApiResponse } from '../../../core/models/api.model';
import { AuthResponse, RegisterRequest, RolUsuario, UsuarioAuth } from '../models/auth.model';
import { AuthApiService } from './auth-api.service';
import { UserApiService } from './user-api.service';

const TOKEN_KEY = 'aci_token';
const USER_KEY = 'aci_user';

@Injectable({ providedIn: 'root' })
export class SessionService {
  private readonly router = inject(Router);
  private readonly authApi = inject(AuthApiService);
  private readonly userApi = inject(UserApiService);

  private readonly tokenSignal = signal<string | null>(localStorage.getItem(TOKEN_KEY));
  private readonly userSignal = signal<UsuarioAuth | null>(this.getStoredUser());
  private readonly loadingSignal = signal(false);

  readonly token = this.tokenSignal.asReadonly();
  readonly user = this.userSignal.asReadonly();
  readonly isLoading = this.loadingSignal.asReadonly();
  readonly isAuthenticated = computed(() => !!this.tokenSignal() && !!this.userSignal());

  async bootstrap(): Promise<void> {
    const storedToken = this.tokenSignal();
    if (!storedToken) {
      return;
    }

    this.tokenSignal.set(storedToken);
    this.loadingSignal.set(true);
    try {
      const response = await firstValueFrom(this.userApi.getMe());
      const user = response.data ?? null;
      this.userSignal.set(user);
      if (user) {
        localStorage.setItem(USER_KEY, JSON.stringify(user));
      }
    } catch {
      this.clearSession();
    } finally {
      this.loadingSignal.set(false);
    }
  }

  async login(email: string, password: string, rol: RolUsuario): Promise<void> {
    this.loadingSignal.set(true);
    try {
      const response = await firstValueFrom(this.authApi.login({ email, password, rol }));
      this.applyAuthResponse(response);
    } finally {
      this.loadingSignal.set(false);
    }
  }

  async register(payload: RegisterRequest): Promise<void> {
    this.loadingSignal.set(true);
    try {
      const response = await firstValueFrom(this.authApi.register(payload));
      this.applyAuthResponse(response);
    } finally {
      this.loadingSignal.set(false);
    }
  }

  async refreshMe(): Promise<void> {
    const response = await firstValueFrom(this.userApi.getMe());
    const user = response.data ?? null;
    this.userSignal.set(user);
    if (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    }
  }

  async logout(redirect = true): Promise<void> {
    this.clearSession();
    if (redirect) {
      await this.router.navigate(['/auth/login']);
    }
  }

  getToken(): string | null {
    return this.tokenSignal();
  }

  setSession(token: string, user: UsuarioAuth): void {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    this.tokenSignal.set(token);
    this.userSignal.set(user);
  }

  private applyAuthResponse(response: ApiResponse<AuthResponse>): void {
    const auth = response.data;
    if (!auth) {
      throw new Error('La respuesta de autenticación no incluye datos');
    }

    this.setSession(auth.access_token, this.normalizeUser(auth.user));
  }

  clearSession(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    this.tokenSignal.set(null);
    this.userSignal.set(null);
  }

  private getStoredUser(): UsuarioAuth | null {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) {
      return null;
    }

    try {
      return this.normalizeUser(JSON.parse(raw) as Partial<UsuarioAuth>);
    } catch {
      localStorage.removeItem(USER_KEY);
      return null;
    }
  }

  private normalizeUser(user: Partial<UsuarioAuth>): UsuarioAuth {
    return {
      id: user.id ?? '',
      name: user.name ?? '',
      email: user.email ?? '',
      gender: user.gender ?? 'masculino',
      rol: user.rol ?? 'cliente',
      branch_id: user.branch_id ?? null,
    };
  }
}
