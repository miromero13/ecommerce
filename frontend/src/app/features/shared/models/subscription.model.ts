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

export interface PlanFeatureInfo {
  key: string;
  label: string;
  description: string;
  /** Sold in the plan but not available in the platform yet. */
  comingSoon?: boolean;
}

/** Every module a plan can include, in display order; keys match the backend plan features. */
export const PLAN_FEATURES: PlanFeatureInfo[] = [
  { key: 'catalog', label: 'Catálogo web y móvil', description: 'Tus prendas publicadas en el marketplace, con filtros por categoría, talla, color y temporada.' },
  { key: 'pos', label: 'Punto de venta (POS)', description: 'Ventas presenciales en caja con cobro y comprobante.' },
  { key: 'inventory', label: 'Inventario por sucursal', description: 'Stock por sucursal, movimientos, traspasos y alertas de stock mínimo.' },
  { key: 'reservations', label: 'Reservas y pedidos para retiro', description: 'Tus clientes reservan o compran online y retiran en la sucursal que eligen.' },
  { key: 'standard_reports', label: 'Reportes y dashboard', description: 'Reportes de ventas, inventario y movimientos exportables, con métricas del negocio.' },
  { key: 'chatbot', label: 'Asistente virtual (chatbot)', description: 'Tus productos aparecen en las recomendaciones del asistente de compras de la plataforma.' },
  { key: 'virtual_try_on_2d', label: 'Vestidor virtual', description: 'Tus clientes se prueban tus prendas con la cámara o una foto antes de comprar.' },
  { key: 'ai_text_reports', label: 'Reportes con IA en lenguaje natural', description: 'Pedí reportes escribiendo, por ejemplo: "ventas de esta semana por sucursal".' },
  { key: 'virtual_try_on_3d_ar', label: 'Vestidor 3D con realidad aumentada', description: 'Seguimiento del cuerpo en vivo con ajuste dinámico de la prenda.', comingSoon: true },
  { key: 'ai_ml_smart_reports', label: 'Analítica predictiva con Machine Learning', description: 'Predicción de demanda y segmentación de clientes (RFM).', comingSoon: true },
];

export interface SubscriptionPlanPayload {
  name: string;
  /** Only on creation: the plan id becomes "plan_<slug>". */
  slug?: string;
  description?: string | null;
  price_monthly: number;
  price_yearly: number;
  max_branches: number;
  max_garments: number;
  features: string[];
  is_active: boolean;
}

export interface SubscriptionChangePlanPayload {
  plan_id: string;
  billing_cycle: 'monthly' | 'yearly';
  card_number?: string;
  card_holder?: string;
  card_exp?: string;
  card_cvv?: string;
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

export interface StripeConnectStatus {
  connected: boolean;
  charges_enabled: boolean;
  account_id: string | null;
}
