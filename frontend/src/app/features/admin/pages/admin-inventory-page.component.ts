import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmSelectImports } from '../../../components/select/src';
import { HlmTable } from '../../../components/table/src';
import { HlmTabsImports } from '../../../components/tabs/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { CatalogBranch } from '../../shared/models/catalog.model';
import {
  InventoryBranchStock,
  InventoryConsolidatedStock,
  InventoryMovement,
} from '../../shared/models/inventory.model';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { InventoryApiService } from '../../shared/services/inventory-api.service';
import { SessionService } from '../../shared/services/session.service';
import { requestWithToast } from '../../../core/utils/request-toast.util';

type InventoryTab = 'consolidated' | 'branch' | 'movements';
type InventoryMovementType = 'income' | 'outcome';

@Component({
  selector: 'app-admin-inventory-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HlmButton, HlmTable, ...HlmBadgeImports, ...HlmCardImports, ...HlmFieldImports, ...HlmSelectImports, ...HlmTabsImports],
  templateUrl: './admin-inventory-page.component.html',
})
export class AdminInventoryPageComponent {
  private readonly catalogApi = inject(CatalogApiService);
  private readonly inventoryApi = inject(InventoryApiService);
  private readonly fb = inject(FormBuilder);
  private readonly session = inject(SessionService);

  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly consolidatedStock = signal<InventoryConsolidatedStock[]>([]);
  protected readonly branchStock = signal<InventoryBranchStock[]>([]);
  protected readonly movements = signal<InventoryMovement[]>([]);
  protected readonly selectedBranchId = signal('');
  protected readonly activeTab = signal<InventoryTab>('consolidated');
  protected readonly loading = signal(false);
  protected readonly submitting = signal(false);
  protected readonly movementModalOpen = signal(false);
  protected readonly transferModalOpen = signal(false);
  protected readonly movementType = signal<InventoryMovementType>('income');
  protected readonly isAdmin = computed(() => this.session.user()?.rol === 'administrador');
  protected readonly isManager = computed(() => this.session.user()?.rol === 'encargado');
  protected readonly tabs = computed<InventoryTab[]>(() => this.isAdmin() ? ['consolidated', 'branch', 'movements'] : ['branch', 'movements']);

  protected readonly incomeForm = this.fb.nonNullable.group({
    variant_id: ['', Validators.required],
    branch_id: ['', Validators.required],
    quantity: [1, [Validators.required, Validators.min(1)]],
    note: [''],
  });

  protected readonly outcomeForm = this.fb.nonNullable.group({
    variant_id: ['', Validators.required],
    branch_id: ['', Validators.required],
    quantity: [1, [Validators.required, Validators.min(1)]],
    note: [''],
  });

  protected readonly transferForm = this.fb.nonNullable.group({
    variant_id: ['', Validators.required],
    from_branch_id: ['', Validators.required],
    to_branch_id: ['', Validators.required],
    quantity: [1, [Validators.required, Validators.min(1)]],
    note: [''],
  });

