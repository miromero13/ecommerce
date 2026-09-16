import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { HlmButton } from '../../../components/button/src';
import { toast } from '@spartan-ng/brain/sonner';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { requestWithToast } from '../../../core/utils/request-toast.util';
import { ReplenishmentApiService } from '../services/replenishment-api.service';
import { ReplenishmentRequest, ReplenishmentStatus } from '../models/replenishment.model';
import { SessionService } from '../services/session.service';
import { CatalogApiService } from '../services/catalog-api.service';

@Component({ selector: 'app-replenishment-page', standalone: true, imports: [CommonModule, HlmButton], templateUrl: './replenishment-page.component.html' })
export class ReplenishmentPageComponent {
  private readonly api = inject(ReplenishmentApiService);
  private readonly catalogApi = inject(CatalogApiService);
  protected readonly session = inject(SessionService);
  protected readonly requests = signal<ReplenishmentRequest[]>([]);
  protected readonly branches = signal<Array<{ id: string; name: string }>>([]);
  protected readonly statusLabels: Record<ReplenishmentStatus, string> = { requested: 'Solicitada', accepted: 'Aceptada', preparing: 'Preparando', awaiting_receipt: 'En camino / por recibir', delivered: 'Recibida' };

  constructor() { void this.load(); }
  protected label(status: ReplenishmentStatus) { return this.statusLabels[status]; }
  protected branchName(id: string) { return this.branches().find((branch) => branch.id === id)?.name ?? id; }
  protected nextAction(request: ReplenishmentRequest): ReplenishmentStatus | null {
    if (this.session.user()?.rol === 'proveedor') return ({ requested: 'accepted', accepted: 'preparing', preparing: 'awaiting_receipt' } as any)[request.status] ?? null;
    return request.status === 'awaiting_receipt' ? 'delivered' : null;
  }
  protected async transition(request: ReplenishmentRequest): Promise<void> {
    const next = this.nextAction(request); if (!next) return;
    try { await requestWithToast(this.api.updateStatus(request.id, next), { loading: 'Actualizando solicitud...', success: 'Solicitud actualizada.', error: 'No se pudo actualizar la solicitud.' }); await this.load(); } catch { /* toast already shown */ }
  }
  private async load(): Promise<void> {
    try {
      const [requests, branches] = await Promise.all([firstValueFrom(this.api.list()), firstValueFrom(this.catalogApi.listPublicBranches())]);
      this.requests.set(requests.data ?? []); this.branches.set(branches.data ?? []);
    } catch (error) { toast.error(getErrorMessage(error, 'No se pudieron cargar las solicitudes.')); }
  }
}
