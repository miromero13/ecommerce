import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

import { getErrorMessage } from '../../../core/utils/http-error.util';
import {
  CatalogCollectionItem,
  CatalogColorItem,
  CatalogNameItem,
  CatalogProduct,
} from '../../shared/models/catalog.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';

@Component({
  selector: 'app-admin-catalog-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
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

  protected readonly categoryForm = this.fb.nonNullable.group({ name: ['', [Validators.required]] });
  protected readonly sizeForm = this.fb.nonNullable.group({ name: ['', [Validators.required]] });
  protected readonly colorForm = this.fb.nonNullable.group({ name: ['', [Validators.required]], hex_code: [''] });
  protected readonly seasonForm = this.fb.nonNullable.group({ name: ['', [Validators.required]] });
  protected readonly collectionForm = this.fb.nonNullable.group({ name: ['', [Validators.required]], season_id: [''] });
  protected readonly productForm = this.fb.nonNullable.group({
    sku: ['', [Validators.required]],
    name: ['', [Validators.required]],
    description: [''],
    price: ['', [Validators.required]],
    category_id: ['', [Validators.required]],
    size_id: [''],
    color_id: [''],
    season_id: [''],
    collection_id: [''],
  });

  constructor() {
    void this.loadData();
  }

  protected async submitCategory(): Promise<void> {
    await this.submitSimple(this.categoryForm, () => this.api.createCategory(this.categoryForm.getRawValue()), 'Categoría creada correctamente.');
  }

  protected async submitSize(): Promise<void> {
    await this.submitSimple(this.sizeForm, () => this.api.createSize(this.sizeForm.getRawValue()), 'Talla creada correctamente.');
  }

  protected async submitColor(): Promise<void> {
    await this.submitSimple(this.colorForm, () => this.api.createColor(this.colorForm.getRawValue()), 'Color creado correctamente.');
  }

  protected async submitSeason(): Promise<void> {
    await this.submitSimple(this.seasonForm, () => this.api.createSeason(this.seasonForm.getRawValue()), 'Temporada creada correctamente.');
  }

  protected async submitCollection(): Promise<void> {
    await this.submitSimple(this.collectionForm, () => this.api.createCollection({
      name: this.collectionForm.controls.name.value,
      season_id: this.collectionForm.controls.season_id.value || null,
    }), 'Colección creada correctamente.');
  }

  protected async submitProduct(): Promise<void> {
    if (this.productForm.invalid) {
      this.productForm.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');
    try {
      const payload = this.productForm.getRawValue();
      await firstValueFrom(this.api.createProduct({
        sku: payload.sku,
        name: payload.name,
        description: payload.description || null,
        price: payload.price,
        category_id: payload.category_id,
        size_id: payload.size_id || null,
        color_id: payload.color_id || null,
        season_id: payload.season_id || null,
        collection_id: payload.collection_id || null,
      }));
      this.productForm.reset({ sku: '', name: '', description: '', price: '', category_id: '', size_id: '', color_id: '', season_id: '', collection_id: '' });
      await this.loadData();
      this.successMessage.set('Producto creado correctamente.');
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo crear el producto.'));
    } finally {
      this.loading.set(false);
    }
  }

  protected async toggleProductStatus(product: CatalogProduct): Promise<void> {
    const nextStatus = product.status === 'active' ? 'inactive' : 'active';
    try {
      await firstValueFrom(this.api.updateProductStatus(product.id, nextStatus));
      await this.loadData();
      this.successMessage.set('Estado del producto actualizado.');
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo actualizar el producto.'));
    }
  }

  protected seasonName(seasonId: string | null): string {
    if (!seasonId) return 'Sin temporada';
    return this.seasons().find((season) => season.id === seasonId)?.name ?? seasonId;
  }

  private async submitSimple(form: any, action: () => ReturnType<CatalogApiService['createCategory']>, successMessage: string): Promise<void> {
    if (form.invalid) {
      form.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');
    try {
      await firstValueFrom(action());
      form.reset();
      await this.loadData();
      this.successMessage.set(successMessage);
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo guardar el registro.'));
    } finally {
      this.loading.set(false);
    }
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
