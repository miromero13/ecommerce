export type TenantStatus = 'active' | 'trial' | 'suspended';

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  contact_email: string;
  currency: string;
  country?: string | null;
  status: TenantStatus;
  created_at: string;
  updated_at: string;
  branches_count: number;
  users_count: number;
}

export interface TenantCreatePayload {
  name: string;
  slug: string;
  contact_email: string;
  currency?: string;
  country?: string;
  status?: TenantStatus;
}

export interface TenantUpdatePayload {
  name?: string;
  slug?: string;
  contact_email?: string;
  currency?: string;
  country?: string;
  status?: TenantStatus;
}
