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

export interface CatalogProduct {
  id: string;
  sku: string;
  name: string;
  description: string | null;
  price: string;
  status: ProductStatus;
  category_id: string;
  size_id: string | null;
  color_id: string | null;
  season_id: string | null;
  collection_id: string | null;
  branch_quantity?: number | null;
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

export interface CreateProductRequest {
  sku: string;
  name: string;
  description?: string | null;
  price: string;
  category_id: string;
  size_id?: string | null;
  color_id?: string | null;
  season_id?: string | null;
  collection_id?: string | null;
}

export type ListResponse<T> = ApiResponse<T[]>;
