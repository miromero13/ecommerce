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
  original_unit_price: string;
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
  protected readonly products = signal<CatalogProduct[]>([]);
  protected readonly selectedItems = signal<SelectedSaleItem[]>([]);
  protected readonly lastSale = signal<Sale | null>(null);
  protected readonly loadingProducts = signal(false);
  protected readonly submitting = signal(false);
  protected readonly cashReference = signal('');
  protected readonly salesHistory = signal<Sale[]>([]);

  protected readonly branchId = computed(() => this.session.user()?.branch_id ?? null);
  protected readonly branchLabel = computed(() => this.session.user()?.branch_id ?? 'Sin sucursal');

  protected readonly itemCount = computed(() => this.selectedItems().reduce((sum, item) => sum + item.quantity, 0));
  protected readonly subtotal = computed(() => this.selectedItems().reduce((sum, item) => sum + Number(item.original_unit_price) * item.quantity, 0).toFixed(2));
  protected readonly discount = computed(() => this.selectedItems().reduce((sum, item) => sum + (Number(item.original_unit_price) - Number(item.unit_price)) * item.quantity, 0).toFixed(2));
  protected readonly total = computed(() => (Number(this.subtotal()) - Number(this.discount())).toFixed(2));

  constructor() {
    void this.searchProducts();
    void this.loadHistory();
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

  protected addVariant(product: CatalogProduct, variant: CatalogProductVariant): void {
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
      original_unit_price: variant.original_price ?? variant.price,
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
    this.lastSale.set(null);
    this.cashReference.set('');
  }

  protected async submitSale(): Promise<void> {
    const branchId = this.branchId();
    if (!branchId) {
      toast.error('No tienes una sucursal asignada.');
      return;
    }

    if (!this.selectedItems().length) {
      toast.warning('Agrega items a la venta.');
      return;
    }

    this.submitting.set(true);
    try {
      const payload: CreateSaleRequest = {
        branch_id: branchId,
        payment_method: 'cash',
        cash_reference: this.cashReference() || null,
        items: this.selectedItems().map((item) => ({ variant_id: item.variant_id, quantity: item.quantity })),
      };

      const response = await requestWithToast(
        this.salesApi.createSale(payload),
        { loading: 'Registrando venta...', success: 'Venta registrada.', error: 'No se pudo registrar la venta.' },
      );
      this.lastSale.set(response.data ?? null);
      this.selectedItems.set([]);
      this.cashReference.set('');
      await this.searchProducts();
      await this.loadHistory();
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

  protected printReceipt(): void {
    window.print();
  }

  protected lineTotal(item: SelectedSaleItem): string {
    return (Number(item.unit_price) * item.quantity).toFixed(2);
  }

  private async loadHistory(): Promise<void> {
    const branchId = this.branchId();
    if (!branchId) return;
    try {
      const response = await firstValueFrom(this.salesApi.listBranchSales(branchId));
      this.salesHistory.set(response.data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo cargar el historial de ventas.'));
    }
  }

}
