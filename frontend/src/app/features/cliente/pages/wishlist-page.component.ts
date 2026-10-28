import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { toast } from '@spartan-ng/brain/sonner';

import { HlmButton } from '../../../components/button/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { WishlistItem } from '../../shared/models/wishlist.model';
import { WishlistApiService } from '../../shared/services/wishlist-api.service';

/** CU16: the customer's favorites; each one can be moved to the cart choosing size/color. */
@Component({
  selector: 'app-wishlist-page',
  standalone: true,
  imports: [CommonModule, RouterLink, HlmButton],
  template: `
    <section class="space-y-5 text-slate-700">
      <header>
        <h1 class="text-2xl font-semibold">Lista de deseos</h1>
        <p class="text-sm text-slate-500">Tus prendas favoritas. Elige talla y color para moverlas al carrito.</p>
      </header>
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        @for (item of items(); track item.id) {
          <article class="flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <a [routerLink]="['/app/cliente/products', item.product_id]" class="h-52 bg-slate-100">
              @if (item.image_url) { <img [src]="item.image_url" [alt]="item.product_name" class="h-full w-full object-cover" /> }
            </a>
            <div class="flex flex-1 flex-col gap-2 p-4">
              <p class="font-semibold text-slate-900">{{ item.product_name }}</p>
              <p class="text-xs text-slate-500">{{ item.tenant_name }}</p>
              <p class="text-sm font-medium">{{ item.price | number: '1.2-2' }} BOB</p>
              @if (item.in_stock) {
                <select class="h-9 rounded-md border border-slate-300 bg-white px-2 text-sm" [value]="variantFor(item)" (change)="choose(item, $event)">
                  @for (variant of item.variants; track variant.id) {
                    <option [value]="variant.id" [disabled]="variant.available < 1">
                      {{ variant.size || 'Única' }} · {{ variant.color || 'Sin color' }}{{ variant.available < 1 ? ' (agotado)' : '' }}
                    </option>
                  }
                </select>
              } @else {
                <p class="text-xs font-medium text-amber-700">Sin stock por ahora</p>
              }
              <div class="mt-auto flex gap-2 pt-2">
                <button hlmBtn type="button" class="flex-1" [disabled]="!item.in_stock || busyId() === item.product_id" (click)="move(item)">Mover al carrito</button>
                <button hlmBtn type="button" variant="outline" [disabled]="busyId() === item.product_id" (click)="remove(item)">Quitar</button>
              </div>
            </div>
          </article>
        } @empty {
          <p class="text-sm text-slate-500">Aún no guardaste prendas. Usa el corazón del catálogo para añadirlas.</p>
        }
      </div>
    </section>
  `,
})
export class WishlistPageComponent {
  private readonly wishlist = inject(WishlistApiService);
  protected readonly items = signal<WishlistItem[]>([]);
  protected readonly chosen = signal<Partial<Record<string, string>>>({});
  protected readonly busyId = signal<string | null>(null);

  constructor() {
    void this.load();
  }

  /** Default to the first variant with stock. */
  protected variantFor(item: WishlistItem): string {
    return this.chosen()[item.product_id] ?? item.variants.find((v) => v.available > 0)?.id ?? '';
  }

  protected choose(item: WishlistItem, event: Event): void {
    this.chosen.update((chosen) => ({ ...chosen, [item.product_id]: (event.target as HTMLSelectElement).value }));
  }

  protected async move(item: WishlistItem): Promise<void> {
    await this.run(item, () => this.wishlist.moveToCart(item.product_id, this.variantFor(item)), 'No se pudo mover la prenda al carrito.');
  }

  protected async remove(item: WishlistItem): Promise<void> {
    await this.run(item, () => this.wishlist.toggle(item.product_id), 'No se pudo quitar la prenda.');
  }

  private async run(item: WishlistItem, action: () => Promise<string>, fallback: string): Promise<void> {
    this.busyId.set(item.product_id);
    try {
      toast.success(await action());
      await this.load();
    } catch (error) {
      toast.error(getErrorMessage(error, fallback));
    } finally {
      this.busyId.set(null);
    }
  }

  private async load(): Promise<void> {
    try {
      this.items.set(await this.wishlist.reload());
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo cargar tu lista de deseos.'));
    }
  }
}
