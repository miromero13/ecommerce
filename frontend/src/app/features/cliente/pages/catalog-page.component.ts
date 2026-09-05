import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

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
  CatalogBranch,
  CatalogCollectionItem,
  CatalogColorItem,
  CatalogNameItem,
  CatalogProduct,
  CatalogProductVariant,
} from '../../shared/models/catalog.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';

@Component({
  selector: 'app-catalog-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HlmButton, HlmInput, ...HlmBadgeImports, ...HlmCardImports, ...HlmFieldImports, ...HlmSelectImports],
  templateUrl: './catalog-page.component.html',
})
export class CatalogPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(CatalogApiService);

  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly categories = signal<CatalogNameItem[]>([]);
  protected readonly sizes = signal<CatalogNameItem[]>([]);
  protected readonly colors = signal<CatalogColorItem[]>([]);
  protected readonly seasons = signal<CatalogNameItem[]>([]);
  protected readonly collections = signal<CatalogCollectionItem[]>([]);
  protected readonly products = signal<CatalogProduct[]>([]);
  protected readonly selectedVariantByProduct = signal<Record<string, string>>({});
  protected readonly loading = signal(false);

  protected readonly form = this.fb.nonNullable.group({
    q: [''],
    branch_id: [''],
    category_id: [''],
    size_id: [''],
    color_id: [''],
    season_id: [''],
    collection_id: [''],
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

  constructor() {
    void this.loadData();
  }

  protected async search(): Promise<void> {
    this.loading.set(true);
    try {
      const value = this.form.getRawValue();
      const response = await requestWithToast(
        this.api.listProducts({
          q: value.q || undefined,
          branch_id: value.branch_id || undefined,
          category_id: value.category_id || undefined,
          size_id: value.size_id || undefined,
          color_id: value.color_id || undefined,
          season_id: value.season_id || undefined,
          collection_id: value.collection_id || undefined,
        }),
        { loading: 'Consultando catálogo...', success: 'Catálogo actualizado.', error: 'No se pudo consultar el catálogo.' },
      );
      this.products.set(response.data ?? []);
      this.ensureSelectedVariants();
    } catch {
      // El toast de error ya se mostró con requestWithToast
    } finally {
      this.loading.set(false);
    }
  }

  protected async updateBranchAvailability(): Promise<void> {
    await this.search();
  }

  private async loadData(): Promise<void> {
    try {
      const [branches, categories, sizes, colors, seasons, collections, products] = await Promise.all([
        firstValueFrom(this.api.listPublicBranches()),
        firstValueFrom(this.api.listCategories()),
        firstValueFrom(this.api.listSizes()),
        firstValueFrom(this.api.listColors()),
        firstValueFrom(this.api.listSeasons()),
        firstValueFrom(this.api.listCollections()),
        firstValueFrom(this.api.listProducts()),
      ]);
      this.branches.set(branches.data ?? []);
      this.categories.set(categories.data ?? []);
      this.sizes.set(sizes.data ?? []);
      this.colors.set(colors.data ?? []);
      this.seasons.set(seasons.data ?? []);
      this.collections.set(collections.data ?? []);
      this.products.set(products.data ?? []);
      this.ensureSelectedVariants();
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
    return this.collections().find((collection) => collection.id === collectionId)?.name ?? collectionId;
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

  protected variantSelectLabel(product: CatalogProduct): (variantId: string | null | undefined) => string {
    return (variantId: string | null | undefined): string => {
      if (!variantId) return 'Variante';
      const variant = this.productVariants(product).find((item) => item.id === variantId);
      return variant ? `${this.variantLabel(variant)} - ${variant.price}` : variantId;
    };
  }

  protected availabilityLabel(variant: CatalogProductVariant | null, branchId: string | null): string {
    if (!branchId) {
      return 'Selecciona una sucursal para ver stock';
    }
    if (!variant) {
      return 'Sin variante seleccionada';
    }
    return `${variant.branch_quantity ?? 0} unidades`;
  }

  protected variantStock(variant: CatalogProductVariant | null): number | null {
    return variant?.branch_quantity ?? null;
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
}
