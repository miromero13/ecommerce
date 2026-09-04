import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

import { getErrorMessage } from '../../../core/utils/http-error.util';
import { CatalogBranch, CatalogNameItem, CatalogProduct } from '../../shared/models/catalog.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';

@Component({
  selector: 'app-catalog-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './catalog-page.component.html',
})
export class CatalogPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(CatalogApiService);

  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly categories = signal<CatalogNameItem[]>([]);
  protected readonly products = signal<CatalogProduct[]>([]);
  protected readonly errorMessage = signal('');
  protected readonly loading = signal(false);

  protected readonly form = this.fb.nonNullable.group({
    q: [''],
    branch_id: [''],
    category_id: [''],
  });

  constructor() {
    void this.loadData();
  }

  protected async search(): Promise<void> {
    this.loading.set(true);
    this.errorMessage.set('');
    try {
      const value = this.form.getRawValue();
      const response = await firstValueFrom(this.api.listProducts({
        q: value.q || undefined,
        branch_id: value.branch_id || undefined,
        category_id: value.category_id || undefined,
      }));
      this.products.set(response.data ?? []);
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo consultar el catálogo.'));
    } finally {
      this.loading.set(false);
    }
  }

  protected async updateBranchAvailability(): Promise<void> {
    await this.search();
  }

  private async loadData(): Promise<void> {
    try {
      const [branches, categories, products] = await Promise.all([
        firstValueFrom(this.api.listPublicBranches()),
        firstValueFrom(this.api.listCategories()),
        firstValueFrom(this.api.listProducts()),
      ]);
      this.branches.set(branches.data ?? []);
      this.categories.set(categories.data ?? []);
      this.products.set(products.data ?? []);
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo cargar el catálogo.'));
    }
  }

  protected branchName(branchId: string | null): string {
    if (!branchId) return 'Sin sucursal';
    return this.branches().find((branch) => branch.id === branchId)?.name ?? branchId;
  }
}
