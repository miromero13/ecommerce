import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideHeart, lucideMapPin, lucideShoppingCart, lucideStore, lucideTrash2 } from '@ng-icons/lucide';
import { toast } from '@spartan-ng/brain/sonner';

import { HlmButton } from '../../../components/button/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { WishlistItem } from '../../shared/models/wishlist.model';
import { WishlistApiService } from '../../shared/services/wishlist-api.service';

interface WishlistGroup {
  tenantId: string;
  tenantName: string;
  branchId: string;
  branchName: string;
  items: WishlistItem[];
}

/** CU16: the customer's favorites grouped by company and branch. */
@Component({
  selector: 'app-wishlist-page',
  standalone: true,
  imports: [CommonModule, RouterLink, HlmButton, NgIcon],
  providers: [
    provideIcons({
      lucideHeart,
      lucideMapPin,
      lucideShoppingCart,
      lucideStore,
      lucideTrash2,
    }),
  ],
  template: `
    <section class="space-y-6 text-slate-700">
      <header>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
          <ng-icon name="lucideHeart" class="text-rose-600" /> Lista de deseos
        </h1>
        <p class="text-sm text-slate-500">Tus prendas favoritas organizadas por tienda y sucursal. Puedes mover prendas individuales o agregar todo el lote de una sucursal al carrito.</p>
      </header>

      @if (groups().length === 0) {
        <div class="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center">
          <ng-icon name="lucideHeart" class="mx-auto text-4xl text-slate-300" />
          <h3 class="mt-3 text-base font-semibold text-slate-800">Aún no guardaste prendas</h3>
          <p class="mt-1 text-sm text-slate-500">Explora el catálogo y usa el icono de corazón para agregar tus prendas favoritas.</p>
          <div class="mt-5">
            <a hlmBtn routerLink="/app/cliente/catalog">Ir al catálogo</a>
          </div>
        </div>
      }

      <div class="space-y-6">
        @for (group of groups(); track group.tenantId + '_' + group.branchId) {
          <div class="rounded-2xl border border-slate-200 bg-slate-50/60 p-5 space-y-4 shadow-2xs">
            <!-- Encabezado de la Sucursal -->
            <div class="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200/90 pb-3">
              <div class="space-y-0.5">
                <div class="flex items-center gap-2">
                  <span class="inline-flex items-center gap-1.5 rounded-md bg-slate-900 px-2.5 py-1 text-xs font-semibold text-white">
                    <ng-icon name="lucideStore" /> {{ group.tenantName }}
                  </span>
                  <span class="inline-flex items-center gap-1 rounded-md bg-white border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-700">
                    <ng-icon name="lucideMapPin" class="text-slate-500" /> {{ group.branchName }}
                  </span>
                </div>
                <p class="text-xs text-slate-500 pt-0.5">{{ group.items.length }} prenda(s) disponible(s) en esta sucursal</p>
              </div>

              @if (group.branchId) {
                <button
                  hlmBtn
                  type="button"
                  class="gap-2 cursor-pointer shadow-xs bg-slate-900 hover:bg-slate-800 text-white"
                  [disabled]="busyGroupId() === group.branchId"
                  (click)="moveAll(group)"
                >
                  <ng-icon name="lucideShoppingCart" />
                  {{ busyGroupId() === group.branchId ? 'Agregando...' : 'Agregar todo al carrito' }}
                </button>
              }
            </div>

            <!-- Grilla de prendas de esa sucursal -->
            <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              @for (item of group.items; track item.id) {
                <article class="flex flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xs transition-all hover:shadow-xs">
                  <a [routerLink]="['/app/cliente/products', item.product_id]" class="h-48 bg-slate-100 block overflow-hidden">
                    @if (item.image_url) {
                      <img [src]="item.image_url" [alt]="item.product_name" class="h-full w-full object-cover transition-transform hover:scale-105" />
                    }
                  </a>
                  <div class="flex flex-1 flex-col gap-2 p-3.5">
                    <p class="font-semibold text-slate-900 line-clamp-1" [title]="item.product_name">{{ item.product_name }}</p>
                    <p class="text-sm font-bold text-slate-800">{{ item.price | number: '1.2-2' }} BOB</p>

                    @if (item.in_stock) {
                      <div class="space-y-1">
                        <label class="text-[11px] font-medium text-slate-500">Talla y color:</label>
                        <select class="h-8 w-full rounded-md border border-slate-300 bg-white px-2 text-xs" [value]="variantFor(item, group.branchId)" (change)="choose(item, $event)">
                          @for (variant of availableVariants(item, group.branchId); track variant.id) {
                            <option [value]="variant.id" [disabled]="variant.available < 1">
                              {{ variant.size || 'Única' }} · {{ variant.color || 'Sin color' }}{{ variant.available < 1 ? ' (agotado)' : '' }}
                            </option>
                          }
                        </select>
                      </div>
                    } @else {
                      <p class="text-xs font-medium text-amber-700">Sin stock en esta sucursal</p>
                    }

                    <div class="mt-auto flex gap-2 pt-2">
                      <button
                        hlmBtn
                        type="button"
                        class="flex-1 text-xs h-8"
                        [disabled]="!item.in_stock || busyId() === item.product_id"
                        (click)="move(item, group.branchId)"
                      >
                        Mover al carrito
                      </button>
                      <button
                        hlmBtn
                        type="button"
                        variant="outline"
                        size="icon"
                        class="h-8 w-8 text-rose-600 hover:text-rose-700 hover:bg-rose-50"
                        [disabled]="busyId() === item.product_id"
                        (click)="remove(item)"
                        title="Quitar de favoritos"
                      >
                        <ng-icon name="lucideTrash2" />
                      </button>
                    </div>
                  </div>
                </article>
              }
            </div>
          </div>
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
  protected readonly busyGroupId = signal<string | null>(null);

  protected readonly groups = computed<WishlistGroup[]>(() => {
    const items = this.items();
    const map = new Map<string, WishlistGroup>();

    for (const item of items) {
      const tenantId = item.tenant_id;
      const tenantName = item.tenant_name || 'Tienda';
      const branches = item.available_branches ?? [];

      if (branches.length === 0) {
        const key = `${tenantId}_none`;
        if (!map.has(key)) {
          map.set(key, {
            tenantId,
            tenantName,
            branchId: '',
            branchName: 'Sin sucursal con stock',
            items: [],
          });
        }
        map.get(key)!.items.push(item);
      } else {
        for (const br of branches) {
          const key = `${tenantId}_${br.branch_id}`;
          if (!map.has(key)) {
            map.set(key, {
              tenantId,
              tenantName,
              branchId: br.branch_id,
              branchName: `${br.branch_name} (${br.city})`,
              items: [],
            });
          }
          map.get(key)!.items.push(item);
        }
      }
    }

    return Array.from(map.values());
  });

  constructor() {
    void this.load();
  }

  protected availableVariants(item: WishlistItem, branchId?: string) {
    if (!branchId) return item.variants;
    // Filter or highlight variants that have stock in this branch
    const filtered = item.variants.filter((v) =>
      (v.branch_stocks ?? []).some((b) => b.branch_id === branchId && (b.quantity ?? 0) > 0),
    );
    return filtered.length > 0 ? filtered : item.variants;
  }

  protected variantFor(item: WishlistItem, branchId?: string): string {
    const selected = this.chosen()[item.product_id];
    if (selected) return selected;
    const variants = this.availableVariants(item, branchId);
    return variants.find((v) => v.available > 0)?.id ?? item.variants[0]?.id ?? '';
  }

  protected choose(item: WishlistItem, event: Event): void {
    this.chosen.update((chosen) => ({ ...chosen, [item.product_id]: (event.target as HTMLSelectElement).value }));
  }

  // [CU16 - Secuencia: Paso 3] El Cliente ejecuta move(item, branchId) en WishlistPageComponent
  protected async move(item: WishlistItem, branchId?: string): Promise<void> {
    const vId = this.variantFor(item, branchId);
    await this.run(item, () => this.wishlist.moveToCart(item.product_id, vId, branchId), 'No se pudo mover la prenda al carrito.');
  }

  // [CU16 - Secuencia: Paso 4] El Cliente ejecuta moveAll(group) en WishlistPageComponent
  protected async moveAll(group: WishlistGroup): Promise<void> {
    this.busyGroupId.set(group.branchId);
    try {
      const message = await this.wishlist.moveAllToCart(group.tenantId, group.branchId, true);
      toast.success(message);
      await this.load();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron mover las prendas de esta sucursal al carrito.'));
    } finally {
      this.busyGroupId.set(null);
    }
  }

  // [CU16 - Secuencia: Paso 5] El Cliente ejecuta remove(item) en WishlistPageComponent
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

  // [CU16 - Secuencia: Paso 1] El Cliente ejecuta load() en WishlistPageComponent
  private async load(): Promise<void> {
    try {
      this.items.set(await this.wishlist.reload());
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo cargar tu lista de deseos.'));
    }
  }
}
