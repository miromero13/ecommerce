import { ApiResponse } from '../../../core/models/api.model';
import { GeneroUsuario, RolUsuario } from '../../shared/models/auth.model';

export interface AdminUsuario {
  id: string;
  name: string;
  email: string;
  gender: GeneroUsuario;
  rol: RolUsuario;
  branch_id: string | null;
  is_active: boolean;
  custom_roles?: Array<{ id: string; name: string; code: string }>;
}

export interface UpdateUsuarioRequest {
  name: string;
  email: string;
  gender: GeneroUsuario;
  rol?: Exclude<RolUsuario, 'cliente' | 'proveedor'>;
  role_id?: string | null;
  branch_id?: string | null;
  is_active: boolean;
}

export interface CreateUsuarioRequest {
  name: string;
  email: string;
  password: string;
  gender: GeneroUsuario;
  rol: Exclude<RolUsuario, 'cliente' | 'proveedor'>;
  role_id?: string | null;
  branch_id?: string | null;
  is_active: boolean;
}

export interface UpdateUsuarioActiveRequest {
  is_active: boolean;
}

export type ListResponse<T> = ApiResponse<T[]>;
