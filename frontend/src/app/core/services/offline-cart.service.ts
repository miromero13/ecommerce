import { HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { toast } from '@spartan-ng/brain/sonner';

import { IndexedDbService, STORES } from './indexeddb.service';
import { requestWithToast } from '../utils/request-toast.util';
import { getErrorMessage, isNoResponse } from '../utils/http-error.util';
import { AddCartItemRequest } from '../../features/shared/models/cart.model';
import { CartApiService } from '../../features/shared/services/cart-api.service';

/** Prenda que el cliente agregó al carrito sin conexión (store pending_cart_items de IndexedDB). */
export interface PendingCartItem extends AddCartItemRequest {
  id: string;
  product_name: string;
  variant_label: string;
  created_at: string;
}

/**
 * Sin conexión = el navegador no tiene red. Un status 0 con red no es falta de internet: suele ser un error del
 * servidor sin cabeceras CORS, y se muestra como error (no se guarda la prenda como pendiente).
 */
function isOffline(): boolean {
  return !navigator.onLine;
}

/**
 * CU25 (cliente): agregar al carrito sin conexión guarda la prenda en IndexedDB.
 * CU30: al volver la conexión se envía cada prenda al carrito del servidor (POST /cart/items).
 * El pago con tarjeta (Stripe) siempre requiere conexión.
 */
@Injectable({ providedIn: 'root' })
export class OfflineCartService {
  private readonly idb = inject(IndexedDbService);
  private readonly cartApi = inject(CartApiService);

  readonly pending = signal<PendingCartItem[]>([]);
  private syncing = false;
  /** El carrito está bloqueado por un pedido pendiente: no se reintenta ni se repite el aviso hasta que se desbloquee. */
  private lockToastShown = false;
  private lockedAt = 0;

  constructor() {
    void this.loadPending().then(() => this.syncPending());
    window.addEventListener('online', () => void this.syncPending());
  }

  async loadPending(): Promise<PendingCartItem[]> {
    try {
      // [CU25 - Secuencia: Paso 2.3] OfflineCartService ejecuta getAll(STORES.PENDING_CART_ITEMS) sobre la entidad local PendingCartItem (IndexedDB)
      // [CU30 - Secuencia: Paso 3.20] OfflineCartService ejecuta getAll(STORES.PENDING_CART_ITEMS) sobre la entidad local PendingCartItem (IndexedDB)
      const items = await this.idb.getAll<PendingCartItem>(STORES.PENDING_CART_ITEMS);
      items.sort((a, b) => a.created_at.localeCompare(b.created_at));
      this.pending.set(items);
      return items;
    } catch {
      return [];
    }
  }

  /** Agrega al carrito del servidor; sin conexión, guarda la prenda localmente. Devuelve true si quedó agregada o guardada. */
  // [CU25 - Secuencia: Paso 2.1] ProductDetailPageComponent invoca addItem(payload, productName, variantLabel) en OfflineCartService
  async addItem(payload: AddCartItemRequest, productName: string, variantLabel: string): Promise<boolean> {
    if (isOffline()) {
      return this.saveLocally(payload, productName, variantLabel);
    }
    try {
      await requestWithToast(this.cartApi.addItem(payload), {
        loading: 'Agregando al carrito...',
        success: 'Producto agregado al carrito.',
        error: 'No se pudo agregar al carrito.',
      });
      return true;
    } catch (error) {
      // La conexión se cortó durante la petición, o hay Wi-Fi sin internet (navigator.onLine sigue en true pero el servidor
      // no responde: status 0): la prenda no se pierde, se guarda y se envía al volver la conexión.
      const noResponse = isNoResponse(error);
      return isOffline() || noResponse ? this.saveLocally(payload, productName, variantLabel) : false;
    }
  }

  private async saveLocally(payload: AddCartItemRequest, productName: string, variantLabel: string): Promise<boolean> {
    const item: PendingCartItem = {
      ...payload,
      id: crypto.randomUUID(),
      product_name: productName,
      variant_label: variantLabel,
      created_at: new Date().toISOString(),
    };
    // [CU25 - Secuencia: Paso 2.2] OfflineCartService ejecuta putItem(STORES.PENDING_CART_ITEMS, item) sobre la entidad local PendingCartItem (IndexedDB)
    await this.idb.putItem(STORES.PENDING_CART_ITEMS, item);
    await this.loadPending();
    toast.info('Sin conexión: guardamos la prenda y se agregará a tu carrito cuando vuelva la conexión.');
    return true;
  }

  /** El servidor devolvió el carrito sin bloqueo: se pueden reintentar las prendas guardadas. */
  cartUnlocked(): void {
    if (!this.lockToastShown) return;
    this.lockToastShown = false;
    void this.syncPending(); // ya hay un envío en curso: syncPending lo ignora
  }

  /** CU30: envía al servidor las prendas guardadas sin conexión. Devuelve cuántas se agregaron. */
  // [CU30 - Secuencia: Paso 3] El sistema dispara syncPending() en OfflineCartService (evento del navegador)
  async syncPending(): Promise<number> {
    if (!this.pending().length) this.lockToastShown = false;
    if (this.syncing || isOffline() || !this.pending().length || (this.lockToastShown && Date.now() - this.lockedAt < 5 * 60_000)) return 0; // pasados 5 min se permite un reintento
    this.syncing = true;
    let added = 0;
    try {
      for (const item of this.pending()) {
        const { id, product_name, variant_label, created_at, ...payload } = item;
        try {
          await firstValueFrom(this.cartApi.addItem(payload));
          added++;
          this.lockToastShown = false;
        } catch (error) {
          if (isOffline()) break; // se volvió a cortar: queda pendiente
          // Carrito bloqueado por un pedido pendiente de pago: la prenda se conserva y se reintenta en la próxima sincronización.
          if (error instanceof HttpErrorResponse && error.status === 400 && getErrorMessage(error, '').includes('pedido pendiente de pago')) {
            this.lockedAt = Date.now();
            if (!this.lockToastShown) toast.info('Tienes un pedido pendiente de pago: tus prendas guardadas se agregarán cuando lo pagues o lo canceles.');
            this.lockToastShown = true;
            break;
          }
          // Fallo transitorio (red inestable al volver el internet, sesión vencida, 5xx, límite de peticiones): la prenda se
          // conserva y se reintenta en la próxima sincronización; nunca se descarta por un error que no es del negocio.
          const status = error instanceof HttpErrorResponse ? error.status : 0;
          if (![400, 404, 409, 422].includes(status)) break;
          // El servidor la rechazó (sin stock, otra empresa...): se informa y se descarta.
          toast.error(`${product_name} (${variant_label}): ${getErrorMessage(error, 'no se pudo agregar al carrito.')}`);
        }
        // [CU30 - Secuencia: Paso 3.19] OfflineCartService ejecuta deleteItem(STORES.PENDING_CART_ITEMS, id) sobre la entidad local PendingCartItem (IndexedDB)
        await this.idb.deleteItem(STORES.PENDING_CART_ITEMS, id);
      }
    } finally {
      this.syncing = false;
      await this.loadPending();
    }
    if (added) toast.success(`Conexión restablecida: ${added} prenda(s) agregada(s) a tu carrito.`);
    return added;
  }
}
