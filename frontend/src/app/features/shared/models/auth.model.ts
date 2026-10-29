export type RolUsuario = 'superadministrador' | 'administrador' | 'cliente' | 'proveedor' | 'encargado' | 'cajero' | 'delivery';

export type GeneroUsuario = 'masculino' | 'femenino';

export interface UsuarioAuth {
  id: string;
  name: string;
  email: string;
  gender: GeneroUsuario;
  rol: RolUsuario;
  tenant_id?: string | null;
  branch_id: string | null;
  is_active?: boolean;
  permissions?: string[];
}

export interface LoginRequest {
  email: string;
  password: string;
  rol?: RolUsuario;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  gender: GeneroUsuario;
}

export interface UpdateProfileRequest {
  name: string;
  email: string;
  gender: GeneroUsuario;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UsuarioAuth;
}
