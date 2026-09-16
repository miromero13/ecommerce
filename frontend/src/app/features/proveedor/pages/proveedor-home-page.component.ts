import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { DonutChartComponent } from 'angular-chrts';
import type { BulletLegendItemInterface } from '@unovis/ts';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmCardImports } from '../../../components/card/src';
import { OnBrowserDirective } from '@spartan-ng/helm/utils';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { ReplenishmentApiService } from '../../shared/services/replenishment-api.service';
import { CatalogProduct } from '../../shared/models/catalog.model';
import { ReplenishmentRequest } from '../../shared/models/replenishment.model';

@Component({
  selector: 'app-proveedor-home-page',
  standalone: true,
  imports: [CommonModule, RouterLink, DonutChartComponent, OnBrowserDirective, ...HlmBadgeImports, ...HlmCardImports],
  templateUrl: './proveedor-home-page.component.html',
})
export class ProveedorHomePageComponent {
  private readonly catalogApi = inject(CatalogApiService);
  private readonly replenishmentApi = inject(ReplenishmentApiService);
  protected readonly products = signal<CatalogProduct[]>([]);
  protected readonly requests = signal<ReplenishmentRequest[]>([]);
  private readonly statusInfo: Record<ReplenishmentRequest['status'], { name: string; color: string }> = {
    requested: { name: 'Solicitadas', color: '#f59e0b' }, accepted: { name: 'Aceptadas', color: '#0ea5e9' },
    preparing: { name: 'Preparando', color: '#8b5cf6' }, awaiting_receipt: { name: 'En camino', color: '#f97316' },
    delivered: { name: 'Recibidas', color: '#10b981' },
  };
  protected readonly requestDistribution = computed(() => Object.entries(this.statusInfo)
    .map(([key, info]) => ({ key, info, value: this.requests().filter((request) => request.status === key).length }))
    .filter((item) => item.value > 0));
  protected readonly requestChartData = computed(() => this.requestDistribution().map((item) => item.value));
  protected readonly requestCategories = computed<Record<string, BulletLegendItemInterface>>(() =>
    Object.fromEntries(this.requestDistribution().map(({ key, info }) => [key, { name: info.name, color: info.color }])));
  constructor() { void this.load(); }
  private async load(): Promise<void> { try { const [products, requests] = await Promise.all([firstValueFrom(this.catalogApi.listMyProviderProducts()), firstValueFrom(this.replenishmentApi.list())]); this.products.set(products.data ?? []); this.requests.set(requests.data ?? []); } catch { /* keep empty state */ } }
}
