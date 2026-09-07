import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { AddCartItemRequest, Cart, CartResponse, UpdateCartItemRequest } from '../models/cart.model';

@Injectable({ providedIn: 'root' })
export class CartApiService {
  private readonly api = inject(ApiService);

  getCurrentCart() {
    return this.api.get<CartResponse>('/cart/current');
  }

  addItem(payload: AddCartItemRequest) {
    return this.api.post<CartResponse>('/cart/items', payload);
  }

  updateItem(itemId: string, payload: UpdateCartItemRequest) {
    return this.api.patch<CartResponse>(`/cart/items/${itemId}`, payload);
  }

  removeItem(itemId: string) {
    return this.api.delete<CartResponse>(`/cart/items/${itemId}`);
  }

  clearCart() {
    return this.api.delete<CartResponse>('/cart/current');
  }
}
