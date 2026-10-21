import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideAlertTriangle, lucideBookmark, lucideCalendar, lucideShoppingCart } from '@ng-icons/lucide';

import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { requestWithToast } from '../../../core/utils/request-toast.util';
import {
  BranchStockInfo,
  CatalogBranch,
  CatalogCollectionItem,
  CatalogNameItem,
  CatalogProduct,
  CatalogProductVariant,
} from '../../shared/models/catalog.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { CartApiService } from '../../shared/services/cart-api.service';
import { ChatbotUiService } from '../../shared/services/chatbot-ui.service';
import { ReservationDraftService } from '../../shared/services/reservation-draft.service';
import { VirtualTryOnComponent } from '../../shared/components/virtual-try-on.component';
import { DetectorRopaComponent } from '../../shared/components/detector-ropa.component';
import { DetectorMediapipeComponent } from '../../shared/components/detector-mediapipe.component';

export interface StoreConflictModal {
  type: 'cart' | 'reservation';
  product: CatalogProduct;
  variant: CatalogProductVariant;
  newBranchId: string;
  newBranchName: string;
  newTenantName: string;
  currentName: string;
}

@Component({
  selector: 'app-product-detail-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    NgIcon,
    HlmButton,
    VirtualTryOnComponent,
    DetectorRopaComponent,
    DetectorMediapipeComponent,
    ...HlmBadgeImports,
    ...HlmCardImports,
  ],
  providers: [provideIcons({ lucideShoppingCart, lucideCalendar, lucideBookmark, lucideAlertTriangle })],
  templateUrl: './product-detail-page.component.html',
})
export class ProductDetailPageComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly api = inject(CatalogApiService);
  private readonly cartApi = inject(CartApiService);
  protected readonly reservationDraft = inject(ReservationDraftService);
  private readonly chatbotUi = inject(ChatbotUiService);

  protected readonly product = signal<CatalogProduct | null>(null);
  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly conflictModal = signal<StoreConflictModal | null>(null);
  protected readonly sizes = signal<CatalogNameItem[]>([]);
  protected readonly colors = signal<CatalogNameItem[]>([]);
  protected readonly categories = signal<CatalogNameItem[]>([]);
  protected readonly collections = signal<CatalogCollectionItem[]>([]);
  protected readonly selectedVariantId = signal<string | null>(null);
  protected readonly loading = signal(true);
  protected readonly addingToCart = signal(false);
  protected readonly origin = signal('/app/cliente');

  constructor() {
    this.chatbotUi.requestClose();
    void this.loadProduct();
  }

  protected variants(): CatalogProductVariant[] {
    return this.product()?.variants ?? [];
  }

  protected selectedVariant(): CatalogProductVariant | null {
    const variants = this.variants();
    return variants.find((variant) => variant.id === this.selectedVariantId()) ?? variants[0] ?? null;
  }

  protected selectVariant(variantId: string): void {
    this.selectedVariantId.set(variantId);
  }

  protected variantLabel(variant: CatalogProductVariant): string {
    const size = this.sizes().find((item) => item.id === variant.size_id)?.name ?? 'Sin talla';
    const color = this.colors().find((item) => item.id === variant.color_id)?.name ?? 'Sin color';
    return `${size} / ${color}`;
  }

  protected hasDiscount(variant: CatalogProductVariant | null): boolean {
    if (!variant || !variant.original_price) return false;
    return Number(variant.original_price) > Number(variant.price);
  }

  protected getVariantQuantity(variant: CatalogProductVariant | null): number {
    if (!variant) return 0;
    const branchId = this.route.snapshot.queryParamMap.get('branch_id');
    if (branchId) {
      const stock = (variant.branch_stocks ?? []).find((s) => s.branch_id === branchId);
      return stock ? stock.quantity : (variant.branch_quantity ?? 0);
    }
    return variant.total_stock ?? variant.branch_quantity ?? 0;
  }

  protected availabilityText(variant: CatalogProductVariant | null): string {
    if (!variant) return 'Sin datos';
    const qty = this.getVariantQuantity(variant);
    if (qty > 0) {
      return `${qty} unidades disponibles`;
    }
    return 'Agotado';
  }

  protected categoryName(): string {
    const catId = this.product()?.category_id;
    return this.categories().find((c) => c.id === catId)?.name ?? 'Sin categoría';
  }

  protected collectionName(): string {
    const colId = this.product()?.collection_id;
    return this.collections().find((c) => c.id === colId)?.name ?? 'Sin colección';
  }

  protected resolveBranchInfo(
    product: CatalogProduct,
    variant: CatalogProductVariant,
    preferredBranchId?: string,
  ): { branchId: string; branchName: string; tenantName: string } {
    const bId = preferredBranchId || this.route.snapshot.queryParamMap.get('branch_id');
    if (bId) {
      const b = this.branches().find((item) => item.id === bId);
      const bName = b ? `${b.name} (${b.city})` : 'Sucursal';
      const tName = product.tenant_name || 'Tienda';
      return { branchId: bId, branchName: bName, tenantName: tName };
    }
    const stock =
      (variant.branch_stocks ?? []).find((s) => s.quantity > 0) ||
      variant.branch_stocks?.[0];
    if (stock) {
      const b = this.branches().find((item) => item.id === stock.branch_id);
      const tName = product.tenant_name || 'Tienda';
      return {
        branchId: stock.branch_id,
        branchName: `${stock.branch_name} (${stock.city})`,
        tenantName: tName,
      };
    }
    const defB = this.branches()[0];
    const bName = defB ? `${defB.name} (${defB.city})` : 'Sucursal';
    const tName = product.tenant_name || 'Tienda';
    return { branchId: defB?.id || '', branchName: bName, tenantName: tName };
  }

  private getCartBranchId(): string {
    try {
      return localStorage.getItem('fashionstore_cart_branch_id') || '';
    } catch {
      return '';
    }
  }

  private getCartBranchName(): string {
    try {
      return localStorage.getItem('fashionstore_cart_branch_name') || '';
    } catch {
      return '';
    }
  }

  private setCartBranch(branchId: string, branchName: string): void {
    try {
      localStorage.setItem('fashionstore_cart_branch_id', branchId);
      localStorage.setItem('fashionstore_cart_branch_name', branchName);
    } catch {}
  }

  private clearCartBranch(): void {
    try {
      localStorage.removeItem('fashionstore_cart_branch_id');
      localStorage.removeItem('fashionstore_cart_branch_name');
    } catch {}
  }

  protected addToReservation(): void {
    const prod = this.product();
    const variant = this.selectedVariant();
    if (!prod || !variant) {
      toast.warning('Selecciona una variante primero.');
      return;
    }
    const info = this.resolveBranchInfo(prod, variant);
    if (this.reservationDraft.hasBranchConflict(info.branchId)) {
      const currentName = this.reservationDraft.selectedBranchName()
        ? `${this.reservationDraft.selectedTenantName()} — ${this.reservationDraft.selectedBranchName()}`
        : 'otra sucursal';
      this.conflictModal.set({
        type: 'reservation',
        product: prod,
        variant,
        newBranchId: info.branchId,
        newBranchName: info.branchName,
        newTenantName: info.tenantName,
        currentName,
      });
      return;
    }

    this.reservationDraft.addItem(prod, variant, info.branchId, info.branchName, info.tenantName);
  }

  protected getReservationCount(): number {
    const prod = this.product();
    return prod ? this.reservationDraft.getQuantityForProduct(prod) : 0;
  }

  protected async addToCart(): Promise<void> {
    const prod = this.product();
    const variant = this.selectedVariant();
    if (!prod || !variant) {
      toast.warning('Selecciona una variante primero.');
      return;
    }
    const info = this.resolveBranchInfo(prod, variant);
    const cartBranchId = this.getCartBranchId();

    if (cartBranchId && info.branchId && cartBranchId !== info.branchId) {
      const currentName = this.getCartBranchName() || 'otra sucursal';
      this.conflictModal.set({
        type: 'cart',
        product: prod,
        variant,
        newBranchId: info.branchId,
        newBranchName: info.branchName,
        newTenantName: info.tenantName,
        currentName,
      });
      return;
    }

    await this.executeAddToCart(prod, variant, info.branchId, info.branchName);
  }

  protected async executeAddToCart(
    product: CatalogProduct,
    variant: CatalogProductVariant,
    branchId: string,
    branchName: string,
  ): Promise<void> {
    this.addingToCart.set(true);
    try {
      await requestWithToast(
        this.cartApi.addItem({
          variant_id: variant.id,
          branch_id: branchId || undefined,
          quantity: 1,
        }),
        {
          loading: 'Agregando al carrito...',
          success: 'Producto agregado al carrito.',
          error: 'No se pudo agregar al carrito.',
        },
      );
      if (branchId) {
        this.setCartBranch(branchId, branchName);
      }
    } catch {
      // El error ya se mostró con requestWithToast
    } finally {
      this.addingToCart.set(false);
    }
  }

  protected closeConflictModal(): void {
    this.conflictModal.set(null);
  }

  protected async confirmConflictSwitch(): Promise<void> {
    const modal = this.conflictModal();
    if (!modal) return;

    if (modal.type === 'reservation') {
      this.reservationDraft.resetAndAddItem(
        modal.product,
        modal.variant,
        modal.newBranchId,
        modal.newBranchName,
        modal.newTenantName,
      );
      this.closeConflictModal();
      return;
    }

    if (modal.type === 'cart') {
      try {
        await firstValueFrom(this.cartApi.clearCart());
        this.clearCartBranch();
        this.closeConflictModal();
        await this.executeAddToCart(
          modal.product,
          modal.variant,
          modal.newBranchId,
          modal.newBranchName,
        );
      } catch (err) {
        toast.error(getErrorMessage(err, 'No se pudo vaciar el carrito.'));
        this.closeConflictModal();
      }
    }
  }

  protected goBack(): void {
    void this.router.navigateByUrl(this.origin());
  }

  private async loadProduct(): Promise<void> {
    try {
      const productId = this.route.snapshot.paramMap.get('productId');
      if (!productId) throw new Error('Producto inválido');

      const query = this.route.snapshot.queryParamMap;
      const from = query.get('from');
      this.origin.set(from === 'reservations' ? '/app/cliente/reservations' : from === 'catalog' ? '/app/cliente/catalog' : '/app/cliente');
      const [productResponse, sizes, colors, categories, collections, branches] = await Promise.all([
        firstValueFrom(this.api.getProduct(productId, query.get('branch_id') ?? undefined)),
        firstValueFrom(this.api.listSizes()),
        firstValueFrom(this.api.listColors()),
        firstValueFrom(this.api.listCategories()),
        firstValueFrom(this.api.listCollections()),
        firstValueFrom(this.api.listPublicBranches()),
      ]);
      this.product.set(productResponse.data ?? null);
      this.selectedVariantId.set(productResponse.data?.variants?.[0]?.id ?? null);
      this.sizes.set(sizes.data ?? []);
      this.colors.set(colors.data ?? []);
      this.categories.set(categories.data ?? []);
      this.collections.set(collections.data ?? []);
      this.branches.set(branches.data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo cargar el producto.'));
    } finally {
      this.loading.set(false);
    }
  }
}
