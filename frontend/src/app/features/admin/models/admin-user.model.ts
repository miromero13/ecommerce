import { ApiResponse } from '../../../core/models/api.model';
import { GeneroUsuario, RolUsuario } from '../../shared/models/auth.model';

export interface AdminUsuario {
  id: string;
  name: string;
  email: string;
  gender: GeneroUsuario;
  rol: RolUsuario;
}

export type ListResponse<T> = ApiResponse<T[]>;
