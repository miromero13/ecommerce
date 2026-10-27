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
  logo_url?: string | null;
  primary_color?: string | null;
}

/** CU1 company branding shown in the staff panel and on receipts. */
export interface TenantBranding {
  tenant_id: string;
  name: string;
  logo_url: string | null;
  primary_color: string | null;
  currency: string;
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
  primary_color?: string;
}
