import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { toast } from '@spartan-ng/brain/sonner';
import { OfflineQueueService } from './offline-queue.service';
import { OfflineCatalogService } from './offline-catalog.service';
import { environment } from '../../../environments/environment';

export interface ConflictResolveResponse {
  statusCode: number;
  message: string;
  data: {
    operation_id: string;
    resolution: string;
    customer_email?: string;
    amount_original?: number;
    credited_amount?: number;
    resolved_at: string;
  };
}

@Injectable({
  providedIn: 'root',
})
export class OfflineSyncService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly queueService = inject(OfflineQueueService);
  private readonly catalogService = inject(OfflineCatalogService);

  constructor() {
    this.initAutoSync();
  }

  private initAutoSync(): void {
    if (typeof window === 'undefined') return;

    window.addEventListener('online', () => {
      void this.triggerAutoSync();
    });
  }

  /**
   * CU30: Sincronización diferida automática al recuperar la conectividad
   */
  // [CU30 - Secuencia: Paso 1] El sistema dispara triggerAutoSync() en OfflineSyncService (evento del navegador)
  async triggerAutoSync(): Promise<void> {
    const pendingCount = this.queueService.pendingCount();
    if (pendingCount === 0) return;

    toast.info(`Conexión reestablecida: sincronizando ${pendingCount} operaciones en cola...`);
    const result = await this.queueService.syncBatchNow();

    if (result.synced > 0) {
      toast.success(`${result.synced} operaciones offline consolidadas en el servidor central.`);
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

  /**
   * Resolver colisión de inventario compensando en Billetera (+10%) o devolución física
   */
  // [CU30 - Secuencia: Pasos 4.1, 5.1] OfflineConflictsPageComponent invoca resolveConflict(operationId, action, amount, customerEmail) en OfflineSyncService
  async resolveConflict(
    operationId: string,
    action: 'wallet_compensation' | 'cash_refund',
    amount: number,
    customerEmail?: string | null
  ): Promise<boolean> {
    try {
      const apiUrl = environment.apiBaseUrl || '/api';
      const payload = {
        resolution_action: action,
        customer_email: customerEmail || undefined,
        amount,
        bonus_percent: 10.0,
      };

      const res = await firstValueFrom(
        this.http.post<ConflictResolveResponse>(
          `${apiUrl}/offline/conflicts/${operationId}/resolve`,
          payload
        )
      );

      if (res?.statusCode === 200) {
        // Al resolverlo, removemos la operación de la cola local
        await this.queueService.removeOperation(operationId);
        toast.success(res.message || 'Conflicto resuelto exitosamente.');
        return true;
      }
      return false;
    } catch (err: any) {
      toast.error(err?.error?.detail || 'Error al resolver el conflicto en el servidor.');
      return false;
    }
  }
}
