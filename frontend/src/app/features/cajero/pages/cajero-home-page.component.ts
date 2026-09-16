import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { AreaChartComponent } from 'angular-chrts';
import type { BulletLegendItemInterface } from '@unovis/ts';

import { HlmButton } from '../../../components/button/src';
import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmCardImports } from '../../../components/card/src';
import { SalesApiService } from '../../shared/services/sales-api.service';
import { SessionService } from '../../shared/services/session.service';
import { Sale } from '../../shared/models/sale.model';
import { OnBrowserDirective } from '@spartan-ng/helm/utils';

@Component({
  selector: 'app-cajero-home-page',
  standalone: true,
  imports: [CommonModule, AreaChartComponent, OnBrowserDirective, ...HlmBadgeImports, ...HlmCardImports],
  templateUrl: './cajero-home-page.component.html',
})
export class CajeroHomePageComponent {
  private readonly api = inject(SalesApiService);
  private readonly session = inject(SessionService);
  protected readonly sales = signal<Sale[]>([]);
  protected readonly categories: Record<string, BulletLegendItemInterface> = { total_amount: { name: 'Ventas', color: '#10b981' } };
  protected readonly chartData = computed(() => this.sales().map((sale) => ({ label: sale.created_at.slice(0, 10), total_amount: Number(sale.total_amount) })));
  protected readonly total = () => this.sales().reduce((sum, sale) => sum + Number(sale.total_amount), 0).toFixed(2);
  constructor() { void this.load(); }
  private async load(): Promise<void> {
    try { this.sales.set((await firstValueFrom(this.api.listBranchSales(this.session.user()?.branch_id ?? undefined))).data ?? []); } catch { this.sales.set([]); }
  }
}
