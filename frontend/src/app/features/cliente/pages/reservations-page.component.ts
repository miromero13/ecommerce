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
import { CreateReservationRequest, Reservation } from '../../shared/models/reservation.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { ReservationApiService } from '../../shared/services/reservation-api.service';

@Component({
  selector: 'app-reservations-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HlmButton, HlmInput, ...HlmBadgeImports, ...HlmCardImports, ...HlmFieldImports, ...HlmSelectImports],
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
  protected readonly reservations = signal<Reservation[]>([]);
  protected readonly selectedVariantByProduct = signal<Record<string, string>>({});
  protected readonly draftByVariant = signal<Record<string, number>>({});
  protected readonly loading = signal(false);
  protected readonly submitting = signal(false);

  protected readonly form = this.fb.nonNullable.group({
    branch_id: [''],
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

  protected variantLabel(variant: CatalogProductVariant): string {
    return `${this.sizeName(variant.size_id)} / ${this.colorName(variant.color_id)}`;
  }

  protected sizeName(sizeId: string | null | undefined): string {
    return this.sizes().find((size) => size.id === sizeId)?.name ?? 'Sin talla';
  }

  protected colorName(colorId: string | null | undefined): string {
    return this.colors().find((color) => color.id === colorId)?.name ?? 'Sin color';
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
      this.reservations.set([response.data!, ...this.reservations()]);
      this.draftByVariant.set({});
      this.form.patchValue({ visit_date: '' });
    } catch {
      // toast handled by requestWithToast
    } finally {
      this.submitting.set(false);
    }
  }

  protected reservationStatusLabel(status: Reservation['status']): string {
    switch (status) {
      case 'pending': return 'Pendiente';
      case 'confirmed': return 'Confirmada';
      case 'attended': return 'Atendida';
      case 'cancelled': return 'Cancelada';
      case 'expired': return 'Vencida';
      default: return status;
    }
  }

  protected reservationStatusClass(status: Reservation['status']): string {
    switch (status) {
      case 'pending': return 'bg-amber-100 text-amber-700';
      case 'confirmed': return 'bg-sky-100 text-sky-700';
      case 'attended': return 'bg-emerald-100 text-emerald-700';
      case 'cancelled': return 'bg-rose-100 text-rose-700';
      case 'expired': return 'bg-slate-100 text-slate-700';
      default: return 'bg-slate-100 text-slate-700';
    }
  }

  protected async cancelReservation(reservationId: string): Promise<void> {
    try {
      const response = await requestWithToast(
        this.reservationApi.cancelReservation(reservationId),
        { loading: 'Cancelando reserva...', success: 'Reserva cancelada.', error: 'No se pudo cancelar la reserva.' },
      );
      const updated = response.data;
      if (updated) {
        this.reservations.update((current) => current.map((item) => item.id === updated.id ? updated : item));
      }
    } catch {
      // toast handled by requestWithToast
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
      const [branches, categories, sizes, colors, seasons, collections, products, reservations] = await Promise.all([
        firstValueFrom(this.catalogApi.listPublicBranches()),
        firstValueFrom(this.catalogApi.listCategories()),
        firstValueFrom(this.catalogApi.listSizes()),
        firstValueFrom(this.catalogApi.listColors()),
        firstValueFrom(this.catalogApi.listSeasons()),
        firstValueFrom(this.catalogApi.listCollections()),
        firstValueFrom(this.catalogApi.listProducts()),
        firstValueFrom(this.reservationApi.listMyReservations()),
      ]);
      this.branches.set(branches.data ?? []);
      this.categories.set(categories.data ?? []);
      this.sizes.set(sizes.data ?? []);
      this.colors.set(colors.data ?? []);
      this.seasons.set(seasons.data ?? []);
      this.collections.set(collections.data ?? []);
      this.products.set(products.data ?? []);
      this.reservations.set(reservations.data ?? []);
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
