import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { toast } from '@spartan-ng/brain/sonner';
import { OfflineQueueService } from './offline-queue.service';
import { environment } from '../../../environments/environment';
import { getErrorMessage } from '../utils/http-error.util';
import { SessionService } from '../../features/shared/services/session.service';

export type ConflictAction = 'cash_refund' | 'wallet_credit' | 'exchange' | 'delivered';

export interface OfflineConflictItem {
  variant_id: string;
  quantity: number;
  unit_price: number;
  sku: string;
  product_name: string;
}

/** Offline sale that lost the last unit to a sale that reached the server first. Lives on the server. */
export interface OfflineConflict {
  id: string;
  operation_id: string;
  receipt_number: string;
  branch_id: string;
  cashier_id: string;
  cashier_name: string | null;
  reason: string;
  items: OfflineConflictItem[];
  subtotal: number;
  discount: number;
  total: number;
  cash_received: number | null;
  change_returned: number | null;
  customer_name: string | null;
  customer_phone: string | null;
  customer_email: string | null;
  offline_created_at: string;
  status: 'pending' | 'resolved';
  resolution: ConflictAction | null;
  refund_amount: number | null;
  wallet_credit_amount: number | null;
  extra_charged: number | null;
  sale_id: string | null;
  refund_receipt_number: string | null;
  resolution_notes: string | null;
  resolved_at: string | null;
  created_at: string;
}

export interface ResolveConflictRequest {
  action: ConflictAction;
  customer_email?: string;
  exchange_items?: Array<{ variant_id: string; quantity: number }>;
  difference_method?: 'cash' | 'wallet';
  cash_received?: number;
  notes?: string;
}

interface ApiEnvelope<T> {
  statusCode: number;
  message: string;
  data: T;
}

@Injectable({
  providedIn: 'root',
})
export class OfflineSyncService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly session = inject(SessionService);
  private readonly queueService = inject(OfflineQueueService);
  private readonly apiUrl = environment.apiBaseUrl || '/api';

  /** Increases after a sync that changed the server's stock: pages showing stock reload it. */
  readonly stockChanged = signal(0);

  /** Created at app boot by the App component, so the listener exists on every page. */
  constructor() {
    if (typeof window === 'undefined') return;
    window.addEventListener('online', () => void this.triggerAutoSync());
  }

  /**
   * CU30: Sincronización diferida automática al recuperar la conectividad
   */
  // [CU29 - Secuencia: Paso 3.1] CajaPageComponent invoca triggerAutoSync() en OfflineSyncService
  // [CU30 - Secuencia: Paso 1] El sistema dispara triggerAutoSync() en OfflineSyncService (evento del navegador)
  // [CU30 - Secuencia: Paso 2.1] CajaPageComponent invoca triggerAutoSync() en OfflineSyncService
  async triggerAutoSync(): Promise<void> {
    if (this.session.user()?.rol !== 'cajero' || !navigator.onLine) return;
    await this.queueService.loadQueue();
    const pendingCount = this.queueService.pendingCount();
    if (pendingCount === 0) return;

    toast.info(`Sincronizando ${pendingCount} ventas offline pendientes...`);
    const result = await this.queueService.syncBatchNow();
    if (result.synced > 0 || result.conflicts > 0) this.stockChanged.update((n) => n + 1);

    if (result.synced > 0) {
      toast.success(`${result.synced} ventas offline registradas en el servidor.`);
    }
    if (result.rejected > 0) {
      toast.warning(`${result.rejected} ventas offline fueron rechazadas. Revisa la cola local.`);
    }
    if (result.failed > 0) {
      toast.error('No se pudo conectar con el servidor para sincronizar las ventas offline.');
    }
    if (result.conflicts > 0) {
      toast.error(
        `Atención: ${result.conflicts} ventas offline presentaron conflicto de inventario.`,
        {
          action: {
            label: 'Ver conflictos',
            onClick: () => this.router.navigate(['/app/cajero/offline-conflicts']),
          },
          duration: 10000,
        }
      );
    }
  }

  // [CU30 - Secuencia: Pasos 4.1, 5.32] OfflineConflictsPageComponent invoca loadConflicts(status) en OfflineSyncService
  async loadConflicts(
    status: 'pending' | 'resolved' | 'all' = 'pending'
  ): Promise<{ items: OfflineConflict[]; pending_count: number; pending_total: number }> {
    const res = await firstValueFrom(
      this.http.get<ApiEnvelope<{ items: OfflineConflict[]; pending_count: number; pending_total: number }>>(
        `${this.apiUrl}/offline/conflicts`,
        { params: { status } }
      )
    );
    return res.data;
  }

  /** Resolves a conflict once (by conflict id). Returns the updated conflict, or null after showing the error. */
  // [CU30 - Secuencia: Paso 5.1] OfflineConflictsPageComponent invoca resolveConflict(conflictId, body) en OfflineSyncService
  async resolveConflict(conflictId: string, body: ResolveConflictRequest): Promise<OfflineConflict | null> {
    try {
      const res = await firstValueFrom(
        this.http.post<ApiEnvelope<OfflineConflict>>(`${this.apiUrl}/offline/conflicts/${conflictId}/resolve`, body)
      );
      toast.success(res.message || 'Conflicto resuelto.');
      return res.data;
    } catch (err) {
      toast.error(getErrorMessage(err, 'No se pudo resolver el conflicto.'));
      return null;
    }
  }
}
