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
  UpdateCollectionRequest,
  UpdateColorRequest,
  UpdateNameItemRequest,
  UpdateProductRequest,
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

  updateCategory(categoryId: string, payload: UpdateNameItemRequest) {
    return this.api.put<ApiResponse<CatalogNameItem>>(`/catalog/categories/${categoryId}`, payload);
  }

  deleteCategory(categoryId: string) {
    return this.api.delete<ApiResponse<{ id: string }>>(`/catalog/categories/${categoryId}`);
  }

  listSizes() {
    return this.api.get<ListResponse<CatalogNameItem>>('/catalog/sizes');
  }

  createSize(payload: CreateNameItemRequest) {
    return this.api.post<ApiResponse<CatalogNameItem>>('/catalog/sizes', payload);
  }

  updateSize(sizeId: string, payload: UpdateNameItemRequest) {
    return this.api.put<ApiResponse<CatalogNameItem>>(`/catalog/sizes/${sizeId}`, payload);
  }

  deleteSize(sizeId: string) {
    return this.api.delete<ApiResponse<{ id: string }>>(`/catalog/sizes/${sizeId}`);
  }

  listColors() {
    return this.api.get<ListResponse<CatalogColorItem>>('/catalog/colors');
  }

  createColor(payload: CreateColorRequest) {
    return this.api.post<ApiResponse<CatalogColorItem>>('/catalog/colors', payload);
  }

  updateColor(colorId: string, payload: UpdateColorRequest) {
    return this.api.put<ApiResponse<CatalogColorItem>>(`/catalog/colors/${colorId}`, payload);
  }

  deleteColor(colorId: string) {
    return this.api.delete<ApiResponse<{ id: string }>>(`/catalog/colors/${colorId}`);
  }

  listSeasons() {
    return this.api.get<ListResponse<CatalogNameItem>>('/catalog/seasons');
  }

  createSeason(payload: CreateNameItemRequest) {
    return this.api.post<ApiResponse<CatalogNameItem>>('/catalog/seasons', payload);
  }

  updateSeason(seasonId: string, payload: UpdateNameItemRequest) {
    return this.api.put<ApiResponse<CatalogNameItem>>(`/catalog/seasons/${seasonId}`, payload);
  }

  deleteSeason(seasonId: string) {
    return this.api.delete<ApiResponse<{ id: string }>>(`/catalog/seasons/${seasonId}`);
  }

  listCollections() {
    return this.api.get<ListResponse<CatalogCollectionItem>>('/catalog/collections');
  }

  createCollection(payload: CreateCollectionRequest) {
    return this.api.post<ApiResponse<CatalogCollectionItem>>('/catalog/collections', payload);
  }

  updateCollection(collectionId: string, payload: UpdateCollectionRequest) {
    return this.api.put<ApiResponse<CatalogCollectionItem>>(`/catalog/collections/${collectionId}`, payload);
  }

  deleteCollection(collectionId: string) {
    return this.api.delete<ApiResponse<{ id: string }>>(`/catalog/collections/${collectionId}`);
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

  updateProduct(productId: string, payload: UpdateProductRequest) {
    return this.api.put<ApiResponse<CatalogProduct>>(`/catalog/products/${productId}`, payload);
  }

  deleteProduct(productId: string) {
    return this.api.delete<ApiResponse<{ id: string }>>(`/catalog/products/${productId}`);
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

  getVariantAvailability(variantId: string, branchId: string) {
    return this.api.get<ApiResponse<{ variant_id: string; branch_id: string; quantity: number }>>(
      `/catalog/availability?variant_id=${variantId}&branch_id=${branchId}`,
    );
  }

  updateVariantStatus(variantId: string, status: ProductStatus) {
    return this.api.patch<ApiResponse<CatalogProduct>>(`/catalog/variants/${variantId}/status`, { status });
  }
}
