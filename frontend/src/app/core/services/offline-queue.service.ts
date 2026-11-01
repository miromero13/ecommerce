import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { IndexedDbService, STORES } from './indexeddb.service';
import { environment } from '../../../environments/environment';

export type OfflineOperationType = 'cash_sale' | 'reservation';
export type OfflineOperationStatus = 'local_pending' | 'syncing' | 'synced' | 'rejected';

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
  cash_session_id?: string | null;
  customer_name?: string | null;
  customer_phone?: string | null;
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
  private readonly http = inject(HttpClient);

  // [CU29 - Secuencia: Paso 2.1] OfflineQueueModalComponent invoca operations() en OfflineQueueService (senal que lee la plantilla)
  readonly operations = signal<OfflineOperation[]>([]);
  readonly isSyncing = signal<boolean>(false);
  readonly lastSyncAttempt = signal<Date | null>(null);
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

  // [CU29 - Secuencia: Paso 1] El sistema dispara loadQueue() en OfflineQueueService (evento del navegador)
  // [CU30 - Secuencia: Pasos 1.1, 2.2] OfflineSyncService invoca loadQueue() en OfflineQueueService
  async loadQueue(): Promise<OfflineOperation[]> {
    try {
      // [CU25 - Secuencia: Paso 1.3] OfflineQueueService ejecuta getAll(STORES.PENDING_OPERATIONS_QUEUE) sobre la entidad local OfflineOperation (IndexedDB)
      // [CU29 - Secuencia: Paso 1.1] OfflineQueueService ejecuta getAll<OfflineOperation>(STORES.PENDING_OPERATIONS_QUEUE) sobre la entidad local OfflineOperation (IndexedDB)
      // [CU30 - Secuencia: Pasos 1.2, 2.3] OfflineQueueService ejecuta getAll(STORES.PENDING_OPERATIONS_QUEUE) sobre la entidad local OfflineOperation (IndexedDB)
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
  // [CU25 - Secuencia: Paso 1.1] CajaPageComponent invoca enqueueOperation(input) en OfflineQueueService
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

    // [CU25 - Secuencia: Paso 1.2] OfflineQueueService ejecuta putItem(STORES.PENDING_OPERATIONS_QUEUE, operation) sobre la entidad local OfflineOperation (IndexedDB)
    await this.idb.putItem(STORES.PENDING_OPERATIONS_QUEUE, operation);
    await this.loadQueue();

    return operation;
  }

  async getOperation(operationId: string): Promise<OfflineOperation | null> {
    try {
      // [CU30 - Secuencia: Pasos 1.4, 2.5] OfflineQueueService ejecuta getItem(STORES.PENDING_OPERATIONS_QUEUE, operationId) sobre la entidad local OfflineOperation (IndexedDB)
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

    // [CU30 - Secuencia: Pasos 1.5, 2.6] OfflineQueueService ejecuta putItem(STORES.PENDING_OPERATIONS_QUEUE, updated) sobre la entidad local OfflineOperation (IndexedDB)
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

  /**
   * CU29 / CU30: Dispara la sincronización del lote de operaciones pendientes
   */
  // [CU30 - Secuencia: Pasos 1.3, 2.4] OfflineSyncService invoca syncBatchNow() en OfflineQueueService
  async syncBatchNow(): Promise<{ synced: number; conflicts: number; rejected: number; failed: number }> {
    const empty = { synced: 0, conflicts: 0, rejected: 0, failed: 0 };
    if (this.isSyncing()) return empty;

    // Oldest first: the sale that reaches the server first keeps the last unit.
    // Rejected operations are never resent automatically.
    const pending = this.operations()
      .filter((op) => op.status === 'local_pending')
      .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
    if (!pending.length) return empty;

    this.isSyncing.set(true);
    this.lastSyncAttempt.set(new Date());

    try {
      for (const op of pending) {
        await this.updateStatus(op.operation_id, 'syncing');
      }

      const apiUrl = environment.apiBaseUrl || '/api';
      const payload = {
        operations: pending.map((op) => ({
          operation_id: op.operation_id,
          receipt_number: op.receipt_number,
          type: op.type,
          created_at: op.created_at,
          branch_id: op.branch_id,
          cashier_id: op.cashier_id,
          cash_session_id: op.cash_session_id ?? null,
          customer_name: op.customer_name,
          customer_phone: op.customer_phone ?? null,
          customer_email: op.customer_email ?? null,
          items: op.items.map((it) => ({
            variant_id: it.variant_id,
            quantity: it.quantity,
            unit_price: it.unit_price,
            product_name: it.product_name,
            variant_sku: it.variant_sku,
          })),
          subtotal: op.subtotal,
          discount: op.discount,
          total: op.total,
          cash_received: op.cash_received,
          change_returned: op.change_returned,
          notes: op.notes ?? null,
        })),
      };

      const res = await firstValueFrom(
        this.http.post<{
          statusCode: number;
          data: {
            synced_count: number;
            conflicts_count: number;
            rejected_count: number;
            synced_ids: string[];
            conflicts: Array<{ operation_id: string }>;
            rejected: Array<{ operation_id: string; reason: string }>;
          };
        }>(`${apiUrl}/offline/queue-sync`, payload)
      );

      const data = res?.data;
      if (!data) {
        for (const op of pending) await this.updateStatus(op.operation_id, 'local_pending');
        return { ...empty, failed: pending.length };
      }

      // Synced sales and conflicts now live on the server: drop them from the local queue.
      const done = [...(data.synced_ids || []), ...(data.conflicts || []).map((c) => c.operation_id)];
      for (const id of done) {
        // [CU30 - Secuencia: Pasos 1.20, 2.21] OfflineQueueService ejecuta deleteItem(STORES.PENDING_OPERATIONS_QUEUE, id) sobre la entidad local OfflineOperation (IndexedDB)
        await this.idb.deleteItem(STORES.PENDING_OPERATIONS_QUEUE, id);
      }
      for (const r of data.rejected || []) {
        await this.updateStatus(r.operation_id, 'rejected', r.reason);
      }
      // Anything the server did not mention goes back to pending.
      const handled = new Set([...done, ...(data.rejected || []).map((r) => r.operation_id)]);
      for (const op of pending) {
        if (!handled.has(op.operation_id)) await this.updateStatus(op.operation_id, 'local_pending');
      }

      return {
        synced: data.synced_count || 0,
        conflicts: data.conflicts_count || 0,
        rejected: data.rejected_count || 0,
        failed: 0,
      };
    } catch (err) {
      console.warn('Error sincronizando lote offline con el servidor:', err);
      for (const op of pending) {
        await this.updateStatus(op.operation_id, 'local_pending', 'Error de conexión con el servidor central');
      }
      return { ...empty, failed: pending.length };
    } finally {
      this.isSyncing.set(false);
      await this.loadQueue();
    }
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
