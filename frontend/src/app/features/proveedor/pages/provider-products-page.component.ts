import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { HlmTable } from '../../../components/table/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { toast } from '@spartan-ng/brain/sonner';
import { CatalogProduct } from '../../shared/models/catalog.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';

@Component({
  selector: 'app-provider-products-page',
  standalone: true,
  imports: [CommonModule, HlmTable],
  templateUrl: './provider-products-page.component.html',
})
export class ProviderProductsPageComponent {
  private readonly api = inject(CatalogApiService);
  private readonly route = inject(ActivatedRoute);
  protected readonly products = signal<CatalogProduct[]>([]);

  constructor() {
    void this.loadProducts();
  }

  private async loadProducts(): Promise<void> {
    try {
      const providerId = this.route.snapshot.paramMap.get('providerId');
      const response = providerId
        ? await firstValueFrom(this.api.listProviderProducts(providerId))
        : await firstValueFrom(this.api.listMyProviderProducts());
      this.products.set(response.data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar los productos.'));
    }
  }
}
