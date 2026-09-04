import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import {
  CatalogBranch,
  CatalogCollectionItem,
  CatalogColorItem,
  CatalogNameItem,
  CatalogProduct,
  CreateCollectionRequest,
  CreateColorRequest,
  CreateNameItemRequest,
  CreateProductRequest,
  ListResponse,
  ProductStatus,
} from '../models/catalog.model';

@Injectable({ providedIn: 'root' })
export class CatalogApiService {
  private readonly api = inject(ApiService);

  listPublicBranches() {
    return this.api.get<ListResponse<CatalogBranch>>('/branches/public');
  }

  listCategories() {
    return this.api.get<ListResponse<CatalogNameItem>>('/catalog/categories');
  }

  createCategory(payload: CreateNameItemRequest) {
    return this.api.post<ApiResponse<CatalogNameItem>>('/catalog/categories', payload);
  }

  listSizes() {
    return this.api.get<ListResponse<CatalogNameItem>>('/catalog/sizes');
  }

  createSize(payload: CreateNameItemRequest) {
    return this.api.post<ApiResponse<CatalogNameItem>>('/catalog/sizes', payload);
  }

  listColors() {
    return this.api.get<ListResponse<CatalogColorItem>>('/catalog/colors');
  }

  createColor(payload: CreateColorRequest) {
    return this.api.post<ApiResponse<CatalogColorItem>>('/catalog/colors', payload);
  }

  listSeasons() {
    return this.api.get<ListResponse<CatalogNameItem>>('/catalog/seasons');
  }

  createSeason(payload: CreateNameItemRequest) {
    return this.api.post<ApiResponse<CatalogNameItem>>('/catalog/seasons', payload);
  }

  listCollections() {
    return this.api.get<ListResponse<CatalogCollectionItem>>('/catalog/collections');
  }

  createCollection(payload: CreateCollectionRequest) {
    return this.api.post<ApiResponse<CatalogCollectionItem>>('/catalog/collections', payload);
  }

  listProducts(params?: Record<string, string | undefined>) {
    const query = params
      ? '?' + Object.entries(params).filter(([, value]) => !!value).map(([key, value]) => `${key}=${encodeURIComponent(value ?? '')}`).join('&')
      : '';
    return this.api.get<ListResponse<CatalogProduct>>(`/catalog/products${query}`);
  }

  listPendingProducts() {
    return this.api.get<ListResponse<CatalogProduct>>('/catalog/products/pending');
  }

  createProduct(payload: CreateProductRequest) {
    return this.api.post<ApiResponse<CatalogProduct>>('/catalog/products', payload);
  }

  submitProviderProduct(payload: CreateProductRequest) {
    return this.api.post<ApiResponse<CatalogProduct>>('/catalog/products/provider-submission', payload);
  }

  updateProductStatus(productId: string, status: ProductStatus) {
    return this.api.patch<ApiResponse<CatalogProduct>>(`/catalog/products/${productId}/status`, { status });
  }

  getAvailability(productId: string, branchId: string) {
    return this.api.get<ApiResponse<{ product_id: string; branch_id: string; quantity: number }>>(
      `/catalog/availability?product_id=${productId}&branch_id=${branchId}`,
    );
  }
}
