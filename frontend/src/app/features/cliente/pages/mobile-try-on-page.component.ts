import { Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { DetectorRopaComponent } from '../../shared/components/detector-ropa.component';
import { CatalogProduct } from '../../shared/models/catalog.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { SessionService } from '../../shared/services/session.service';

/**
 * CU5 live try-on for the Flutter app's WebView: /mobile-try-on?product=..&variant=..#token=..
 * The token travels in the fragment, which is never sent to any server.
 */
@Component({
  selector: 'app-mobile-try-on-page',
  standalone: true,
  imports: [DetectorRopaComponent],
  template: `
    <main class="min-h-screen bg-white p-4 space-y-4">
      @if (error()) {
        <p class="text-sm text-red-600">{{ error() }}</p>
      } @else if (product(); as p) {
        <h1 class="text-lg font-semibold text-slate-900">{{ p.name }}</h1>
        <p class="text-sm text-slate-500">Párate frente a la cámara, de cuerpo entero si puedes, y toca el botón.</p>
        @if (variant(); as v) {
          <app-detector-ropa
            [variantId]="v.id"
            [garmentPoints]="v.garment_points"
            [garmentImageUrl]="v.try_on_image_url ?? v.image_url ?? p.image_url ?? null"
          />
        }
      } @else {
        <p class="text-sm text-slate-500">Cargando prenda...</p>
      }
    </main>
  `,
})
export class MobileTryOnPageComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(CatalogApiService);

  protected readonly product = signal<CatalogProduct | null>(null);
  protected readonly error = signal<string | null>(null);
  private readonly variantId = this.route.snapshot.queryParamMap.get('variant');
  protected readonly variant = computed(() => {
    const variants = this.product()?.variants ?? [];
    return variants.find((v) => v.id === this.variantId) ?? variants[0] ?? null;
  });

  constructor() {
    const token = new URLSearchParams(this.route.snapshot.fragment ?? '').get('token');
    if (token) inject(SessionService).useToken(token);
    void this.load(this.route.snapshot.queryParamMap.get('product'));
  }

  private async load(productId: string | null): Promise<void> {
    if (!productId) {
      this.error.set('Falta la prenda a probar.');
      return;
    }
    try {
      const response = await firstValueFrom(this.api.getProduct(productId));
      this.product.set(response.data ?? null);
    } catch {
      this.error.set('No se pudo cargar la prenda.');
    }
  }
}
