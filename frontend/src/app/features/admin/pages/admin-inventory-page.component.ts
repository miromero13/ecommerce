import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmSelectImports } from '../../../components/select/src';
import { HlmTable } from '../../../components/table/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { CatalogBranch } from '../../shared/models/catalog.model';
import {
  InventoryBranchStock,
  InventoryConsolidatedStock,
  InventoryMovement,
} from '../../shared/models/inventory.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { InventoryApiService } from '../../shared/services/inventory-api.service';

@Component({
  selector: 'app-admin-inventory-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HlmButton, HlmTable, ...HlmBadgeImports, ...HlmCardImports, ...HlmFieldImports, ...HlmSelectImports],
  templateUrl: './admin-inventory-page.component.html',
})
export class AdminInventoryPageComponent {
  private readonly catalogApi = inject(CatalogApiService);
  private readonly inventoryApi = inject(InventoryApiService);

  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly consolidatedStock = signal<InventoryConsolidatedStock[]>([]);
  protected readonly branchStock = signal<InventoryBranchStock[]>([]);
  protected readonly movements = signal<InventoryMovement[]>([]);
  protected readonly selectedBranchId = signal('');
  protected readonly loading = signal(false);

  constructor() {
    void this.loadData();
  }

  protected get totalVariants(): number {
    return this.consolidatedStock().length;
  }

  protected get totalQuantity(): number {
    return this.consolidatedStock().reduce((sum, item) => sum + item.quantity, 0);
  }

  protected get availableQuantity(): number {
    return this.consolidatedStock().reduce((sum, item) => sum + item.available_quantity, 0);
  }

  protected get reservedQuantity(): number {
    return this.consolidatedStock().reduce((sum, item) => sum + item.reserved_quantity, 0);
  }

  protected get branchCount(): number {
    return this.branches().length;
  }

  protected get movementCount(): number {
    return this.movements().length;
  }

  protected async refresh(): Promise<void> {
    await this.loadInventoryData();
  }

  protected async selectBranch(branchId: string | null | undefined): Promise<void> {
    this.selectedBranchId.set(branchId ?? '');
    await this.loadBranchData();
    await this.loadMovements();
  }

  protected branchLabel(branchId: string | null | undefined): string {
    if (!branchId) return 'Sin sucursal';
    return this.branches().find((branch) => branch.id === branchId)?.name ?? branchId;
  }

  protected movementTypeLabel(type: InventoryMovement['movement_type']): string {
    switch (type) {
      case 'income':
        return 'Ingreso';
      case 'outcome':
        return 'Salida';
      case 'transfer_in':
        return 'Traspaso entrada';
      case 'transfer_out':
        return 'Traspaso salida';
      default:
        return type;
    }
  }

  protected movementTypeClass(type: InventoryMovement['movement_type']): string {
    switch (type) {
      case 'income':
        return 'bg-emerald-100 text-emerald-700';
      case 'outcome':
        return 'bg-rose-100 text-rose-700';
      case 'transfer_in':
        return 'bg-sky-100 text-sky-700';
      case 'transfer_out':
        return 'bg-amber-100 text-amber-700';
      default:
        return 'bg-slate-100 text-slate-700';
    }
  }

  protected consolidatedBranchNames(item: InventoryConsolidatedStock): string {
    return item.branches.map((branch) => branch.branch_name).join(' · ');
  }

  protected trackById(_: number, item: { id?: string; variant_id?: string }): string {
    return item.id ?? item.variant_id ?? String(_);
  }

  private async loadData(): Promise<void> {
    this.loading.set(true);
    try {
      const [branches, consolidated] = await Promise.all([
        firstValueFrom(this.catalogApi.listPublicBranches()),
        firstValueFrom(this.inventoryApi.getConsolidatedStock()),
      ]);

      this.branches.set(branches.data ?? []);
      this.consolidatedStock.set(consolidated.data ?? []);

      if (!this.selectedBranchId()) {
        const defaultBranch = this.branches().find((branch) => branch.is_default) ?? this.branches()[0] ?? null;
        this.selectedBranchId.set(defaultBranch?.id ?? '');
      }

      await this.loadBranchData();
      await this.loadMovements();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo cargar el inventario.'));
    } finally {
      this.loading.set(false);
    }
  }

  private async loadInventoryData(): Promise<void> {
    this.loading.set(true);
    try {
      const consolidated = await firstValueFrom(this.inventoryApi.getConsolidatedStock());
      this.consolidatedStock.set(consolidated.data ?? []);
      await this.loadBranchData();
      await this.loadMovements();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo refrescar el inventario.'));
    } finally {
      this.loading.set(false);
    }
  }

  private async loadBranchData(): Promise<void> {
    const branchId = this.selectedBranchId();
    if (!branchId) {
      this.branchStock.set([]);
      return;
    }

    try {
      const response = await firstValueFrom(this.inventoryApi.getBranchStock(branchId));
      this.branchStock.set(response.data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo cargar el stock de la sucursal.'));
      this.branchStock.set([]);
    }
  }

  private async loadMovements(): Promise<void> {
    try {
      const response = await firstValueFrom(this.inventoryApi.getMovements({ branch_id: this.selectedBranchId() || undefined, limit: 50 }));
      this.movements.set(response.data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar los movimientos.'));
      this.movements.set([]);
    }
  }
}
