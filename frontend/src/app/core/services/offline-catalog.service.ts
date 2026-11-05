import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { IndexedDbService, STORES } from './indexeddb.service';
import { environment } from '../../../environments/environment';

export interface OfflineVariant {
  id: string;
  sku: string;
  price: number;
  size: string | null;
  size_id: string | null;
  color: string | null;
  color_hex: string | null;
  color_id: string | null;
  image_url: string | null;
  available_stock: number;
}

export interface OfflineCatalogProduct {
  id: string;
  tenant_id: string;
  name: string;
  description: string;
  category_id: string | null;
  category: string;
  discount_type: string | null;
  discount_value: number | null;
  variants: OfflineVariant[];
  synced_at: string;
}

export interface CatalogSyncResponse {
  statusCode: number;
  message: string;
  data: {
    branch_id: string | null;
    total_products: number;
    synced_at: string;
    products: OfflineCatalogProduct[];
  };
}

@Injectable({
  providedIn: 'root',
})
export class OfflineCatalogService {
  private readonly http = inject(HttpClient);
  private readonly idb = inject(IndexedDbService);

  readonly isSyncing = signal<boolean>(false);
  readonly lastSyncTimestamp = signal<Date | null>(null);
  readonly cachedCount = signal<number>(0);
  readonly isOffline = signal<boolean>(typeof navigator !== 'undefined' ? !navigator.onLine : false);

  constructor() {
    this.initNetworkListeners();
    this.refreshCachedCount();
  }

  private initNetworkListeners(): void {
    if (typeof window === 'undefined') return;

    window.addEventListener('online', () => {
      this.isOffline.set(false);
      // Al recuperar conexión, refrescar automáticamente el catálogo local
      this.syncCatalog().catch(() => {});
    });

    window.addEventListener('offline', () => {
      this.isOffline.set(true);
    });
  }

  async refreshCachedCount(): Promise<number> {
    try {
      const count = await this.idb.count(STORES.CACHED_CATALOG);
      this.cachedCount.set(count);
      return count;
    } catch {
      return 0;
    }
  }

  /**
   * CU23: Descarga y sincroniza el catálogo de la sucursal en IndexedDB
   */
  async syncCatalog(branchId?: string): Promise<number> {
    if (this.isOffline()) {
      return this.cachedCount();
    }

    this.isSyncing.set(true);
    try {
      const apiUrl = environment.apiBaseUrl || '/api';
      const params: Record<string, string> = {};
      if (branchId) {
        params['branch_id'] = branchId;
      }

      const res = await firstValueFrom(
        this.http.get<CatalogSyncResponse>(`${apiUrl}/offline/catalog-sync`, { params })
      );

      if (res?.data?.products) {
        // Reemplazar almacén local con los productos sincronizados
        await this.idb.clearStore(STORES.CACHED_CATALOG);
        await this.idb.putItems(STORES.CACHED_CATALOG, res.data.products);

        const newCount = res.data.products.length;
        this.cachedCount.set(newCount);
        const syncDate = new Date(res.data.synced_at || Date.now());
        this.lastSyncTimestamp.set(syncDate);
        return newCount;
      }
      return 0;
    } catch (err) {
      console.warn('No se pudo sincronizar el catálogo online, utilizando copia local:', err);
      await this.refreshCachedCount();
      return this.cachedCount();
    } finally {
      this.isSyncing.set(false);
    }
  }

  /**
   * Búsqueda en catálogo local cuando no hay conexión a internet
   */
  async searchProducts(query: string = '', category: string = ''): Promise<OfflineCatalogProduct[]> {
    try {
      const all = await this.idb.getAll<OfflineCatalogProduct>(STORES.CACHED_CATALOG);
      const cleanQuery = query.trim().toLowerCase();
      const cleanCategory = category.trim().toLowerCase();

      return all.filter((prod) => {
        const matchesCategory =
          !cleanCategory ||
          cleanCategory === 'todas' ||
          (prod.category && prod.category.toLowerCase().includes(cleanCategory));

        if (!matchesCategory) return false;
        if (!cleanQuery) return true;

        const nameMatch = prod.name.toLowerCase().includes(cleanQuery);
        const descMatch = prod.description.toLowerCase().includes(cleanQuery);
        const skuMatch = prod.variants.some((v) => v.sku.toLowerCase().includes(cleanQuery));

        return nameMatch || descMatch || skuMatch;
      });
    } catch (err) {
      console.error('Error buscando en catálogo offline IndexedDB:', err);
      return [];
    }
  }

  /**
   * Obtener un producto específico por ID desde la base local
   */
  async getProduct(id: string): Promise<OfflineCatalogProduct | null> {
    try {
      return await this.idb.getItem<OfflineCatalogProduct>(STORES.CACHED_CATALOG, id);
    } catch {
      return null;
    }
  }

  /**
   * Buscar variante por SKU en el catálogo local (útil para lectores de código de barras)
   */
  async findVariantBySku(sku: string): Promise<{ product: OfflineCatalogProduct; variant: OfflineVariant } | null> {
    try {
      const all = await this.idb.getAll<OfflineCatalogProduct>(STORES.CACHED_CATALOG);
      const cleanSku = sku.trim().toLowerCase();

      for (const product of all) {
        const foundVariant = product.variants.find((v) => v.sku.toLowerCase() === cleanSku);
        if (foundVariant) {
          return { product, variant: foundVariant };
        }
      }
      return null;
    } catch {
      return null;
    }
  }
}
