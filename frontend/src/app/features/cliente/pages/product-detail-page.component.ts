import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { CatalogNameItem, CatalogProduct, CatalogProductVariant } from '../../shared/models/catalog.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { ChatbotUiService } from '../../shared/services/chatbot-ui.service';
import { VirtualTryOnComponent } from '../../shared/components/virtual-try-on.component';
import { DetectorRopaComponent } from '../../shared/components/detector-ropa.component';
import { DetectorMediapipeComponent } from '../../shared/components/detector-mediapipe.component';

@Component({
  selector: 'app-product-detail-page',
  standalone: true,
  imports: [CommonModule, HlmButton, VirtualTryOnComponent, DetectorRopaComponent, DetectorMediapipeComponent, ...HlmBadgeImports, ...HlmCardImports],
  templateUrl: './product-detail-page.component.html',
})
export class ProductDetailPageComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly api = inject(CatalogApiService);
  private readonly chatbotUi = inject(ChatbotUiService);

  protected readonly product = signal<CatalogProduct | null>(null);
  protected readonly sizes = signal<CatalogNameItem[]>([]);
  protected readonly colors = signal<CatalogNameItem[]>([]);
  protected readonly selectedVariantId = signal<string | null>(null);
  protected readonly loading = signal(true);
  protected readonly origin = signal('/app/cliente');

  constructor() {
    this.chatbotUi.requestClose();
    void this.loadProduct();
  }

  protected variants(): CatalogProductVariant[] {
    return this.product()?.variants ?? [];
  }

  protected selectedVariant(): CatalogProductVariant | null {
    const variants = this.variants();
    return variants.find((variant) => variant.id === this.selectedVariantId()) ?? variants[0] ?? null;
  }

  protected selectVariant(variantId: string): void {
    this.selectedVariantId.set(variantId);
  }

  protected variantLabel(variant: CatalogProductVariant): string {
    const size = this.sizes().find((item) => item.id === variant.size_id)?.name ?? 'Sin talla';
    const color = this.colors().find((item) => item.id === variant.color_id)?.name ?? 'Sin color';
    return `${size} / ${color}`;
  }

  protected goBack(): void {
    void this.router.navigateByUrl(this.origin());
  }

  private async loadProduct(): Promise<void> {
    try {
      const productId = this.route.snapshot.paramMap.get('productId');
      if (!productId) throw new Error('Producto inválido');

      const query = this.route.snapshot.queryParamMap;
      const from = query.get('from');
      this.origin.set(from === 'reservations' ? '/app/cliente/reservations' : from === 'catalog' ? '/app/cliente/catalog' : '/app/cliente');
      const [productResponse, sizes, colors] = await Promise.all([
        firstValueFrom(this.api.getProduct(productId, query.get('branch_id') ?? undefined)),
        firstValueFrom(this.api.listSizes()),
        firstValueFrom(this.api.listColors()),
      ]);
      this.product.set(productResponse.data ?? null);
      this.selectedVariantId.set(productResponse.data?.variants?.[0]?.id ?? null);
      this.sizes.set(sizes.data ?? []);
      this.colors.set(colors.data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo cargar el producto.'));
    } finally {
      this.loading.set(false);
    }
  }
}
