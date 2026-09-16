import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { HlmTable } from '../../../components/table/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInput } from '../../../components/input/src';
import { AdminActionMenuComponent } from '../../admin/components/admin-action-menu.component';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { requestWithToast } from '../../../core/utils/request-toast.util';
import { toast } from '@spartan-ng/brain/sonner';
import { CatalogBranch, CatalogNameItem, CatalogProduct } from '../../shared/models/catalog.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { ReplenishmentApiService } from '../../shared/services/replenishment-api.service';

@Component({
  selector: 'app-provider-products-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HlmTable, HlmButton, HlmInput, AdminActionMenuComponent, ...HlmCardImports, ...HlmFieldImports],
  templateUrl: './provider-products-page.component.html',
})
export class ProviderProductsPageComponent {
  private readonly api = inject(CatalogApiService);
  private readonly replenishmentApi = inject(ReplenishmentApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);
  protected readonly products = signal<CatalogProduct[]>([]);
  protected readonly categories = signal<CatalogNameItem[]>([]);
  protected readonly sizes = signal<CatalogNameItem[]>([]);
  protected readonly colors = signal<CatalogNameItem[]>([]);
  protected readonly modalOpen = signal(false);
  protected readonly openMenuId = signal<string | null>(null);
  protected readonly availabilityForm = this.fb.group({ updates: this.fb.array<FormGroup>([]) });
  protected readonly requestForm = this.fb.group({ branch_id: ['', Validators.required], items: this.fb.array<FormGroup>([]) });
  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly requestModalOpen = signal(false);
  protected editingProduct: CatalogProduct | null = null;
  protected readonly isAdminInspection = !!this.route.snapshot.paramMap.get('providerId');

  constructor() {
    void this.loadProducts();
  }

  private async loadProducts(): Promise<void> {
    try {
      const providerId = this.route.snapshot.paramMap.get('providerId');
      const [response, categories, sizes, colors, branches] = await Promise.all([
        providerId ? firstValueFrom(this.api.listProviderProducts(providerId)) : firstValueFrom(this.api.listMyProviderProducts()),
        firstValueFrom(this.api.listCategories()),
        firstValueFrom(this.api.listSizes()),
        firstValueFrom(this.api.listColors()),
        firstValueFrom(this.api.listPublicBranches()),
      ]);
      this.products.set(response.data ?? []);
      this.categories.set(categories.data ?? []);
      this.sizes.set(sizes.data ?? []);
      this.colors.set(colors.data ?? []);
      this.branches.set(branches.data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar los productos.'));
    }
  }

  protected categoryName(id: string): string { return this.categories().find((category) => category.id === id)?.name ?? '-'; }
  protected sizeName(id: string | null): string { return id ? this.sizes().find((size) => size.id === id)?.name ?? '-' : '-'; }
  protected colorName(id: string | null): string { return id ? this.colors().find((color) => color.id === id)?.name ?? '-' : '-'; }
  protected statusLabel(status: string | null | undefined): string { return status === 'active' ? 'Activo' : status === 'inactive' ? 'Inactivo' : 'Pendiente'; }
  protected toggleMenu(id: string): void { this.openMenuId.set(this.openMenuId() === id ? null : id); }
  protected closeMenu(): void { this.openMenuId.set(null); }
  protected openEdit(product: CatalogProduct): void {
    if (this.isAdminInspection) return;
    this.closeMenu();
    this.editingProduct = product;
    this.availabilityForm.controls.updates.clear();
    for (const variant of product.variants ?? []) {
      this.availabilityForm.controls.updates.push(this.fb.group({
        variant_id: [variant.id],
        quantity: [variant.provider_quantity ?? 0, [Validators.required, Validators.min(0), Validators.pattern(/^\d+$/)]],
      }));
    }
    this.modalOpen.set(true);
  }
  protected openView(product: CatalogProduct): void {
    this.closeMenu();
    this.editingProduct = product;
    this.modalOpen.set(true);
  }
  protected openRequest(product: CatalogProduct): void {
    if (!this.isAdminInspection) return;
    this.closeMenu();
    this.editingProduct = product;
    this.requestForm.reset({ branch_id: '' });
    this.requestForm.controls.items.clear();
    for (const variant of product.variants ?? []) {
      this.requestForm.controls.items.push(this.fb.group({ variant_id: [variant.id], requested_quantity: [0, [Validators.required, Validators.min(1), Validators.pattern(/^\d+$/)]] }));
    }
    this.requestModalOpen.set(true);
  }
  protected closeRequest(): void { this.requestModalOpen.set(false); this.editingProduct = null; this.closeMenu(); }
  protected async submitRequest(): Promise<void> {
    if (this.requestForm.invalid || !this.editingProduct) { this.requestForm.markAllAsTouched(); return; }
    const value = this.requestForm.getRawValue();
    const items = value.items.filter((item) => Number(item['requested_quantity']) > 0).map((item) => ({ variant_id: item['variant_id']!, requested_quantity: Number(item['requested_quantity']) }));
    if (!items.length) { toast.error('Ingresa al menos una cantidad solicitada.'); return; }
    try {
      await requestWithToast(this.replenishmentApi.create({ provider_id: this.editingProduct.provider_id!, branch_id: value.branch_id!, items }), { loading: 'Creando solicitud...', success: 'Solicitud creada.', error: 'No se pudo crear la solicitud.' });
      this.closeRequest();
    } catch { /* toast already shown */ }
  }
  protected closeModal(): void { this.modalOpen.set(false); this.editingProduct = null; this.closeMenu(); }
  protected async saveAvailability(): Promise<void> {
    if (this.availabilityForm.invalid || !this.editingProduct) { this.availabilityForm.markAllAsTouched(); return; }
    try {
      await requestWithToast(this.api.updateMyProviderAvailability(this.availabilityForm.controls.updates.getRawValue() as Array<{ variant_id: string; quantity: number }>), { loading: 'Guardando disponibilidad...', success: 'Disponibilidad actualizada.', error: 'No se pudo guardar la disponibilidad.' });
      this.closeModal();
      await this.loadProducts();
    } catch { this.closeModal(); }
  }
}
