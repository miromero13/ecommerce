import { ApiResponse } from '../../../core/models/api.model';
import { GeneroUsuario } from '../../shared/models/auth.model';

export type ProviderStatus = 'active' | 'suspended';

export interface AdminProvider {
  id: string;
  user_id: string;
  business_name: string;
  contact_name: string;
  email: string;
  gender: GeneroUsuario;
  phone: string | null;
  branch_id: string | null;
  status: ProviderStatus;
}

export interface CreateProviderRequest {
  business_name: string;
  contact_name: string;
  email: string;
  password: string;
  gender: GeneroUsuario;
  phone?: string | null;
  branch_id?: string | null;
}

export interface UpdateProviderStatusRequest {
  status: ProviderStatus;
}

export interface UpdateProviderRequest {
  business_name: string;
  contact_name: string;
  email: string;
  gender: GeneroUsuario;
  phone?: string | null;
  branch_id?: string | null;
  status: ProviderStatus;
}

export type ProviderListResponse = ApiResponse<AdminProvider[]>;
