import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmTable } from '../../../components/table/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { requestWithToast } from '../../../core/utils/request-toast.util';
import { Cart } from '../../shared/models/cart.model';
import { CartApiService } from '../../shared/services/cart-api.service';

@Component({
  selector: 'app-cart-page',
  standalone: true,
  imports: [CommonModule, RouterLink, HlmButton, HlmTable, ...HlmBadgeImports, ...HlmCardImports],
  templateUrl: './cart-page.component.html',
})
export class CartPageComponent {
  private readonly cartApi = inject(CartApiService);

  protected readonly cart = signal<Cart | null>(null);
  protected readonly loading = signal(false);
  protected readonly updatingItemId = signal<string | null>(null);

  constructor() {
    void this.loadCart();
  }

  protected get itemCount(): number {
    return this.cart()?.item_count ?? 0;
  }

  protected get subtotal(): string {
    return this.cart()?.subtotal ?? '0.00';
  }

  protected get discount(): string {
    return this.cart()?.discount_amount ?? '0.00';
  }

  protected get total(): string {
    return this.cart()?.total_amount ?? '0.00';
  }

  protected async refresh(): Promise<void> {
    await this.loadCart();
  }

  protected async increase(itemId: string, quantity: number): Promise<void> {
    await this.updateQuantity(itemId, quantity + 1);
  }

  protected async decrease(itemId: string, quantity: number): Promise<void> {
    await this.updateQuantity(itemId, quantity - 1);
  }

  protected async remove(itemId: string): Promise<void> {
    this.updatingItemId.set(itemId);
    try {
      const response = await requestWithToast(
        this.cartApi.removeItem(itemId),
        { loading: 'Eliminando item...', success: 'Item eliminado.', error: 'No se pudo eliminar el item.' },
      );
      this.cart.set(response.data ?? null);
    } catch {
      // toast handled by requestWithToast
    } finally {
      this.updatingItemId.set(null);
    }
  }

  protected async clear(): Promise<void> {
    try {
      const response = await requestWithToast(
        this.cartApi.clearCart(),
        { loading: 'Vaciando carrito...', success: 'Carrito vaciado.', error: 'No se pudo vaciar el carrito.' },
      );
      this.cart.set(response.data ?? null);
    } catch {
      // toast handled by requestWithToast
    }
  }

  protected lineTotal(item: { line_total: string }): string {
    return item.line_total;
  }

  private async loadCart(): Promise<void> {
    this.loading.set(true);
    try {
      const response = await firstValueFrom(this.cartApi.getCurrentCart());
      this.cart.set(response.data ?? null);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo cargar el carrito.'));
      this.cart.set(null);
    } finally {
      this.loading.set(false);
    }
  }

  private async updateQuantity(itemId: string, quantity: number): Promise<void> {
    if (quantity < 0) {
      return;
    }
    this.updatingItemId.set(itemId);
    try {
      const response = await requestWithToast(
        this.cartApi.updateItem(itemId, { quantity }),
        { loading: 'Actualizando carrito...', success: 'Carrito actualizado.', error: 'No se pudo actualizar el carrito.' },
      );
      this.cart.set(response.data ?? null);
    } catch {
      // toast handled by requestWithToast
    } finally {
      this.updatingItemId.set(null);
    }
  }
}
