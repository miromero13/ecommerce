import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { debounceTime, distinctUntilChanged, firstValueFrom } from 'rxjs';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  lucideAlertTriangle,
  lucideBookmark,
  lucideCalendar,
  lucideChevronDown,
  lucideEye,
  lucideRotateCcw,
  lucideSearch,
  lucideShoppingCart,
  lucideX,
} from '@ng-icons/lucide';

import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInput } from '../../../components/input/src';
import { HlmSelectImports } from '../../../components/select/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { requestWithToast } from '../../../core/utils/request-toast.util';
import {
  BranchStockInfo,
  CatalogBranch,
  CatalogCollectionItem,
  CatalogColorItem,
  CatalogNameItem,
  CatalogProduct,
  CatalogProductVariant,
} from '../../shared/models/catalog.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { CartApiService } from '../../shared/services/cart-api.service';
import { SessionService } from '../../shared/services/session.service';
import { TenantApiService } from '../../shared/services/tenant-api.service';
import { ReservationDraftService } from '../../shared/services/reservation-draft.service';

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
  selector: 'app-catalog-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    ReactiveFormsModule,
    NgIcon,
    HlmButton,
    HlmInput,
    ...HlmBadgeImports,
    ...HlmCardImports,
    ...HlmFieldImports,
    ...HlmSelectImports,
  ],
  providers: [
    provideIcons({
      lucideShoppingCart,
      lucideEye,
      lucideCalendar,
      lucideBookmark,
      lucideAlertTriangle,
      lucideSearch,
      lucideX,
      lucideRotateCcw,
      lucideChevronDown,
    }),
  ],
  templateUrl: './catalog-page.component.html',
})
export class CatalogPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(CatalogApiService);
  private readonly cartApi = inject(CartApiService);
  private readonly session = inject(SessionService);
  private readonly tenantApi = inject(TenantApiService);
  protected readonly reservationDraft = inject(ReservationDraftService);
  private readonly router = inject(Router);

  protected readonly tenants = signal<Array<{ id: string; name: string; slug: string; currency: string; country: string }>>([]);
  protected readonly selectedTenantId = signal<string>('');
  protected readonly selectedBranchId = signal<string>('');
  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly categories = signal<CatalogNameItem[]>([]);
  protected readonly sizes = signal<CatalogNameItem[]>([]);
  protected readonly colors = signal<CatalogColorItem[]>([]);
  protected readonly seasons = signal<CatalogNameItem[]>([]);
  protected readonly collections = signal<CatalogCollectionItem[]>([]);
  protected readonly products = signal<CatalogProduct[]>([]);
  protected readonly recommendedProducts = signal<CatalogProduct[]>([]);
  protected readonly selectedVariantByProduct = signal<Record<string, string>>({});
  protected readonly selectedImageByProduct = signal<Record<string, number>>({});
  protected readonly addingToCartByProduct = signal<Record<string, boolean>>({});
  protected readonly loading = signal(false);
  private recommendationsRequestVersion = 0;

  protected readonly filteredBranches = computed(() => {
    const tenantId = this.selectedTenantId();
    if (!tenantId) return this.branches();
    return this.branches().filter((b: any) => !b.tenant_id || b.tenant_id === tenantId);
  });

  protected readonly currentBranchDisplay = computed(() => {
    const bId = this.selectedBranchId();
    if (!bId) return '';
    const b = this.branches().find((item) => item.id === bId);
    if (!b) return '';
    const tenant = this.tenants().find((t) => t.id === b.tenant_id);
    return `${tenant?.name || 'Tienda'} — ${b.name} (${b.city})`;
  });

  protected readonly currentBranchProducts = computed(() => {
    const bId = this.selectedBranchId();
    if (!bId) return this.products();
    return this.products().filter((p) => {
      return (p.variants ?? []).some((v) => {
        const stock = (v.branch_stocks ?? []).find((s) => s.branch_id === bId);
        return stock ? stock.quantity > 0 : true;
      });
    });
  });

  protected readonly branchSections = computed<Array<{
    branchId: string;
    branchName: string;
    cityName: string;
    tenantName: string;
    products: CatalogProduct[];
  }>>(() => {
    const targetBranches = this.filteredBranches();
    const allProducts = this.products();
    const sections: Array<{
      branchId: string;
      branchName: string;
      cityName: string;
      tenantName: string;
      products: CatalogProduct[];
    }> = [];

    for (const b of targetBranches) {
      const prods = allProducts.filter((p) => {
        if (b.tenant_id && p.tenant_id && b.tenant_id !== p.tenant_id) {
          return false;
        }
        return (p.variants ?? []).some((v) => {
          const stock = (v.branch_stocks ?? []).find((s) => s.branch_id === b.id);
          return stock ? stock.quantity > 0 : true;
        });
      });

      if (prods.length > 0) {
        const tenant = this.tenants().find((t) => t.id === b.tenant_id);
        sections.push({
          branchId: b.id,
          branchName: b.name,
          cityName: b.city,
          tenantName: tenant?.name || prods[0]?.tenant_name || 'Tienda',
          products: prods,
        });
      }
    }
    return sections;
  });

  protected readonly form = this.fb.nonNullable.group({
    q: [''],
    category_id: [''],
    size_id: [''],
    color_id: [''],
    season_id: [''],
    collection_id: [''],
  });

  protected readonly formFilterValues = signal(this.form.getRawValue());

  protected readonly hasActiveFilters = computed(() => {
    const v = this.formFilterValues();
    return !!(
      v.q?.trim() ||
      v.category_id ||
      v.size_id ||
      v.color_id ||
      v.season_id ||
      v.collection_id
    );
  });

  protected readonly branchSelectLabel = (branchId: string | null | undefined): string => {
    if (!branchId) return 'Sucursal';
    const branch = this.branches().find((item) => item.id === branchId);
    return branch ? `${branch.name} - ${branch.city}` : branchId;
  };

  protected readonly categorySelectLabel = (categoryId: string | null | undefined): string => {
    if (!categoryId) return 'Categoría';
    return this.categories().find((category) => category.id === categoryId)?.name ?? categoryId;
  };

  protected readonly sizeSelectLabel = (sizeId: string | null | undefined): string => {
    if (!sizeId) return 'Talla';
    return this.sizes().find((size) => size.id === sizeId)?.name ?? sizeId;
  };

  protected readonly colorSelectLabel = (colorId: string | null | undefined): string => {
    if (!colorId) return 'Color';
    return this.colors().find((color) => color.id === colorId)?.name ?? colorId;
  };

  protected readonly seasonSelectLabel = (seasonId: string | null | undefined): string => {
    if (!seasonId) return 'Temporada';
    return this.seasons().find((season) => season.id === seasonId)?.name ?? seasonId;
  };

  protected readonly collectionSelectLabel = (collectionId: string | null | undefined): string => {
    if (!collectionId) return 'Colección';
    const collection = this.collections().find((item) => item.id === collectionId);
    if (!collection) return collectionId;
    return `${collection.name} - ${this.seasonName(collection.season_id)}`;
  };

  protected productDetailOrigin(): string {
    return this.router.url.startsWith('/app/cliente/catalog') ? 'catalog' : 'catalog-home';
  }

  constructor() {
    void this.loadData();

    this.form.valueChanges
      .pipe(takeUntilDestroyed())
      .subscribe(() => {
        this.formFilterValues.set(this.form.getRawValue());
      });

    this.form.valueChanges
      .pipe(
        debounceTime(250),
        distinctUntilChanged((prev, curr) => JSON.stringify(prev) === JSON.stringify(curr)),
        takeUntilDestroyed(),
      )
      .subscribe(() => {
        void this.search(true);
      });
  }

  protected selectTenant(tenantId: string): void {
    this.selectedTenantId.set(tenantId);
    this.selectedBranchId.set('');
    void this.search(true);
  }

  protected selectBranch(branchId: string): void {
    this.selectedBranchId.set(branchId);
    void this.search(true);
  }

  protected resetFilters(): void {
    this.form.reset({
      q: '',
      category_id: '',
      size_id: '',
      color_id: '',
      season_id: '',
      collection_id: '',
    });
  }

  protected clearSearchInput(): void {
    this.form.controls.q.setValue('');
  }

  protected async search(silent = false): Promise<void> {
    this.loading.set(true);
    try {
      const value = this.form.getRawValue();
      const params = {
        q: value.q?.trim() || undefined,
        tenant_id: this.selectedTenantId() || undefined,
        branch_id: this.selectedBranchId() || undefined,
        category_id: value.category_id || undefined,
        size_id: value.size_id || undefined,
        color_id: value.color_id || undefined,
        season_id: value.season_id || undefined,
        collection_id: value.collection_id || undefined,
      };

      const response = silent
        ? await firstValueFrom(this.api.listProducts(params))
        : await requestWithToast(
            this.api.listProducts(params),
            {
              loading: 'Consultando catálogo...',
              success: 'Catálogo actualizado.',
              error: 'No se pudo consultar el catálogo.',
            },
          );
      this.products.set(response.data ?? []);
      this.ensureSelectedVariants();
      void this.loadRecommendations();
    } catch (error) {
      if (silent) {
        toast.error(getErrorMessage(error, 'No se pudo consultar el catálogo.'));
      }
    } finally {
      this.loading.set(false);
    }
  }

  protected async updateBranchAvailability(): Promise<void> {
    await this.search();
  }

  protected readonly conflictModal = signal<StoreConflictModal | null>(null);

  protected resolveBranchInfo(
    product: CatalogProduct,
    variant: CatalogProductVariant,
    preferredBranchId?: string,
  ): { branchId: string; branchName: string; tenantName: string } {
    const bId = preferredBranchId || this.selectedBranchId();
    if (bId) {
      const b = this.branches().find((item) => item.id === bId);
      const bName = b ? `${b.name} (${b.city})` : 'Sucursal';
      const tName =
        (b ? this.tenants().find((t) => t.id === b.tenant_id)?.name : null) ||
        product.tenant_name ||
        'Tienda';
      return { branchId: bId, branchName: bName, tenantName: tName };
    }
    const stock =
      (variant.branch_stocks ?? []).find((s) => s.quantity > 0) ||
      variant.branch_stocks?.[0];
    if (stock) {
      const b = this.branches().find((item) => item.id === stock.branch_id);
      const tName =
        (b ? this.tenants().find((t) => t.id === b.tenant_id)?.name : null) ||
        product.tenant_name ||
        'Tienda';
      return {
        branchId: stock.branch_id,
        branchName: `${stock.branch_name} (${stock.city})`,
        tenantName: tName,
      };
    }
    const defB = this.filteredBranches()[0] || this.branches()[0];
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

  protected addToReservation(product: CatalogProduct, preferredBranchId?: string): void {
    const variant = this.selectedVariant(product);
    if (!variant) {
      toast.warning('No se pudo identificar la variante.');
      return;
    }
    const info = this.resolveBranchInfo(product, variant, preferredBranchId);
    if (this.reservationDraft.hasBranchConflict(info.branchId)) {
      const currentName = this.reservationDraft.selectedBranchName()
        ? `${this.reservationDraft.selectedTenantName()} — ${this.reservationDraft.selectedBranchName()}`
        : 'otra sucursal';
      this.conflictModal.set({
        type: 'reservation',
        product,
        variant,
        newBranchId: info.branchId,
        newBranchName: info.branchName,
        newTenantName: info.tenantName,
        currentName,
      });
      return;
    }

    this.reservationDraft.addItem(
      product,
      variant,
      info.branchId,
      info.branchName,
      info.tenantName,
    );
  }

  protected getReservationCount(product: CatalogProduct): number {
    return this.reservationDraft.getQuantityForProduct(product);
  }

  protected async addSelectedVariantToCart(
    product: CatalogProduct,
    preferredBranchId?: string,
  ): Promise<void> {
    const variant = this.selectedVariant(product);
    if (!variant) {
      toast.warning('Selecciona una variante primero.');
      return;
    }

    const info = this.resolveBranchInfo(product, variant, preferredBranchId);
    // One cart per company: the backend rejects another company's item with a clear message.

    await this.executeAddToCart(product, variant, info.branchId, info.branchName);
  }

  protected async executeAddToCart(
    product: CatalogProduct,
    variant: CatalogProductVariant,
    branchId: string,
    branchName: string,
  ): Promise<void> {
    this.addingToCartByProduct.update((current) => ({ ...current, [product.id]: true }));
    try {
      void this.recordProductView(product.id);
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
      // Remember the first branch only, to preselect pickup in the cart.
      if (branchId && !this.getCartBranchId()) {
        this.setCartBranch(branchId, branchName);
      }
    } catch {
      // El toast de error ya se mostró con requestWithToast
    } finally {
      this.addingToCartByProduct.update((current) => ({ ...current, [product.id]: false }));
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

  private async loadData(): Promise<void> {
    try {
      const [branches, categories, sizes, colors, seasons, collections, products, tenants] =
        await Promise.all([
          firstValueFrom(this.api.listPublicBranches()),
          firstValueFrom(this.api.listCategories()),
          firstValueFrom(this.api.listSizes()),
          firstValueFrom(this.api.listColors()),
          firstValueFrom(this.api.listSeasons()),
          firstValueFrom(this.api.listCollections()),
          firstValueFrom(this.api.listProducts()),
          firstValueFrom(this.tenantApi.listPublicTenants()),
        ]);
      this.branches.set(branches.data ?? []);
      this.categories.set(categories.data ?? []);
      this.sizes.set(sizes.data ?? []);
      this.colors.set(colors.data ?? []);
      this.seasons.set(seasons.data ?? []);
      this.collections.set(collections.data ?? []);
      this.products.set(products.data ?? []);
      this.tenants.set(tenants.data ?? []);
      this.ensureSelectedVariants();
      void this.loadRecommendations();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo cargar el catálogo.'));
    }
  }

  protected branchName(branchId: string | null): string {
    if (!branchId) return 'Sin sucursal';
    return this.branches().find((branch) => branch.id === branchId)?.name ?? branchId;
  }

  protected categoryName(categoryId: string | null | undefined): string {
    if (!categoryId) return 'Sin categoría';
    return this.categories().find((category) => category.id === categoryId)?.name ?? categoryId;
  }

  protected sizeName(sizeId: string | null | undefined): string {
    if (!sizeId) return 'Sin talla';
    return this.sizes().find((size) => size.id === sizeId)?.name ?? sizeId;
  }

  protected colorName(colorId: string | null | undefined): string {
    if (!colorId) return 'Sin color';
    return this.colors().find((color) => color.id === colorId)?.name ?? colorId;
  }

  protected seasonName(seasonId: string | null | undefined): string {
    if (!seasonId) return 'Sin temporada';
    return this.seasons().find((season) => season.id === seasonId)?.name ?? seasonId;
  }

  protected collectionName(collectionId: string | null | undefined): string {
    if (!collectionId) return 'Sin colección';
    return (
      this.collections().find((collection) => collection.id === collectionId)?.name ?? collectionId
    );
  }

  protected collectionSeasonName(collectionId: string | null | undefined): string {
    if (!collectionId) return 'Sin temporada';
    const collection = this.collections().find((item) => item.id === collectionId);
    return this.seasonName(collection?.season_id);
  }

  protected productVariants(product: CatalogProduct): CatalogProductVariant[] {
    return product.variants ?? [];
  }

  protected selectedVariant(product: CatalogProduct): CatalogProductVariant | null {
    const variants = this.productVariants(product);
    if (!variants.length) {
      return null;
    }
    const selectedId = this.selectedVariantByProduct()[product.id];
    return variants.find((variant) => variant.id === selectedId) ?? variants[0] ?? null;
  }

  protected setSelectedVariant(productId: string, variantId: string | null | undefined): void {
    if (!variantId) {
      return;
    }

    this.selectedVariantByProduct.update((current) => ({
      ...current,
      [productId]: variantId,
    }));
  }

  protected variantLabel(variant: CatalogProductVariant): string {
    return `${this.sizeName(variant.size_id)} / ${this.colorName(variant.color_id)}`;
  }

  protected variantSelectLabel(
    product: CatalogProduct,
  ): (variantId: string | null | undefined) => string {
    return (variantId: string | null | undefined): string => {
      if (!variantId) return 'Variante';
      const variant = this.productVariants(product).find((item) => item.id === variantId);
      return variant ? `${this.variantLabel(variant)} - ${variant.price}` : variantId;
    };
  }

  protected hasDiscount(variant: CatalogProductVariant | null): boolean {
    if (!variant || !variant.original_price) return false;
    return Number(variant.original_price) > Number(variant.price);
  }

  protected availabilityLabel(
    variant: CatalogProductVariant | null,
    branchId: string | null,
  ): string {
    if (!variant) {
      return 'Sin variante seleccionada';
    }
    if (branchId) {
      return `${this.branchName(branchId)}: ${variant.branch_quantity ?? 0} unidades`;
    }
    const stocks = variant.branch_stocks ?? [];
    if (stocks.length === 0) {
      return (variant.branch_quantity ?? 0) > 0
        ? `${variant.branch_quantity} unidades`
        : 'Agotado en todas las sucursales';
    }
    const details = stocks.map((s) => `${s.branch_name} (${s.quantity} u.)`).join(' · ');
    return `${details} (Total: ${variant.total_stock ?? variant.branch_quantity ?? 0} u.)`;
  }

  protected variantStock(variant: CatalogProductVariant | null): number | null {
    return variant?.branch_quantity ?? null;
  }

  protected isAddingToCart(productId: string): boolean {
    return this.addingToCartByProduct()[productId] ?? false;
  }

  protected productImages(product: CatalogProduct): string[] {
    const images = new Set<string>();
    for (const variant of product.variants ?? []) {
      if (variant.image_url) {
        images.add(variant.image_url);
      }
    }
    if (product.image_url) {
      images.add(product.image_url);
    }
    return [...images];
  }

  protected currentProductImage(product: CatalogProduct): string | null {
    const images = this.productImages(product);
    if (!images.length) {
      return null;
    }
    return images[this.currentProductImageIndex(product)] ?? null;
  }

  protected currentProductImageIndex(product: CatalogProduct): number {
    const images = this.productImages(product);
    if (!images.length) {
      return 0;
    }
    const index = this.selectedImageByProduct()[product.id] ?? 0;
    return ((index % images.length) + images.length) % images.length;
  }

  protected previousProductImage(productId: string, total: number): void {
    this.selectedImageByProduct.update((current) => ({
      ...current,
      [productId]: ((current[productId] ?? 0) - 1 + total) % total,
    }));
  }

  protected nextProductImage(productId: string, total: number): void {
    this.selectedImageByProduct.update((current) => ({
      ...current,
      [productId]: ((current[productId] ?? 0) + 1) % total,
    }));
  }

  private ensureSelectedVariants(): void {
    const current = { ...this.selectedVariantByProduct() };
    for (const product of this.products()) {
      const variants = product.variants ?? [];
      if (!variants.length) continue;
      if (!current[product.id] || !variants.some((variant) => variant.id === current[product.id])) {
        current[product.id] = variants[0].id;
      }
    }
    this.selectedVariantByProduct.set(current);
  }

  private async loadRecommendations(): Promise<void> {
    const requestVersion = ++this.recommendationsRequestVersion;
    const user = this.session.user();
    if (!user || user.rol !== 'cliente') return;
    try {
      const response = await firstValueFrom(
        this.api.getCollaborativeRecommendations(user.id, {
          branch_id: this.selectedBranchId() || undefined,
        }),
      );
      const catalog = await firstValueFrom(this.api.listProducts({ branch_id: this.selectedBranchId() || undefined }));
      const productById = new Map((catalog.data ?? []).map((product) => [product.id, product]));
      if (requestVersion !== this.recommendationsRequestVersion) return;
      this.recommendedProducts.set(
        (response.data?.recommendations ?? [])
          .map((recommendation) => productById.get(recommendation.product_id))
          .filter((product): product is CatalogProduct => !!product),
      );
    } catch {
      if (requestVersion !== this.recommendationsRequestVersion) return;
      this.recommendedProducts.set([]);
    }
  }

  protected async recordProductView(productId: string): Promise<void> {
    try {
      const product = this.products().find((item) => item.id === productId);
      await firstValueFrom(this.api.recordProductView(productId, {
        variant_id: product ? this.selectedVariant(product)?.id : undefined,
        branch_id: this.selectedBranchId() || undefined,
      }));
    } catch {
      // View telemetry must never block the normal cart flow.
    }
  }
}
