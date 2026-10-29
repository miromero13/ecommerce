import { computed, inject, Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { ApiResponse } from '../../../core/models/api.model';
import { AuthResponse, LoginRequest, RegisterRequest, RolUsuario, UsuarioAuth } from '../models/auth.model';
import { AuthApiService } from './auth-api.service';
import { UserApiService } from './user-api.service';

const TOKEN_KEY = 'aci_token';
const USER_KEY = 'aci_user';
// Superadmin session kept aside while it works inside a company's panel.
const PANEL_RETURN_KEY = 'aci_panel_return';

interface PanelReturn {
  token: string;
  user: UsuarioAuth;
  tenantName: string;
}

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
  private readonly panelReturnSignal = signal<PanelReturn | null>(this.getStoredPanelReturn());
  /** Company whose panel the superadmin is using, or null. */
  readonly panelTenantName = computed(() => this.panelReturnSignal()?.tenantName ?? null);

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

  async login(email: string, password: string, rol?: RolUsuario): Promise<void> {
    this.loadingSignal.set(true);
    try {
      const payload: LoginRequest = { email: this.normalizeEmail(email), password };
      if (rol) {
        payload.rol = rol;
      }
      const response = await firstValueFrom(this.authApi.login(payload));
      this.applyAuthResponse(response);
    } finally {
      this.loadingSignal.set(false);
    }
  }

  async register(payload: RegisterRequest): Promise<void> {
    this.loadingSignal.set(true);
    try {
      const response = await firstValueFrom(this.authApi.register({ ...payload, email: this.normalizeEmail(payload.email) }));
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

  /** The superadmin switches to the company administrator's session; its own session is kept to come back. */
  async enterTenantPanel(auth: AuthResponse, tenantName: string): Promise<void> {
    const token = this.tokenSignal();
    const user = this.userSignal();
    if (!token || user?.rol !== 'superadministrador') return;
    const back: PanelReturn = { token, user, tenantName };
    localStorage.setItem(PANEL_RETURN_KEY, JSON.stringify(back));
    this.panelReturnSignal.set(back);
    this.setSession(auth.access_token, this.normalizeUser(auth.user));
    await this.router.navigate(['/app/admin']);
  }

  async leaveTenantPanel(): Promise<void> {
    const back = this.panelReturnSignal();
    if (!back) return;
    localStorage.removeItem(PANEL_RETURN_KEY);
    this.panelReturnSignal.set(null);
    this.setSession(back.token, back.user);
    await this.router.navigate(['/app/superadmin/tenants']);
  }

  private getStoredPanelReturn(): PanelReturn | null {
    try {
      const raw = localStorage.getItem(PANEL_RETURN_KEY);
      return raw ? (JSON.parse(raw) as PanelReturn) : null;
    } catch {
      localStorage.removeItem(PANEL_RETURN_KEY);
      return null;
    }
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
    localStorage.removeItem(PANEL_RETURN_KEY); // logging out also ends the superadmin's session
    this.panelReturnSignal.set(null);
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

  hasPermission(permission: string): boolean {
    const user = this.userSignal();
    if (!user) return false;
    if (user.rol === 'administrador' || user.rol === 'superadministrador') {
      return true;
    }
    return user.permissions?.includes(permission) ?? false;
  }

  private normalizeUser(user: Partial<UsuarioAuth>): UsuarioAuth {
    return {
      id: user.id ?? '',
      name: user.name ?? '',
      email: this.normalizeEmail(user.email ?? ''),
      gender: user.gender ?? 'masculino',
      rol: user.rol ?? 'cliente',
      tenant_id: user.tenant_id ?? null,
      branch_id: user.branch_id ?? null,
      is_active: user.is_active ?? true,
      permissions: user.permissions ?? [],
    };
  }

  private normalizeEmail(email: string): string {
    return email.trim().toLowerCase();
  }
}
