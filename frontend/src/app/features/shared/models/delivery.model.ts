import { FulfillmentStatusEnum } from './order.model';

export interface DeliveryAddress {
  address: string;
  reference?: string | null;
  latitude: number;
  longitude: number;
}

export interface DeliveryQuote {
  distance_km: number;
  shipping_cost: number;
  estimated_minutes: number;
}

export interface DeliveryOrder {
  order_id: string;
  tenant_name: string;
  branch_name: string | null;
  branch_city: string | null;
  client_name: string | null;
  address: string;
  reference: string | null;
  distance_km: number | null;
  shipping_cost: number;
  total_amount: number;
  currency: string;
  status: FulfillmentStatusEnum;
  driver_name: string | null;
  delivered_at: string | null;
  created_at: string;
  delivery_pin?: string;
}

export interface DriverCreate {
  name: string;
  email: string;
  password: string;
  gender: 'masculino' | 'femenino';
}
