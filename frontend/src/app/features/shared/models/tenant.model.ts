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
  plan_name?: string | null; // current plan; null when the subscription expired
  subscription_end_date?: string | null;
  has_admin?: boolean; // the superadmin can only enter the panel of a company with an administrator
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

/** Administrator registered by the superadmin for a company that has none. */
export interface TenantAdminPayload {
  name: string;
  email: string;
  password: string;
  gender: 'masculino' | 'femenino';
}
