import { Injectable } from '@angular/core';

export const OFFLINE_DB_NAME = 'FashionStoreOfflineDB';
export const OFFLINE_DB_VERSION = 3;

export const STORES = {
  CACHED_CATALOG: 'cached_catalog',
  PENDING_OPERATIONS_QUEUE: 'pending_operations_queue',
  PENDING_CART_ITEMS: 'pending_cart_items',
  HTTP_CACHE: 'http_cache',
} as const;

export type StoreName = (typeof STORES)[keyof typeof STORES];

@Injectable({
  providedIn: 'root',
})
export class IndexedDbService {
  private dbPromise: Promise<IDBDatabase> | null = null;

  private getDb(): Promise<IDBDatabase> {
    if (this.dbPromise) {
      return this.dbPromise;
    }

    if (typeof window === 'undefined' || !window.indexedDB) {
      return Promise.reject(new Error('IndexedDB no está disponible en este entorno.'));
    }

    this.dbPromise = new Promise<IDBDatabase>((resolve, reject) => {
      const request = window.indexedDB.open(OFFLINE_DB_NAME, OFFLINE_DB_VERSION);

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // 1. Almacén de catálogo local sincronizado (CU23)
        if (!db.objectStoreNames.contains(STORES.CACHED_CATALOG)) {
          const catalogStore = db.createObjectStore(STORES.CACHED_CATALOG, { keyPath: 'id' });
          catalogStore.createIndex('name', 'name', { unique: false });
          catalogStore.createIndex('category', 'category', { unique: false });
          catalogStore.createIndex('tenant_id', 'tenant_id', { unique: false });
        }

        // 2. Almacén de cola de transacciones locales pendientes (CU25, CU29, CU30)
        if (!db.objectStoreNames.contains(STORES.PENDING_OPERATIONS_QUEUE)) {
          const queueStore = db.createObjectStore(STORES.PENDING_OPERATIONS_QUEUE, { keyPath: 'operation_id' });
          queueStore.createIndex('created_at', 'created_at', { unique: false });
          queueStore.createIndex('status', 'status', { unique: false });
          queueStore.createIndex('type', 'type', { unique: false });
        }

        // 3. Prendas que el cliente agregó al carrito sin conexión (CU25, se sincronizan en CU30)
        if (!db.objectStoreNames.contains(STORES.PENDING_CART_ITEMS)) {
          db.createObjectStore(STORES.PENDING_CART_ITEMS, { keyPath: 'id' });
        }

        // 4. Última respuesta con conexión del catálogo público: se muestra cuando no hay internet
        if (!db.objectStoreNames.contains(STORES.HTTP_CACHE)) {
          db.createObjectStore(STORES.HTTP_CACHE, { keyPath: 'key' });
        }
      };

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });

    return this.dbPromise;
  }

  async putItem<T>(storeName: StoreName, item: T): Promise<void> {
    const db = await this.getDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);
      const req = store.put(item);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  }

  async putItems<T>(storeName: StoreName, items: T[]): Promise<void> {
    if (!items.length) return;
    const db = await this.getDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);

      items.forEach((item) => store.put(item));

      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  async getItem<T>(storeName: StoreName, key: IDBValidKey): Promise<T | null> {
    const db = await this.getDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const req = store.get(key);
      req.onsuccess = () => resolve((req.result as T) ?? null);
      req.onerror = () => reject(req.error);
    });
  }

  async getAll<T>(storeName: StoreName): Promise<T[]> {
    const db = await this.getDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const req = store.getAll();
      req.onsuccess = () => resolve((req.result as T[]) ?? []);
      req.onerror = () => reject(req.error);
    });
  }

  async deleteItem(storeName: StoreName, key: IDBValidKey): Promise<void> {
    const db = await this.getDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);
      const req = store.delete(key);
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  }

  async clearStore(storeName: StoreName): Promise<void> {
    const db = await this.getDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);
      const req = store.clear();
      req.onsuccess = () => resolve();
      req.onerror = () => reject(req.error);
    });
  }

  async count(storeName: StoreName): Promise<number> {
    const db = await this.getDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const req = store.count();
      req.onsuccess = () => resolve(req.result ?? 0);
      req.onerror = () => reject(req.error);
    });
  }
}
