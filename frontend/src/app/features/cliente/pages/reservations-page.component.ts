import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
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
import { CreateReservationRequest } from '../../shared/models/reservation.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { ReservationApiService } from '../../shared/services/reservation-api.service';
import { VirtualTryOnComponent } from '../../shared/components/virtual-try-on.component';
import { DetectorRopaComponent } from '../../shared/components/detector-ropa.component';
import { DetectorMediapipeComponent } from '../../shared/components/detector-mediapipe.component';

@Component({
  selector: 'app-reservations-page',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule, HlmButton, HlmInput, ...HlmBadgeImports, ...HlmCardImports, ...HlmFieldImports, ...HlmSelectImports],
  templateUrl: './reservations-page.component.html',
})
export class ReservationsPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly catalogApi = inject(CatalogApiService);
  private readonly reservationApi = inject(ReservationApiService);

  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly categories = signal<CatalogNameItem[]>([]);
  protected readonly sizes = signal<CatalogNameItem[]>([]);
  protected readonly colors = signal<CatalogColorItem[]>([]);
  protected readonly seasons = signal<CatalogNameItem[]>([]);
  protected readonly collections = signal<CatalogCollectionItem[]>([]);
  protected readonly products = signal<CatalogProduct[]>([]);
  protected readonly selectedVariantByProduct = signal<Record<string, string>>({});
  protected readonly selectedImageByProduct = signal<Record<string, number>>({});
  protected readonly draftByVariant = signal<Record<string, number>>({});
  protected readonly loading = signal(false);
  protected readonly submitting = signal(false);

  protected readonly form = this.fb.nonNullable.group({
    q: [''],
    branch_id: [''],
    category_id: [''],
    size_id: [''],
    color_id: [''],
    season_id: [''],
    collection_id: [''],
    visit_date: [''],
  });

  constructor() {
    void this.loadData();
  }

  protected branchSelectLabel = (branchId: string | null | undefined): string => {
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
    return collection ? `${collection.name} - ${this.seasonName(collection.season_id)}` : collectionId;
  };

  protected variantSelectLabel(product: CatalogProduct): (variantId: string | null | undefined) => string {
    return (variantId: string | null | undefined): string => {
      if (!variantId) return 'Variante';
      const variant = this.productVariants(product).find((item) => item.id === variantId);
      return variant ? `${this.variantLabel(variant)} - ${variant.price}` : variantId;
    };
  }

  protected categoryName(categoryId: string | null | undefined): string {
    return this.categories().find((category) => category.id === categoryId)?.name ?? 'Sin categoría';
  }

  protected collectionName(collectionId: string | null | undefined): string {
    return this.collections().find((collection) => collection.id === collectionId)?.name ?? 'Sin colección';
  }

  protected collectionSeasonName(collectionId: string | null | undefined): string {
    const collection = this.collections().find((item) => item.id === collectionId);
    return this.seasonName(collection?.season_id);
  }

  protected seasonName(seasonId: string | null | undefined): string {
    return this.seasons().find((season) => season.id === seasonId)?.name ?? 'Sin temporada';
  }

  protected productVariants(product: CatalogProduct): CatalogProductVariant[] {
    return product.variants ?? [];
  }

  protected selectedVariant(product: CatalogProduct): CatalogProductVariant | null {
    const variants = this.productVariants(product);
    if (!variants.length) return null;
    const selectedId = this.selectedVariantByProduct()[product.id];
    return variants.find((variant) => variant.id === selectedId) ?? variants[0] ?? null;
  }

  protected setSelectedVariant(productId: string, variantId: string | null | undefined): void {
    if (!variantId) return;
    this.selectedVariantByProduct.update((current) => ({ ...current, [productId]: variantId }));
  }

  protected async search(): Promise<void> {
    this.loading.set(true);
    try {
      const value = this.form.getRawValue();
      const response = await requestWithToast(
        this.catalogApi.listProducts({
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
      // Toast handled by requestWithToast.
    } finally {
      this.loading.set(false);
    }
  }

  protected updateBranchAvailability(): Promise<void> {
    return this.search();
  }

  protected variantLabel(variant: CatalogProductVariant): string {
    return `${this.sizeName(variant.size_id)} / ${this.colorName(variant.color_id)}`;
  }

  protected sizeName(sizeId: string | null | undefined): string {
    return this.sizes().find((size) => size.id === sizeId)?.name ?? 'Sin talla';
  }

  protected colorName(colorId: string | null | undefined): string {
    return this.colors().find((color) => color.id === colorId)?.name ?? 'Sin color';
  }

  protected availabilityLabel(variant: CatalogProductVariant | null, branchId: string | null): string {
    if (!branchId) return 'Selecciona una sucursal para ver stock';
    if (!variant) return 'Sin variante seleccionada';
    return `${variant.branch_quantity ?? 0} unidades`;
  }

  protected productImages(product: CatalogProduct): string[] {
    const images = new Set<string>();
    for (const variant of product.variants ?? []) {
      if (variant.image_url) images.add(variant.image_url);
    }
    if (product.image_url) images.add(product.image_url);
    return [...images];
  }

  protected currentProductImage(product: CatalogProduct): string | null {
    const images = this.productImages(product);
    return images[this.currentProductImageIndex(product)] ?? null;
  }

  protected currentProductImageIndex(product: CatalogProduct): number {
    const images = this.productImages(product);
    if (!images.length) return 0;
    const index = this.selectedImageByProduct()[product.id] ?? 0;
    return ((index % images.length) + images.length) % images.length;
  }

  protected previousProductImage(productId: string, total: number): void {
    this.selectedImageByProduct.update((current) => ({ ...current, [productId]: ((current[productId] ?? 0) - 1 + total) % total }));
  }

  protected nextProductImage(productId: string, total: number): void {
    this.selectedImageByProduct.update((current) => ({ ...current, [productId]: ((current[productId] ?? 0) + 1) % total }));
  }

  protected branchName(branchId: string | null | undefined): string {
    return this.branches().find((branch) => branch.id === branchId)?.name ?? 'Sin sucursal';
  }

  protected draftQuantity(product: CatalogProduct): number {
    const variant = this.selectedVariant(product);
    if (!variant) return 1;
    return this.draftByVariant()[variant.id] ?? 1;
  }

  protected setDraftQuantity(product: CatalogProduct, value: string): void {
    const variant = this.selectedVariant(product);
    if (!variant) return;
    const quantity = Number(value);
    this.draftByVariant.update((current) => ({ ...current, [variant.id]: Number.isFinite(quantity) && quantity > 0 ? quantity : 1 }));
  }

  protected addToDraft(product: CatalogProduct): void {
    const variant = this.selectedVariant(product);
    if (!variant) return;
    const quantity = this.draftQuantity(product);
    this.draftByVariant.update((current) => ({ ...current, [variant.id]: (current[variant.id] ?? 0) + quantity }));
    toast.success('Variante agregada a la reserva.');
  }

  protected draftItems(): Array<{ variant_id: string; quantity: number; product_name: string; variant_sku: string; variant_label: string }> {
    const items = new Map<string, { variant_id: string; quantity: number; product_name: string; variant_sku: string; variant_label: string }>();
    for (const product of this.products()) {
      for (const variant of product.variants ?? []) {
        const quantity = this.draftByVariant()[variant.id] ?? 0;
        if (quantity <= 0) continue;
        items.set(variant.id, {
          variant_id: variant.id,
          quantity,
          product_name: product.name,
          variant_sku: variant.sku,
          variant_label: this.variantLabel(variant),
        });
      }
    }
    return [...items.values()];
  }

  protected removeDraftItem(variantId: string): void {
    this.draftByVariant.update((current) => {
      const next = { ...current };
      delete next[variantId];
      return next;
    });
  }

  protected draftCount(): number {
    return this.draftItems().reduce((sum, item) => sum + item.quantity, 0);
  }

  protected draftTotal(): number {
    return this.draftItems().reduce((sum, item) => {
      const variant = this.findVariant(item.variant_id);
      return sum + (variant ? Number(variant.price) * item.quantity : 0);
    }, 0);
  }

  protected canSubmit(): boolean {
    return !!this.form.controls.branch_id.value && !!this.form.controls.visit_date.value && this.draftItems().length > 0;
  }

  protected async submitReservation(): Promise<void> {
    if (!this.canSubmit()) {
      toast.warning('Completa la sucursal, la fecha y agrega al menos una variante.');
      return;
    }

    this.submitting.set(true);
    try {
      const value = this.form.getRawValue();
      const payload: CreateReservationRequest = {
        branch_id: value.branch_id,
        visit_date: value.visit_date,
        items: this.draftItems().map((item) => ({ variant_id: item.variant_id, quantity: item.quantity })),
      };
      const response = await requestWithToast(
        this.reservationApi.createReservation(payload),
        { loading: 'Creando reserva...', success: 'Reserva creada correctamente.', error: 'No se pudo crear la reserva.' },
      );
      this.draftByVariant.set({});
      this.form.patchValue({ visit_date: '' });
    } catch {
      // toast handled by requestWithToast
    } finally {
      this.submitting.set(false);
    }
  }

  private findVariant(variantId: string): CatalogProductVariant | null {
    for (const product of this.products()) {
      const variant = (product.variants ?? []).find((item) => item.id === variantId);
      if (variant) return variant;
    }
    return null;
  }

  private async loadData(): Promise<void> {
    this.loading.set(true);
    try {
      const [branches, categories, sizes, colors, seasons, collections, products] = await Promise.all([
        firstValueFrom(this.catalogApi.listPublicBranches()),
        firstValueFrom(this.catalogApi.listCategories()),
        firstValueFrom(this.catalogApi.listSizes()),
        firstValueFrom(this.catalogApi.listColors()),
        firstValueFrom(this.catalogApi.listSeasons()),
        firstValueFrom(this.catalogApi.listCollections()),
        firstValueFrom(this.catalogApi.listProducts()),
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
      toast.error(getErrorMessage(error, 'No se pudieron cargar las reservas.'));
    } finally {
      this.loading.set(false);
    }
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
