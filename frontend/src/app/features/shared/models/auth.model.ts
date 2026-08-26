export type RolUsuario = 'administrador' | 'cliente' | 'delivery';

export type GeneroUsuario = 'masculino' | 'femenino';

export interface UsuarioAuth {
  id: string;
  name: string;
  email: string;
  gender: GeneroUsuario;
  rol: RolUsuario;
}

export interface LoginRequest {
  email: string;
  password: string;
  rol: RolUsuario;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  gender: GeneroUsuario;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UsuarioAuth;
}
