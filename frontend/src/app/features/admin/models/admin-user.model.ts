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
}

export interface UpdateUsuarioRequest {
  name: string;
  email: string;
  gender: GeneroUsuario;
  branch_id?: string | null;
  is_active: boolean;
}

export interface UpdateUsuarioActiveRequest {
  is_active: boolean;
}

export type ListResponse<T> = ApiResponse<T[]>;
