import { Injectable, computed, inject, signal } from '@angular/core';
import { IndexedDbService, STORES } from './indexeddb.service';

export type OfflineOperationType = 'cash_sale' | 'reservation';
export type OfflineOperationStatus = 'local_pending' | 'syncing' | 'synced' | 'conflict_rejected';

export interface OfflineSaleItem {
  variant_id: string;
  product_name: string;
  variant_sku: string;
  size_name: string | null;
  color_name: string | null;
  unit_price: number;
  original_unit_price: number;
  quantity: number;
  subtotal: number;
}

export interface OfflineOperation {
  operation_id: string; // UUID v4 único para idempotencia
  receipt_number: string; // CONT-YYYYMMDD-XXXX
  type: OfflineOperationType;
  status: OfflineOperationStatus;
  created_at: string; // ISO 8601
  tenant_id?: string | null;
  branch_id?: string | null;
  cashier_name?: string | null;
  cashier_id?: string | null;
  customer_name?: string | null;
  customer_email?: string | null;
  customer_document?: string | null;
  items: OfflineSaleItem[];
  subtotal: number;
  discount: number;
  total: number;
  cash_received?: number | null;
  change_returned?: number | null;
  notes?: string | null;
  sync_error?: string | null;
}

export type EnqueueOperationInput = Omit<
  OfflineOperation,
  'operation_id' | 'receipt_number' | 'created_at' | 'status'
>;

@Injectable({
  providedIn: 'root',
})
export class OfflineQueueService {
  private readonly idb = inject(IndexedDbService);

  readonly operations = signal<OfflineOperation[]>([]);
  readonly pendingCount = computed(() =>
    this.operations().filter((op) => op.status === 'local_pending' || op.status === 'syncing').length
  );
  readonly totalPendingAmount = computed(() =>
    this.operations()
      .filter((op) => op.status === 'local_pending' || op.status === 'syncing')
      .reduce((sum, op) => sum + op.total, 0)
  );

  constructor() {
    void this.loadQueue();
  }

  async loadQueue(): Promise<OfflineOperation[]> {
    try {
      const items = await this.idb.getAll<OfflineOperation>(STORES.PENDING_OPERATIONS_QUEUE);
      // Ordenar por fecha descendente
      items.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      this.operations.set(items);
      return items;
    } catch (err) {
      console.warn('Error cargando cola de operaciones offline:', err);
      return [];
    }
  }

  /**
   * CU25: Encola una venta en efectivo o reserva realizada en contingencia offline
   */
  async enqueueOperation(input: EnqueueOperationInput): Promise<OfflineOperation> {
    const uuid = this.generateUuid();
    const receiptNumber = this.generateReceiptNumber();
    const nowIso = new Date().toISOString();

    const operation: OfflineOperation = {
      ...input,
      operation_id: uuid,
      receipt_number: receiptNumber,
      status: 'local_pending',
      created_at: nowIso,
    };

    await this.idb.putItem(STORES.PENDING_OPERATIONS_QUEUE, operation);
    await this.loadQueue();

    return operation;
  }

  async getOperation(operationId: string): Promise<OfflineOperation | null> {
    try {
      return await this.idb.getItem<OfflineOperation>(STORES.PENDING_OPERATIONS_QUEUE, operationId);
    } catch {
      return null;
    }
  }

  async updateStatus(
    operationId: string,
    status: OfflineOperationStatus,
    syncError?: string
  ): Promise<void> {
    const op = await this.getOperation(operationId);
    if (!op) return;

    const updated: OfflineOperation = {
      ...op,
      status,
      sync_error: syncError ?? op.sync_error,
    };

    await this.idb.putItem(STORES.PENDING_OPERATIONS_QUEUE, updated);
    await this.loadQueue();
  }

  async removeOperation(operationId: string): Promise<void> {
    await this.idb.deleteItem(STORES.PENDING_OPERATIONS_QUEUE, operationId);
    await this.loadQueue();
  }

  async clearQueue(): Promise<void> {
    await this.idb.clearStore(STORES.PENDING_OPERATIONS_QUEUE);
    this.operations.set([]);
  }

  private generateUuid(): string {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  private generateReceiptNumber(): string {
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const dd = String(now.getDate()).padStart(2, '0');
    const randomSuffix = Math.floor(1000 + Math.random() * 9000);
    return `CONT-${yyyy}${mm}${dd}-${randomSuffix}`;
  }
}
