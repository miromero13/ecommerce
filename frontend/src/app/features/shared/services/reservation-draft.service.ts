import { Injectable, computed, signal } from '@angular/core';

import { toast } from '@spartan-ng/brain/sonner';
import { CatalogProduct, CatalogProductVariant } from '../models/catalog.model';

export interface ReservationDraftItem {
  variant_id: string;
  product_id: string;
  product_name: string;
  variant_sku: string;
  variant_label: string;
  unit_price: string;
  quantity: number;
  image_url: string | null;
  tenant_name?: string | null;
  branch_id?: string | null;
  branch_name?: string | null;
}

const STORAGE_KEY = 'fashionstore_reservation_draft';

@Injectable({ providedIn: 'root' })
export class ReservationDraftService {
  readonly items = signal<ReservationDraftItem[]>(this.loadFromStorage());
  readonly selectedBranchId = signal<string>(this.loadMetaFromStorage('branch'));
  readonly selectedBranchName = signal<string>(this.loadMetaFromStorage('branch_name'));
  readonly selectedTenantName = signal<string>(this.loadMetaFromStorage('tenant_name'));

  readonly count = computed(() =>
    this.items().reduce((sum, item) => sum + item.quantity, 0),
  );

  readonly totalEstimated = computed(() =>
    this.items().reduce(
      (sum, item) => sum + Number(item.unit_price || 0) * item.quantity,
      0,
    ),
  );

  hasBranchConflict(branchId?: string): boolean {
    if (!branchId || this.items().length === 0) return false;
    const current = this.selectedBranchId();
    return !!current && current !== branchId;
  }

  addItem(
    product: CatalogProduct,
    variant: CatalogProductVariant,
    branchId?: string,
    branchName?: string,
    tenantName?: string,
  ): void {
    const current = [...this.items()];
    const existingIndex = current.findIndex((i) => i.variant_id === variant.id);

    if (existingIndex >= 0) {
      current[existingIndex] = {
        ...current[existingIndex],
        quantity: current[existingIndex].quantity + 1,
      };
      this.items.set(current);
      this.saveToStorage();
      toast.success(`Se sumó otra unidad de '${product.name}' a tu reserva.`);
      return;
    }

    const tName = tenantName || product.tenant_name || null;
    const bName = branchName || null;

    const newItem: ReservationDraftItem = {
      variant_id: variant.id,
      product_id: product.id,
      product_name: product.name,
      variant_sku: variant.sku,
      variant_label: `${variant.sku}`,
      unit_price: variant.price,
      quantity: 1,
      image_url: variant.image_url ?? product.image_url ?? null,
      tenant_name: tName,
      branch_id: branchId ?? null,
      branch_name: bName,
    };

    if (branchId && (!this.selectedBranchId() || this.items().length === 0)) {
      this.setBranchContext(branchId, bName, tName);
    }

    this.items.set([...current, newItem]);
    this.saveToStorage();
    toast.success(`'${product.name}' agregada para reservar.`);
  }

  resetAndAddItem(
    product: CatalogProduct,
    variant: CatalogProductVariant,
    branchId?: string,
    branchName?: string,
    tenantName?: string,
  ): void {
    this.clearDraft();
    if (branchId) {
      this.setBranchContext(branchId, branchName ?? null, tenantName ?? product.tenant_name ?? null);
    }
    this.addItem(product, variant, branchId, branchName, tenantName);
  }

  increaseItem(variantId: string): void {
    const updated = this.items().map((item) => {
      if (item.variant_id === variantId) {
        return { ...item, quantity: item.quantity + 1 };
      }
      return item;
    });
    this.items.set(updated);
    this.saveToStorage();
  }

  decreaseItem(variantId: string): void {
    const found = this.items().find((i) => i.variant_id === variantId);
    if (!found) return;

    if (found.quantity <= 1) {
      this.removeItem(variantId);
      return;
    }

    const updated = this.items().map((item) => {
      if (item.variant_id === variantId) {
        return { ...item, quantity: item.quantity - 1 };
      }
      return item;
    });
    this.items.set(updated);
    this.saveToStorage();
  }

  removeItem(variantId: string): void {
    const filtered = this.items().filter((item) => item.variant_id !== variantId);
    this.items.set(filtered);
    if (filtered.length === 0) {
      this.clearBranchContext();
    }
    this.saveToStorage();
    toast.info('Prenda removida de la reserva.');
  }

  clearDraft(): void {
    this.items.set([]);
    this.clearBranchContext();
    this.saveToStorage();
  }

  setBranchId(
    branchId: string,
    branchName?: string | null,
    tenantName?: string | null,
  ): void {
    this.setBranchContext(branchId, branchName, tenantName);
  }

  setBranchContext(
    branchId: string,
    branchName?: string | null,
    tenantName?: string | null,
  ): void {
    this.selectedBranchId.set(branchId);
    this.selectedBranchName.set(branchName || '');
    this.selectedTenantName.set(tenantName || '');
    try {
      localStorage.setItem(`${STORAGE_KEY}_branch`, branchId);
      if (branchName) localStorage.setItem(`${STORAGE_KEY}_branch_name`, branchName);
      if (tenantName) localStorage.setItem(`${STORAGE_KEY}_tenant_name`, tenantName);
    } catch {
      // ignore storage errors
    }
  }

  clearBranchContext(): void {
    this.selectedBranchId.set('');
    this.selectedBranchName.set('');
    this.selectedTenantName.set('');
    try {
      localStorage.removeItem(`${STORAGE_KEY}_branch`);
      localStorage.removeItem(`${STORAGE_KEY}_branch_name`);
      localStorage.removeItem(`${STORAGE_KEY}_tenant_name`);
    } catch {
      // ignore storage errors
    }
  }

  getQuantityForVariant(variantId: string): number {
    const item = this.items().find((i) => i.variant_id === variantId);
    return item ? item.quantity : 0;
  }

  getQuantityForProduct(product: CatalogProduct): number {
    const variantIds = (product.variants ?? []).map((v) => v.id);
    return this.items()
      .filter((i) => variantIds.includes(i.variant_id))
      .reduce((sum, i) => sum + i.quantity, 0);
  }

  private loadFromStorage(): ReservationDraftItem[] {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  }

  private loadMetaFromStorage(key: string): string {
    try {
      return localStorage.getItem(`${STORAGE_KEY}_${key}`) || '';
    } catch {
      return '';
    }
  }

  private saveToStorage(): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.items()));
    } catch {
      // ignore storage errors
    }
  }
}
