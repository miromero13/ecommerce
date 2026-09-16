import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { toast } from '@spartan-ng/brain/sonner';

import { HlmCardImports } from '../../../components/card/src';
import { HlmSelectImports } from '../../../components/select/src';
import { HlmTable } from '../../../components/table/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { CatalogBranch } from '../models/catalog.model';
import { Sale } from '../models/sale.model';
import { CatalogApiService } from '../services/catalog-api.service';
import { SalesApiService } from '../services/sales-api.service';
import { SessionService } from '../services/session.service';

@Component({
  selector: 'app-sales-history-page',
  standalone: true,
  imports: [CommonModule, HlmTable, ...HlmCardImports, ...HlmSelectImports],
  templateUrl: './sales-history-page.component.html',
})
export class SalesHistoryPageComponent {
  private readonly salesApi = inject(SalesApiService);
  private readonly catalogApi = inject(CatalogApiService);
  private readonly session = inject(SessionService);

  protected readonly sales = signal<Sale[]>([]);
  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly selectedBranchId = signal('');
  protected readonly loading = signal(false);
  protected readonly isAdmin = () => this.session.user()?.rol === 'administrador';
  protected readonly branchSelectLabel = (branchId: string | null | undefined): string => {
    if (!branchId) return 'Todas las sucursales';
    return this.branches().find((branch) => branch.id === branchId)?.name ?? branchId;
  };

  constructor() {
    if (this.isAdmin()) void this.loadBranches();
    void this.loadSales();
  }

  protected async loadSales(): Promise<void> {
    this.loading.set(true);
    try {
      const branchId = this.isAdmin() ? this.selectedBranchId() || undefined : undefined;
      const response = await firstValueFrom(this.salesApi.listBranchSales(branchId));
      this.sales.set(response.data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar las ventas.'));
      this.sales.set([]);
    } finally {
      this.loading.set(false);
    }
  }

  protected branchChanged(value: string | null | undefined): void {
    this.selectedBranchId.set(value ?? '');
    void this.loadSales();
  }

  protected itemSummary(sale: Sale): string {
    return sale.items.map((item) => `${item.quantity} × ${item.product_name}`).join(', ');
  }

  protected paymentLabel(method: Sale['payment_method']): string {
    return method === 'stripe' ? 'Tarjeta' : 'Efectivo';
  }

  private async loadBranches(): Promise<void> {
    try {
      const response = await firstValueFrom(this.catalogApi.listPublicBranches());
      this.branches.set(response.data ?? []);
    } catch {
      this.branches.set([]);
    }
  }
}