  constructor() {
    if (this.isManager()) {
      this.activeTab.set('branch');
    }
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

  protected selectTab(tab: string): void {
    if (tab === 'consolidated' || tab === 'branch' || tab === 'movements') {
      this.activeTab.set(tab);
    }
  }

  protected async selectBranch(branchId: string | null | undefined): Promise<void> {
    if (!this.isAdmin()) return;
    this.selectedBranchId.set(branchId ?? '');
    this.incomeForm.controls.branch_id.setValue(this.selectedBranchId());
    this.outcomeForm.controls.branch_id.setValue(this.selectedBranchId());
    this.transferForm.controls.from_branch_id.setValue(this.selectedBranchId());
    await this.loadBranchData();
    await this.loadMovements();
  }

  protected activeBranchStock(): InventoryBranchStock[] {
    return this.branchStock().filter((item) => item.status === 'active');
  }

  protected readonly variantSelectLabel = (variantId: string | null | undefined): string => {
    if (!variantId) return 'Variante activa';
    const variant = this.activeBranchStock().find((item) => item.variant_id === variantId);
    return variant ? `${variant.product_name} · ${variant.variant_sku}` : variantId;
  };

  protected readonly branchSelectLabel = (branchId: string | null | undefined): string => {
    return this.branchLabel(branchId);
  };

  protected branchOperationLabel(): string {
    return this.isAdmin() ? 'Sucursal de operación' : `Sucursal asignada: ${this.branchLabel(this.selectedBranchId())}`;
  }

  protected readonly movementTypeSelectLabel = (type: InventoryMovementType | null | undefined): string => {
    return type === 'outcome' ? 'Salida' : 'Ingreso';
  };

  protected openMovementModal(): void {
    this.movementType.set('income');
    const branchId = this.isAdmin() ? '' : this.selectedBranchId();
    this.incomeForm.reset({ variant_id: '', branch_id: branchId, quantity: 1, note: '' });
    this.outcomeForm.reset({ variant_id: '', branch_id: branchId, quantity: 1, note: '' });
    this.movementModalOpen.set(true);
  }

  protected closeMovementModal(): void {
    this.movementModalOpen.set(false);
  }

  protected selectMovementType(type: InventoryMovementType | null | undefined): void {
    if (type === 'income' || type === 'outcome') {
      this.movementType.set(type);
    }
  }

  protected async submitMovementModal(): Promise<void> {
    await this.submitMovement(this.movementType());
  }

  protected openTransferModal(): void {
    const branchId = this.isAdmin() ? '' : this.selectedBranchId();
    this.transferForm.reset({
      variant_id: '',
      from_branch_id: branchId,
      to_branch_id: '',
      quantity: 1,
      note: '',
    });
    this.transferModalOpen.set(true);
  }

  protected closeTransferModal(): void {
    this.transferModalOpen.set(false);
  }

  protected async registerTransfer(): Promise<void> {
    if (this.transferForm.invalid) {
      this.transferForm.markAllAsTouched();
      return;
    }

    this.submitting.set(true);
    try {
      await requestWithToast(this.inventoryApi.registerTransfer(this.transferForm.getRawValue()), {
        loading: 'Registrando traspaso...',
        success: 'Traspaso registrado correctamente.',
        error: 'No se pudo registrar el traspaso.',
      });
      this.transferForm.patchValue({ quantity: 1, note: '' });
      this.closeTransferModal();
      await this.refresh();
    } catch {
      // El toast de error ya se mostró.
    } finally {
      this.submitting.set(false);
    }
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

  protected formatDateTime(value: string | null | undefined): string {
    if (!value) return 'Sin fecha';
    return new Intl.DateTimeFormat('es-BO', {
      dateStyle: 'medium',
      timeStyle: 'short',
      timeZone: 'America/La_Paz',
    }).format(new Date(value));
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
      const branches = await firstValueFrom(this.catalogApi.listPublicBranches());

      this.branches.set(branches.data ?? []);
      if (this.isAdmin()) {
        const consolidated = await firstValueFrom(this.inventoryApi.getConsolidatedStock());
        this.consolidatedStock.set(consolidated.data ?? []);
      }

      if (this.isManager()) {
        this.selectedBranchId.set(this.session.user()?.branch_id ?? '');
      }
      this.incomeForm.controls.branch_id.setValue(this.selectedBranchId());
      this.outcomeForm.controls.branch_id.setValue(this.selectedBranchId());
      this.transferForm.controls.from_branch_id.setValue(this.selectedBranchId());

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
      if (this.isAdmin()) {
        const consolidated = await firstValueFrom(this.inventoryApi.getConsolidatedStock());
        this.consolidatedStock.set(consolidated.data ?? []);
      }
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

  private async submitMovement(type: 'income' | 'outcome'): Promise<void> {
    const form = type === 'income' ? this.incomeForm : this.outcomeForm;
    if (form.invalid) {
      form.markAllAsTouched();
      return;
    }

    this.submitting.set(true);
    try {
      const request = type === 'income'
        ? this.inventoryApi.registerIncome(form.getRawValue())
        : this.inventoryApi.registerOutcome(form.getRawValue());
      await requestWithToast(request, {
        loading: type === 'income' ? 'Registrando ingreso...' : 'Registrando salida...',
        success: type === 'income' ? 'Ingreso registrado correctamente.' : 'Salida registrada correctamente.',
        error: type === 'income' ? 'No se pudo registrar el ingreso.' : 'No se pudo registrar la salida.',
      });
      form.patchValue({ quantity: 1, note: '' });
      await this.refresh();
      this.closeMovementModal();
    } catch {
      // El toast de error ya se mostró.
    } finally {
      this.submitting.set(false);
    }
  }
}
