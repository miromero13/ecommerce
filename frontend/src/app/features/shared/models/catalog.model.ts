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

export interface CatalogProductVariant {
  id: string;
  product_id: string;
  sku: string;
  price: string;
  size_id: string | null;
  color_id: string | null;
  status: ProductStatus;
  branch_quantity?: number | null;
}

export interface CatalogProduct {
  id: string;
  name: string;
  description: string | null;
  price: string;
  provider_id?: string | null;
  category_id: string;
  season_id: string | null;
  collection_id: string | null;
  sku?: string | null;
  status?: ProductStatus | null;
  size_id?: string | null;
  color_id?: string | null;
  branch_quantity?: number | null;
  variants?: CatalogProductVariant[];
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
  sku: string;
  price: string;
  size_id?: string | null;
  color_id?: string | null;
  status?: ProductStatus;
}

export interface CreateProductRequest {
  name: string;
  description?: string | null;
  price: string;
  category_id: string;
  provider_id?: string | null;
  size_id?: string | null;
  color_id?: string | null;
  season_id?: string | null;
  collection_id?: string | null;
  status?: ProductStatus;
  sku?: string;
  variants?: CreateProductVariantRequest[];
}

export type ListResponse<T> = ApiResponse<T[]>;
