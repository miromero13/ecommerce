import { ApiResponse } from '../../../core/models/api.model';

export interface CatalogBranch {
  id: string;
  name: string;
  city: string;
  is_default: boolean;
}

export interface CatalogNameItem {
  id: string;
  name: string;
}

export interface CatalogColorItem extends CatalogNameItem {
  hex_code: string | null;
}

export interface CatalogCollectionItem extends CatalogNameItem {
  season_id: string | null;
}

export type ProductStatus = 'pending' | 'active' | 'inactive';
export type DiscountType = 'percentage' | 'fixed';

export interface CatalogProductVariant {
  id: string;
  product_id: string;
  sku: string;
  price: string;
  original_price?: string | null;
  discount_amount?: string;
  size_id: string | null;
  color_id: string | null;
  image_url?: string | null;
  image_public_id?: string | null;
  status: ProductStatus;
  branch_quantity?: number | null;
  provider_quantity?: number | null;
}

export interface CatalogProduct {
  id: string;
  name: string;
  description: string | null;
  discount_type?: DiscountType | null;
  discount_value?: string | null;
  provider_id?: string | null;
  category_id: string;
  collection_id: string | null;
  sku?: string | null;
  image_url?: string | null;
  image_public_id?: string | null;
  status?: ProductStatus | null;
  size_id?: string | null;
  color_id?: string | null;
  branch_quantity?: number | null;
  variants?: CatalogProductVariant[];
}

export interface CollaborativeRecommendation {
  product_id: string;
  score: number;
}

export interface CollaborativeRecommendations {
  logic_type: 'implicit_als' | 'popular_fallback';
  user_id: string;
  recommendations: CollaborativeRecommendation[];
}

export interface CreateNameItemRequest {
  name: string;
}

export interface CreateColorRequest {
  name: string;
  hex_code?: string | null;
}

export interface CreateCollectionRequest {
  name: string;
  season_id?: string | null;
}

export interface CreateProductVariantRequest {
  id?: string;
  sku: string;
  price: string;
  size_id?: string | null;
  color_id?: string | null;
  image_url?: string | null;
  image_public_id?: string | null;
  status?: ProductStatus;
}

export interface CreateProductRequest {
  name: string;
  description?: string | null;
  category_id: string;
  provider_id?: string | null;
  collection_id?: string | null;
  discount_type?: DiscountType | null;
  discount_value?: string | null;
  status?: ProductStatus;
  variants: CreateProductVariantRequest[];
}

export interface UpdateNameItemRequest {
  name: string;
}

export interface UpdateColorRequest {
  name: string;
  hex_code?: string | null;
}

export interface UpdateCollectionRequest {
  name: string;
  season_id?: string | null;
}

export interface UpdateProductRequest {
  name: string;
  description?: string | null;
  category_id: string;
  provider_id?: string | null;
  collection_id?: string | null;
  discount_type?: DiscountType | null;
  discount_value?: string | null;
  status?: ProductStatus;
  sku?: string;
  variants: CreateProductVariantRequest[];
}

export type ListResponse<T> = ApiResponse<T[]>;
