export interface SubscriptionPlan {
  id: string;
  name: string;
  slug: string;
  description?: string;
  price_monthly: number;
  price_yearly: number;
  max_branches: number;
  max_garments: number;
  features: string[];
  is_active: boolean;
}

export interface TenantSubscription {
  id: string;
  tenant_id: string;
  plan_id: string;
  billing_cycle: 'monthly' | 'yearly';
  status: 'active' | 'trialing' | 'past_due' | 'canceled';
  payment_method: 'simulated_card' | 'cash' | 'stripe';
  start_date: string;
  end_date?: string;
}

export interface SubscriptionUsage {
  branches_count: number;
  branches_max: number | null;
  garments_count: number;
  garments_max: number | null;
}

export interface SubscriptionSummary {
  tenant_id: string;
  tenant_name: string;
  has_active_subscription: boolean;
  plan: SubscriptionPlan | null;
  subscription: TenantSubscription | null;
  usage: SubscriptionUsage;
  features: string[];
}

export interface SubscriptionPurchasePayload {
  company_name: string;
  slug?: string;
  country?: string;
  currency?: string;
  admin_name: string;
  admin_email: string;
  plan_id: string;
  billing_cycle: 'monthly' | 'yearly';
  card_number?: string;
  card_holder?: string;
  card_exp?: string;
  card_cvv?: string;
}

export interface TenantWithSubscriptionPayload {
  name: string;
  slug?: string;
  contact_email: string;
  country?: string;
  currency?: string;
  admin_name: string;
  plan_id: string;
  billing_cycle: 'monthly' | 'yearly';
  payment_method: 'cash' | 'simulated_card';
}
