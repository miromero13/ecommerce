import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmInputImports } from '../../../components/input/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { requestWithToast } from '../../../core/utils/request-toast.util';
import { CatalogProduct, CatalogProductVariant } from '../../shared/models/catalog.model';
import { Reservation } from '../../shared/models/reservation.model';
import { CreateSaleRequest, Sale } from '../../shared/models/sale.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { SalesApiService } from '../../shared/services/sales-api.service';
import { SessionService } from '../../shared/services/session.service';

type SelectedSaleItem = {
  variant_id: string;
  product_name: string;
  variant_sku: string;
  size_name: string | null;
  color_name: string | null;
  unit_price: string;
  quantity: number;
  image_url: string | null;
};

@Component({
  selector: 'app-cajero-sales-page',
  standalone: true,
  imports: [CommonModule, RouterLink, HlmButton, ...HlmBadgeImports, ...HlmCardImports, ...HlmInputImports],
  templateUrl: './sales-page.component.html',
})
export class SalesPageComponent {
  private readonly catalogApi = inject(CatalogApiService);
  private readonly salesApi = inject(SalesApiService);
  private readonly session = inject(SessionService);

  protected readonly searchTerm = signal('');
  protected readonly reservationQuery = signal('');
  protected readonly products = signal<CatalogProduct[]>([]);
  protected readonly selectedReservation = signal<Reservation | null>(null);
  protected readonly selectedItems = signal<SelectedSaleItem[]>([]);
  protected readonly lastSale = signal<Sale | null>(null);
  protected readonly loadingProducts = signal(false);
  protected readonly loadingReservation = signal(false);
  protected readonly submitting = signal(false);
  protected readonly paymentMethod = signal<'cash' | 'stripe'>('cash');
  protected readonly cashReference = signal('');

  protected readonly branchId = computed(() => this.session.user()?.branch_id ?? null);
  protected readonly branchLabel = computed(() => this.session.user()?.branch_id ?? 'Sin sucursal');

  protected readonly itemCount = computed(() => this.selectedItems().reduce((sum, item) => sum + item.quantity, 0));
  protected readonly subtotal = computed(() => this.selectedItems().reduce((sum, item) => sum + Number(item.unit_price) * item.quantity, 0).toFixed(2));

  constructor() {
    void this.searchProducts();
  }

  protected async searchProducts(): Promise<void> {
    const branchId = this.branchId();
    this.loadingProducts.set(true);
    try {
      const response = await firstValueFrom(this.catalogApi.listProducts({ q: this.searchTerm() || undefined, branch_id: branchId ?? undefined }));
      this.products.set((response.data ?? []) as CatalogProduct[]);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar los productos.'));
      this.products.set([]);
    } finally {
      this.loadingProducts.set(false);
    }
  }

  protected async loadReservation(): Promise<void> {
    const reservationId = this.reservationQuery().trim();
    if (!reservationId) {
      toast.warning('Ingresa un id de reserva.');
      return;
    }

    const branchId = this.branchId();
    if (!branchId) {
      toast.error('No tienes una sucursal asignada.');
      return;
    }

    this.loadingReservation.set(true);
    try {
      const response = await firstValueFrom(this.salesApi.searchReservation(reservationId, branchId));
      const reservation = response.data ?? null;
      if (!reservation) {
        toast.warning('Reserva no encontrada.');
        this.selectedReservation.set(null);
        return;
      }

      this.selectedReservation.set(reservation);
      this.selectedItems.set(
        reservation.items.map((item) => ({
          variant_id: item.variant_id,
          product_name: item.product_name,
          variant_sku: item.variant_sku,
          size_name: item.size_name,
          color_name: item.color_name,
          unit_price: item.unit_price,
          quantity: item.quantity,
          image_url: item.image_url,
        })),
      );
      toast.success('Reserva cargada para la venta.');
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo cargar la reserva.'));
      this.selectedReservation.set(null);
    } finally {
      this.loadingReservation.set(false);
    }
  }

  protected addVariant(product: CatalogProduct, variant: CatalogProductVariant): void {
    if (this.selectedReservation()) {
      toast.warning('La venta ya está asociada a una reserva.');
      return;
    }

    const items = [...this.selectedItems()];
    const existing = items.find((item) => item.variant_id === variant.id);
    if (existing) {
      existing.quantity += 1;
      this.selectedItems.set(items);
      return;
    }

    items.push({
      variant_id: variant.id,
      product_name: product.name,
      variant_sku: variant.sku,
      size_name: null,
      color_name: null,
      unit_price: variant.price,
      quantity: 1,
      image_url: variant.image_url ?? product.image_url ?? null,
    });
    this.selectedItems.set(items);
  }

  protected increaseItem(variantId: string): void {
    const items = this.selectedItems().map((item) => item.variant_id === variantId ? { ...item, quantity: item.quantity + 1 } : item);
    this.selectedItems.set(items);
  }

  protected decreaseItem(variantId: string): void {
    const items = this.selectedItems()
      .map((item) => item.variant_id === variantId ? { ...item, quantity: item.quantity - 1 } : item)
      .filter((item) => item.quantity > 0);
    this.selectedItems.set(items);
  }

  protected removeItem(variantId: string): void {
    this.selectedItems.set(this.selectedItems().filter((item) => item.variant_id !== variantId));
  }

  protected clearSale(): void {
    this.selectedItems.set([]);
    this.selectedReservation.set(null);
    this.lastSale.set(null);
    this.cashReference.set('');
  }

  protected async submitSale(): Promise<void> {
    const branchId = this.branchId();
    if (!branchId) {
      toast.error('No tienes una sucursal asignada.');
      return;
    }

    if (!this.selectedReservation() && !this.selectedItems().length) {
      toast.warning('Agrega items o carga una reserva.');
      return;
    }

    this.submitting.set(true);
    try {
      const payload: CreateSaleRequest = {
        branch_id: branchId,
        reservation_id: this.selectedReservation()?.id ?? null,
        payment_method: this.paymentMethod(),
        cash_reference: this.cashReference() || null,
        items: this.selectedReservation()
          ? []
          : this.selectedItems().map((item) => ({ variant_id: item.variant_id, quantity: item.quantity })),
      };

      const response = await requestWithToast(
        this.salesApi.createSale(payload),
        { loading: 'Registrando venta...', success: 'Venta registrada.', error: 'No se pudo registrar la venta.' },
      );
      this.lastSale.set(response.data ?? null);
      this.selectedItems.set([]);
      this.selectedReservation.set(null);
      this.cashReference.set('');
      await this.searchProducts();
    } catch {
      // toast handled by requestWithToast
    } finally {
      this.submitting.set(false);
    }
  }

  protected saleLabel(): string {
    return this.lastSale() ? `Comprobante #${this.lastSale()!.id}` : 'Sin comprobante';
  }

  protected saleStatusClass(): string {
    return this.lastSale()?.payment_status === 'paid' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-700';
  }

  protected saleTotal(): string {
    return this.selectedItems().reduce((sum, item) => sum + Number(item.unit_price) * item.quantity, 0).toFixed(2);
  }

  protected lineTotal(item: SelectedSaleItem): string {
    return (Number(item.unit_price) * item.quantity).toFixed(2);
  }

}
