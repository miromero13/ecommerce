import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { Cart } from '../models/cart.model';
import { WishlistItem } from '../models/wishlist.model';
import { SessionService } from './session.service';

/** CU16: the customer's favorites; `savedIds` keeps every heart button in sync. */
@Injectable({ providedIn: 'root' })
export class WishlistApiService {
  private readonly api = inject(ApiService);
  private readonly session = inject(SessionService);
  private readonly items = signal<WishlistItem[]>([]);
  private loaded = false;

  readonly savedIds = computed(() => new Set(this.items().map((item) => item.product_id)));
  readonly canUse = computed(() => this.session.user()?.rol === 'cliente');

  list() {
    return this.api.get<ApiResponse<WishlistItem[]>>('/wishlist');
  }

  /** Load once per session so catalog hearts show their state. */
  async ensureLoaded(): Promise<void> {
    if (this.loaded || !this.canUse()) return;
    this.loaded = true;
    await this.reload();
  }

  async reload(): Promise<WishlistItem[]> {
    const items = (await firstValueFrom(this.list())).data ?? [];
    this.items.set(items);
    return items;
  }

  async toggle(productId: string): Promise<string> {
    const response = this.savedIds().has(productId)
      ? await firstValueFrom(this.api.delete<ApiResponse<unknown>>(`/wishlist/items/${productId}`))
      : await firstValueFrom(this.api.post<ApiResponse<unknown>>('/wishlist/items', { product_id: productId }));
    await this.reload();
    return response.message;
  }

  async moveToCart(productId: string, variantId: string): Promise<string> {
    const response = await firstValueFrom(
      this.api.post<ApiResponse<Cart>>(`/wishlist/items/${productId}/move-to-cart`, { variant_id: variantId }),
    );
    await this.reload();
    return response.message;
  }
}
