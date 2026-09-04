import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormArray, FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

import { HlmBadge } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInput } from '../../../components/input/src';
import { HlmTable } from '../../../components/table/src';
import { HlmTabsImports } from '../../../components/tabs/src';
import { AdminActionMenuComponent } from '../components/admin-action-menu.component';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import {
  CatalogCollectionItem,
  CatalogColorItem,
  CatalogNameItem,
  CatalogProduct,
  CatalogProductVariant,
} from '../../shared/models/catalog.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';

type CatalogTab = 'categories' | 'sizes' | 'colors' | 'seasons' | 'collections' | 'products';

const CATALOG_TAB_LABELS: Record<CatalogTab, string> = {
  categories: 'Categorías',
  sizes: 'Tallas',
  colors: 'Colores',
  seasons: 'Temporadas',
  collections: 'Colecciones',
  products: 'Productos',
};

const CATALOG_CREATE_LABELS: Record<CatalogTab, string> = {
  categories: 'Crear categoría',
  sizes: 'Crear talla',
  colors: 'Crear color',
  seasons: 'Crear temporada',
  collections: 'Crear colección',
  products: 'Crear producto',
};

@Component({
  selector: 'app-admin-catalog-page',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    HlmBadge,
    HlmButton,
    HlmInput,
    HlmTable,
    AdminActionMenuComponent,
    ...HlmCardImports,
    ...HlmFieldImports,
    ...HlmTabsImports,
  ],
  templateUrl: './admin-catalog-page.component.html',
})
export class AdminCatalogPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(CatalogApiService);

  protected readonly categories = signal<CatalogNameItem[]>([]);
  protected readonly sizes = signal<CatalogNameItem[]>([]);
  protected readonly colors = signal<CatalogColorItem[]>([]);
  protected readonly seasons = signal<CatalogNameItem[]>([]);
  protected readonly collections = signal<CatalogCollectionItem[]>([]);
  protected readonly products = signal<CatalogProduct[]>([]);
  protected readonly errorMessage = signal('');
  protected readonly successMessage = signal('');
  protected readonly loading = signal(false);
  protected readonly activeTab = signal<CatalogTab>('products');
  protected readonly modalOpen = signal(false);
  protected readonly modalMode = signal<'create' | 'edit'>('create');
  protected readonly editingItemId = signal<string | null>(null);
  protected readonly editingProductId = signal<string | null>(null);
  protected readonly openMenuId = signal<string | null>(null);
  protected readonly deleteConfirmOpen = signal(false);
  protected readonly deletingItem = signal<{ tab: CatalogTab; id: string; label: string } | null>(null);

  protected readonly categoryForm = this.fb.nonNullable.group({ name: ['', [Validators.required]] });
  protected readonly sizeForm = this.fb.nonNullable.group({ name: ['', [Validators.required]] });
  protected readonly colorForm = this.fb.nonNullable.group({ name: ['', [Validators.required]], hex_code: [''] });
  protected readonly seasonForm = this.fb.nonNullable.group({ name: ['', [Validators.required]] });
  protected readonly collectionForm = this.fb.nonNullable.group({ name: ['', [Validators.required]], season_id: [''] });
  protected readonly productForm = this.fb.nonNullable.group({
    name: ['', [Validators.required]],
    description: [''],
    category_id: ['', [Validators.required]],
    season_id: [''],
    collection_id: [''],
    variants: this.fb.array([this.createVariantGroup()]),
  });

  constructor() {
    void this.loadData();
  }

  protected readonly tabs: CatalogTab[] = ['products', 'categories', 'sizes', 'colors', 'seasons', 'collections'];

  protected selectTab(tab: string): void {
    this.activeTab.set(tab as CatalogTab);
  }

  protected openModal(tab: CatalogTab): void {
    this.activeTab.set(tab);
    this.modalMode.set('create');
    this.editingItemId.set(null);
    this.editingProductId.set(null);
    this.errorMessage.set('');
    this.successMessage.set('');
    if (tab === 'products') {
      this.productForm.reset({ name: '', description: '', category_id: '', season_id: '', collection_id: '' });
      this.variantsArray().clear();
      this.variantsArray().push(this.createVariantGroup());
    } else {
      this.resetSimpleForm(tab);
    }
    this.modalOpen.set(true);
  }

  protected openEditModal(tab: CatalogTab, item: CatalogNameItem | CatalogColorItem | CatalogCollectionItem): void {
    this.activeTab.set(tab);
    this.modalMode.set('edit');
    this.editingItemId.set(item.id);
    this.editingProductId.set(null);
    this.errorMessage.set('');
    this.successMessage.set('');
    if (tab === 'categories') {
      this.categoryForm.reset({ name: item.name });
    } else if (tab === 'sizes') {
      this.sizeForm.reset({ name: item.name });
    } else if (tab === 'colors') {
      const color = item as CatalogColorItem;
      this.colorForm.reset({ name: color.name, hex_code: color.hex_code ?? '' });
    } else if (tab === 'seasons') {
      this.seasonForm.reset({ name: item.name });
    } else if (tab === 'collections') {
      const collection = item as CatalogCollectionItem;
      this.collectionForm.reset({ name: collection.name, season_id: collection.season_id ?? '' });
    }
    this.modalOpen.set(true);
  }

  protected openEditProduct(product: CatalogProduct): void {
    this.activeTab.set('products');
    this.modalMode.set('edit');
    this.editingProductId.set(product.id);
    this.editingItemId.set(null);
    this.errorMessage.set('');
    this.successMessage.set('');

    this.productForm.reset({
      name: product.name,
      description: product.description ?? '',
      category_id: product.category_id,
      season_id: product.season_id ?? '',
      collection_id: product.collection_id ?? '',
    });
    this.variantsArray().clear();

    const variants = product.variants?.length ? product.variants : [{ sku: product.sku ?? '', price: product.price, size_id: product.size_id ?? '', color_id: product.color_id ?? '', status: product.status ?? 'active' }];
    variants.forEach((variant) => {
      this.variantsArray().push(this.fb.nonNullable.group({
        sku: [variant.sku, [Validators.required]],
        price: [variant.price, [Validators.required]],
        size_id: [variant.size_id ?? ''],
        color_id: [variant.color_id ?? ''],
        status: [variant.status, [Validators.required]],
      }));
    });

    this.modalOpen.set(true);
  }

  protected closeModal(): void {
    this.modalOpen.set(false);
  }

  protected closeMenu(): void {
    this.openMenuId.set(null);
  }

  protected toggleMenu(id: string): void {
    this.openMenuId.set(this.openMenuId() === id ? null : id);
  }

  protected askDelete(tab: CatalogTab, id: string, label: string): void {
    this.closeMenu();
    this.deletingItem.set({ tab, id, label });
    this.deleteConfirmOpen.set(true);
  }

  protected cancelDelete(): void {
    this.deleteConfirmOpen.set(false);
    this.deletingItem.set(null);
  }

  protected async confirmDelete(): Promise<void> {
    const target = this.deletingItem();
    if (!target) return;

    this.loading.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');

    try {
      if (target.tab === 'categories') await firstValueFrom(this.api.deleteCategory(target.id));
      else if (target.tab === 'sizes') await firstValueFrom(this.api.deleteSize(target.id));
      else if (target.tab === 'colors') await firstValueFrom(this.api.deleteColor(target.id));
      else if (target.tab === 'seasons') await firstValueFrom(this.api.deleteSeason(target.id));
      else if (target.tab === 'collections') await firstValueFrom(this.api.deleteCollection(target.id));
      else await firstValueFrom(this.api.deleteProduct(target.id));

      await this.loadData();
      this.successMessage.set(`${target.label} eliminado correctamente.`);
      this.cancelDelete();
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, `No se pudo eliminar ${target.label.toLowerCase()}.`));
    } finally {
      this.loading.set(false);
    }
  }

  protected tabLabel(tab: CatalogTab): string {
    return CATALOG_TAB_LABELS[tab];
  }

  protected createLabel(tab: CatalogTab): string {
    return CATALOG_CREATE_LABELS[tab];
  }

  protected async submitCategory(): Promise<void> {
    await this.submitNameItem('categories', this.categoryForm, () => this.api.createCategory(this.categoryForm.getRawValue()), (id, payload) => this.api.updateCategory(id, payload), 'Categoría creada correctamente.', 'Categoría actualizada correctamente.');
  }

  protected async submitSize(): Promise<void> {
    await this.submitNameItem('sizes', this.sizeForm, () => this.api.createSize(this.sizeForm.getRawValue()), (id, payload) => this.api.updateSize(id, payload), 'Talla creada correctamente.', 'Talla actualizada correctamente.');
  }

  protected async submitColor(): Promise<void> {
    await this.submitColorItem();
  }

  protected async submitSeason(): Promise<void> {
    await this.submitNameItem('seasons', this.seasonForm, () => this.api.createSeason(this.seasonForm.getRawValue()), (id, payload) => this.api.updateSeason(id, payload), 'Temporada creada correctamente.', 'Temporada actualizada correctamente.');
  }

  protected async submitCollection(): Promise<void> {
    await this.submitCollectionItem();
  }

  protected async submitProduct(): Promise<void> {
    if (this.productForm.invalid) {
      this.productForm.markAllAsTouched();
      return;
    }

    if (this.hasDuplicateVariants()) {
      this.errorMessage.set('No puedes repetir la misma combinacion de talla y color dentro del producto.');
      return;
    }

    const variants = this.variantForms().getRawValue();
    const firstVariant = variants[0];
    if (!firstVariant?.price) {
      this.errorMessage.set('Debes definir al menos una variante con precio.');
      return;
    }

    this.loading.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');
    try {
      const payload = this.productForm.getRawValue();
      const request = {
        name: payload.name,
        description: payload.description || null,
        price: firstVariant.price,
        category_id: payload.category_id,
        season_id: payload.season_id || null,
        collection_id: payload.collection_id || null,
        variants: variants.map((variant) => ({
          sku: variant.sku,
          price: variant.price,
          size_id: variant.size_id || null,
          color_id: variant.color_id || null,
          status: variant.status || 'active',
        })),
      };

      if (this.modalMode() === 'edit' && this.editingProductId()) {
        await firstValueFrom(this.api.updateProduct(this.editingProductId()!, request));
        this.successMessage.set('Producto actualizado correctamente.');
      } else {
        await firstValueFrom(this.api.createProduct(request));
        this.successMessage.set('Producto creado correctamente.');
      }
      this.productForm.reset({ name: '', description: '', category_id: '', season_id: '', collection_id: '' });
      this.variantsArray().clear();
      this.variantsArray().push(this.createVariantGroup());
      await this.loadData();
      this.closeModal();
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo guardar el producto.'));
    } finally {
      this.loading.set(false);
    }
  }

  protected async toggleVariantStatus(variant: CatalogProductVariant): Promise<void> {
    const nextStatus = variant.status === 'active' ? 'inactive' : 'active';
    try {
      await firstValueFrom(this.api.updateVariantStatus(variant.id, nextStatus));
      await this.loadData();
      this.successMessage.set('Estado de la variante actualizado.');
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo actualizar la variante.'));
    }
  }

  protected variantsArray(): FormArray {
    return this.productForm.controls.variants as FormArray;
  }

  protected variantForms() {
    return this.variantsArray();
  }

  protected addVariant(): void {
    this.variantsArray().push(this.createVariantGroup());
  }

  protected removeVariant(index: number): void {
    if (this.variantsArray().length === 1) {
      return;
    }
    this.variantsArray().removeAt(index);
  }

  protected variantControls(): Array<any> {
    return this.variantsArray().controls;
  }

  protected productVariants(product: CatalogProduct): CatalogProductVariant[] {
    return product.variants ?? [];
  }

  protected primaryVariant(product: CatalogProduct): CatalogProductVariant | null {
    return this.productVariants(product)[0] ?? null;
  }

  protected variantLabel(variant: CatalogProductVariant): string {
    const size = this.sizeName(variant.size_id);
    const color = this.colorName(variant.color_id);
    return `${size} / ${color}`;
  }

  protected variantStatusBadge(variant: CatalogProductVariant): string {
    return variant.status;
  }

  protected seasonName(seasonId: string | null): string {
    if (!seasonId) return 'Sin temporada';
    return this.seasons().find((season) => season.id === seasonId)?.name ?? seasonId;
  }

  protected modalTitle(): string {
    const tab = this.activeTab();
    if (this.modalMode() === 'edit') {
      return tab === 'products' ? 'Editar producto' : `Editar ${this.tabLabel(tab).slice(0, -1).toLowerCase()}`;
    }
    return this.createLabel(tab);
  }

  private async submitNameItem(
    tab: Extract<CatalogTab, 'categories' | 'sizes' | 'seasons'>,
    form: any,
    createAction: () => any,
    updateAction: (id: string, payload: { name: string }) => any,
    createMessage: string,
    updateMessage: string,
  ): Promise<void> {
    if (form.invalid) {
      form.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');
    try {
      const payload = { name: form.controls.name.value };
      if (this.modalMode() === 'edit' && this.editingItemId()) {
        await firstValueFrom(updateAction(this.editingItemId()!, payload));
        this.successMessage.set(updateMessage);
      } else {
        await firstValueFrom(createAction());
        this.successMessage.set(createMessage);
      }
      form.reset();
      await this.loadData();
      this.closeModal();
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo guardar el registro.'));
    } finally {
      this.loading.set(false);
    }
  }

  protected categoryName(categoryId: string | null): string {
    return this.lookupName(this.categories(), categoryId, 'Sin categoría');
  }

  protected openCategoryEdit(category: CatalogNameItem): void {
    this.openEditModal('categories', category);
  }

  protected openSizeEdit(size: CatalogNameItem): void {
    this.openEditModal('sizes', size);
  }

  protected openSeasonEdit(season: CatalogNameItem): void {
    this.openEditModal('seasons', season);
  }

  protected openColorEdit(color: CatalogColorItem): void {
    this.openEditModal('colors', color);
  }

  protected openCollectionEdit(collection: CatalogCollectionItem): void {
    this.openEditModal('collections', collection);
  }

  private async submitColorItem(): Promise<void> {
    if (this.colorForm.invalid) {
      this.colorForm.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');
    try {
      const payload = this.colorForm.getRawValue();
      if (this.modalMode() === 'edit' && this.editingItemId()) {
        await firstValueFrom(this.api.updateColor(this.editingItemId()!, { name: payload.name, hex_code: payload.hex_code || null }));
        this.successMessage.set('Color actualizado correctamente.');
      } else {
        await firstValueFrom(this.api.createColor({ name: payload.name, hex_code: payload.hex_code || null }));
        this.successMessage.set('Color creado correctamente.');
      }
      this.colorForm.reset({ name: '', hex_code: '' });
      await this.loadData();
      this.closeModal();
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo guardar el color.'));
    } finally {
      this.loading.set(false);
    }
  }

  private async submitCollectionItem(): Promise<void> {
    if (this.collectionForm.invalid) {
      this.collectionForm.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');
    try {
      const payload = {
        name: this.collectionForm.controls.name.value,
        season_id: this.collectionForm.controls.season_id.value || null,
      };
      if (this.modalMode() === 'edit' && this.editingItemId()) {
        await firstValueFrom(this.api.updateCollection(this.editingItemId()!, payload));
        this.successMessage.set('Colección actualizada correctamente.');
      } else {
        await firstValueFrom(this.api.createCollection(payload));
        this.successMessage.set('Colección creada correctamente.');
      }
      this.collectionForm.reset({ name: '', season_id: '' });
      await this.loadData();
      this.closeModal();
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo guardar la colección.'));
    } finally {
      this.loading.set(false);
    }
  }

  private resetSimpleForm(tab: Exclude<CatalogTab, 'products'>): void {
    if (tab === 'categories') {
      this.categoryForm.reset({ name: '' });
    } else if (tab === 'sizes') {
      this.sizeForm.reset({ name: '' });
    } else if (tab === 'colors') {
      this.colorForm.reset({ name: '', hex_code: '' });
    } else if (tab === 'seasons') {
      this.seasonForm.reset({ name: '' });
    } else if (tab === 'collections') {
      this.collectionForm.reset({ name: '', season_id: '' });
    }
  }

  protected sizeName(sizeId: string | null | undefined): string {
    return this.lookupName(this.sizes(), sizeId, 'Sin talla');
  }

  protected colorName(colorId: string | null | undefined): string {
    return this.lookupName(this.colors(), colorId, 'Sin color');
  }

  protected collectionName(collectionId: string | null | undefined): string {
    return this.lookupName(this.collections(), collectionId, 'Sin colección');
  }

  private createVariantGroup() {
    return this.fb.nonNullable.group({
      sku: ['', [Validators.required]],
      price: ['', [Validators.required]],
      size_id: [''],
      color_id: [''],
      status: ['active', [Validators.required]],
    });
  }

  private hasDuplicateVariants(): boolean {
    const seen = new Set<string>();
    for (const group of this.variantForms().controls) {
      const value = group.getRawValue();
      const key = `${value.size_id || 'none'}::${value.color_id || 'none'}`;
      if (seen.has(key)) {
        return true;
      }
      seen.add(key);
    }
    return false;
  }

  private lookupName(items: Array<{ id: string; name: string }>, id: string | null | undefined, fallback: string): string {
    if (!id) {
      return fallback;
    }

    return items.find((item) => item.id === id)?.name ?? fallback;
  }

  private async loadData(): Promise<void> {
    try {
      const [categories, sizes, colors, seasons, collections, products] = await Promise.all([
        firstValueFrom(this.api.listCategories()),
        firstValueFrom(this.api.listSizes()),
        firstValueFrom(this.api.listColors()),
        firstValueFrom(this.api.listSeasons()),
        firstValueFrom(this.api.listCollections()),
        firstValueFrom(this.api.listProducts()),
      ]);

      this.categories.set(categories.data ?? []);
      this.sizes.set(sizes.data ?? []);
      this.colors.set(colors.data ?? []);
      this.seasons.set(seasons.data ?? []);
      this.collections.set(collections.data ?? []);
      this.products.set(products.data ?? []);
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo cargar el catálogo.'));
    }
  }
}
