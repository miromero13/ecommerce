import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  lucideAlertTriangle,
  lucideCheckCircle2,
  lucideDownload,
  lucideEye,
  lucideFilter,
  lucidePackage,
  lucideRotateCcw,
  lucideTrash2,
  lucideWallet,
  lucideX,
  lucideXCircle,
} from '@ng-icons/lucide';
import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmInput } from '../../../components/input/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { ReviewRmaItemPayload, RmaItem, RmaRequest } from '../../shared/models/rma.model';
import { RmaApiService } from '../../shared/services/rma-api.service';

@Component({
  selector: 'app-rma-review-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    NgIcon,
    HlmButton,
    HlmInput,
    ...HlmCardImports,
    ...HlmBadgeImports,
  ],
  providers: [
    provideIcons({
      lucideRotateCcw,
      lucideDownload,
      lucideEye,
      lucidePackage,
      lucideCheckCircle2,
      lucideXCircle,
      lucideAlertTriangle,
      lucideWallet,
      lucideTrash2,
      lucideX,
      lucideFilter,
    }),
  ],
  template: `
    <div class="space-y-6 max-w-7xl mx-auto px-4 py-6">
      <!-- Encabezado Encargado -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <h1 class="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <ng-icon name="lucideRotateCcw" class="text-primary w-6 h-6"></ng-icon>
            Gestión de Devoluciones y Mermas (RMA)
          </h1>
          <p class="text-sm text-muted-foreground mt-1">
            Inspección física de prendas devueltas, entregas de cambios de talla en mostrador y derivación a merma técnica (CU21 y CU24).
          </p>
        </div>

        <div class="flex items-center gap-3">
          <!-- Filtro de estado -->
          <select
            [(ngModel)]="selectedStatusFilter"
            (change)="loadRequests()"
            class="text-xs rounded-lg border border-input bg-background px-3 py-2 shadow-sm focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">Todos los estados</option>
            <option value="pending_inspection">Pendientes de Inspección</option>
            <option value="approved">Aprobados</option>
            <option value="partially_approved">Aprobados Parciales</option>
            <option value="rejected">Rechazados</option>
          </select>

          <!-- Botón Liquidación Mensual -->
          <button
            hlmBtn
            variant="outline"
            size="sm"
            class="gap-1.5 text-xs text-amber-700 dark:text-amber-300 border-amber-300 dark:border-amber-800 hover:bg-amber-50 dark:hover:bg-amber-950/30"
            [disabled]="settling()"
            (click)="triggerSettlement()"
          >
            <ng-icon name="lucideWallet" class="w-3.5 h-3.5"></ng-icon>
            {{ settling() ? 'Liquidando...' : 'Cierre Mensual Billeteras' }}
          </button>
        </div>
      </div>

      <!-- Estado de carga -->
      <div *ngIf="loading()" class="py-12 text-center text-muted-foreground text-sm">
        Cargando solicitudes de RMA...
      </div>

      <!-- Bandeja vacía -->
      <div *ngIf="!loading() && rmaList().length === 0" class="text-center py-16 border rounded-xl border-dashed bg-muted/20">
        <ng-icon name="lucidePackage" class="w-10 h-10 text-muted-foreground mx-auto mb-2"></ng-icon>
        <h3 class="text-base font-semibold text-foreground">No hay solicitudes de devolución con este filtro</h3>
        <p class="text-xs text-muted-foreground mt-1">Las solicitudes enviadas por clientes aparecerán aquí para su inspección física en mostrador.</p>
      </div>

      <!-- Listado de Solicitudes -->
      <div *ngIf="!loading() && rmaList().length > 0" class="space-y-4">
        <div *ngFor="let rma of rmaList()" class="border rounded-xl bg-card shadow-sm overflow-hidden">
          <div class="p-4 sm:p-5 bg-muted/30 border-b flex flex-wrap items-center justify-between gap-3">
            <div class="flex items-center gap-3">
              <span class="font-bold text-base tracking-wide">{{ rma.rma_number }}</span>
              <span
                class="px-2.5 py-0.5 rounded-full text-xs font-medium"
                [ngClass]="statusBadgeClass(rma.status)"
              >
                {{ statusLabel(rma.status) }}
              </span>
            </div>

            <div class="flex items-center gap-2">
              <button
                hlmBtn
                variant="outline"
                size="sm"
                class="gap-1.5 text-xs h-8"
                (click)="downloadPdf(rma)"
              >
                <ng-icon name="lucideDownload" class="w-3.5 h-3.5 text-primary"></ng-icon>
                Ficha PDF
              </button>

              <button
                hlmBtn
                size="sm"
                class="gap-1.5 text-xs h-8 bg-primary text-primary-foreground hover:bg-primary/90"
                (click)="openInspectionModal(rma)"
              >
                <ng-icon name="lucideEye" class="w-3.5 h-3.5"></ng-icon>
                Inspección y Dictamen
              </button>
            </div>
          </div>

          <!-- Info Cliente y Prendas -->
          <div class="p-4 sm:p-5 space-y-4">
            <div class="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs bg-muted/10 p-3 rounded-lg text-muted-foreground">
              <div>
                <span class="font-semibold text-foreground">Cliente:</span>
                <span class="ml-1">{{ rma.customer_name }}</span>
              </div>
              <div>
                <span class="font-semibold text-foreground">Email:</span>
                <span class="ml-1">{{ rma.customer_email }}</span>
              </div>
              <div>
                <span class="font-semibold text-foreground">Orden:</span>
                <span class="ml-1">{{ rma.order_number }}</span>
              </div>
              <div>
                <span class="font-semibold text-foreground">Fecha:</span>
                <span class="ml-1">{{ rma.created_at | date:'dd/MM/yyyy HH:mm' }}</span>
              </div>
            </div>

            <!-- Tabla de prendas -->
            <div class="divide-y divide-border/60">
              <div *ngFor="let item of rma.items" class="py-3 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h4 class="font-semibold text-sm text-foreground">{{ item.product_name }}</h4>
                  <p class="text-xs text-muted-foreground">
                    Talle original: <span class="font-medium text-foreground">{{ item.original_size || '-' }}</span> · 
                    Color: <span class="font-medium text-foreground">{{ item.original_color || '-' }}</span> · 
                    Bs. {{ item.unit_price | number:'1.2-2' }} (Cant: {{ item.quantity }})
                  </p>
                  <p class="text-xs text-muted-foreground mt-0.5">
                    <b>Motivo:</b> {{ reasonLabel(item.reason) }} · 
                    <b>Resolución solicitada:</b> {{ item.preferred_resolution === 'exchange' ? 'Cambio por ' + (item.requested_variant_label || 'otra variante') : 'Crédito Billetera' }}
                  </p>
                </div>

                <div class="sm:text-right shrink-0">
                  <span
                    class="px-2 py-0.5 rounded text-[11px] font-semibold inline-block"
                    [ngClass]="itemStatusBadgeClass(item.status)"
                  >
                    {{ itemStatusLabel(item.status) }}
                  </span>
                  <div *ngIf="item.quarantine_record" class="text-[11px] text-destructive font-mono mt-0.5">
                    Merma Oficial: {{ item.quarantine_record }}
                  </div>
                  <div *ngIf="item.status === 'approved_exchange'" class="text-xs text-emerald-600 mt-0.5">
                    Canjeado por: {{ item.replacement_variant_label || 'Talle entregado' }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- MODAL DE INSPECCIÓN TÉCNICA ÍTEM POR ÍTEM (CU21 & CU24) -->
      <div
        *ngIf="inspectingRma()"
        class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto"
      >
        <div class="bg-card w-full max-w-4xl rounded-xl shadow-2xl border my-8 overflow-hidden animate-in fade-in-50 zoom-in-95">
          <!-- Modal Header -->
          <div class="px-6 py-4 border-b flex items-center justify-between bg-muted/30">
            <div>
              <h2 class="text-lg font-bold text-foreground flex items-center gap-2">
                <ng-icon name="lucideRotateCcw" class="text-primary w-5 h-5"></ng-icon>
                Inspección Física de RMA: {{ inspectingRma()?.rma_number }}
              </h2>
              <p class="text-xs text-muted-foreground">Cliente: {{ inspectingRma()?.customer_name }} · Orden: {{ inspectingRma()?.order_number }}</p>
            </div>
            <button
              class="text-muted-foreground hover:text-foreground p-1 rounded-md"
              (click)="closeInspectionModal()"
            >
              <ng-icon name="lucideX" class="w-5 h-5"></ng-icon>
            </button>
          </div>

          <!-- Modal Body: Lista de prendas a dictaminar -->
          <div class="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
            <div *ngFor="let item of inspectingRma()?.items; let i = index" class="border rounded-xl p-4 bg-muted/10 space-y-3">
              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/60 pb-3">
                <div>
                  <h3 class="font-bold text-sm text-foreground flex items-center gap-2">
                    <span>Prenda #{{ i + 1 }}: {{ item.product_name }}</span>
                    <span class="text-xs text-muted-foreground font-normal">({{ item.original_sku }})</span>
                  </h3>
                  <p class="text-xs text-muted-foreground mt-0.5">
                    Talle original: <b class="text-foreground">{{ item.original_size || '-' }}</b> · 
                    Color original: <b class="text-foreground">{{ item.original_color || '-' }}</b> · 
                    Bs. {{ item.unit_price | number:'1.2-2' }}
                  </p>
                  <p class="text-xs text-muted-foreground">
                    <b>Motivo cliente:</b> {{ reasonLabel(item.reason) }}
                    <span *ngIf="item.customer_notes" class="italic"> - "{{ item.customer_notes }}"</span>
                  </p>
                </div>

                <div>
                  <span
                    class="px-2.5 py-1 rounded text-xs font-semibold"
                    [ngClass]="itemStatusBadgeClass(item.status)"
                  >
                    {{ itemStatusLabel(item.status) }}
                  </span>
                </div>
              </div>

              <!-- Si ya está dictaminado -->
              <div *ngIf="item.status !== 'pending'" class="text-xs text-muted-foreground bg-muted/30 p-3 rounded-lg">
                <p><b>Condición física registrada:</b> {{ conditionLabel(item.item_condition) }}</p>
                <p *ngIf="item.inspection_notes"><b>Nota del dictamen:</b> {{ item.inspection_notes }}</p>
                <p *ngIf="item.quarantine_record" class="text-destructive font-mono mt-0.5"><b>Registro de Merma / Baja Técnica:</b> {{ item.quarantine_record }}</p>
                <p *ngIf="item.status === 'approved_refund'" class="text-amber-700 dark:text-amber-300 mt-0.5">
                  Reembolso de Bs. {{ item.refund_amount | number:'1.2-2' }} programado al cierre de mes ({{ item.wallet_settlement_date | date:'dd/MM/yyyy' }})
                </p>
                <p *ngIf="item.status === 'approved_exchange'" class="text-emerald-700 dark:text-emerald-300 mt-0.5">
                  Cambio entregado en el acto: {{ item.replacement_variant_label || 'Talle nuevo entregado' }}
                </p>
              </div>

              <!-- Formulario de Dictamen si está pendiente -->
              <div *ngIf="item.status === 'pending'" class="space-y-3 pt-1">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <!-- Condición física -->
                  <div>
                    <label class="block font-medium text-foreground mb-1">1. Condición física inspeccionada en mostrador:</label>
                    <select
                      [(ngModel)]="reviewDrafts[item.id].item_condition"
                      class="w-full text-xs rounded-md border border-input bg-background px-3 py-1.5 focus:ring-1 focus:ring-primary"
                    >
                      <option value="intact">Intacta (Con etiquetas originales, sin uso, apta venta)</option>
                      <option value="factory_damaged">Falla de fábrica comprobada (Costura rota, tela defectuosa)</option>
                      <option value="customer_damaged">Prenda usada / Manchada / Dañada por cliente (No apta)</option>
                    </select>
                  </div>

                  <!-- Resolución a aplicar -->
                  <div>
                    <label class="block font-medium text-foreground mb-1">2. Resolución a aplicar:</label>
                    <select
                      [(ngModel)]="reviewDrafts[item.id].resolution"
                      class="w-full text-xs rounded-md border border-input bg-background px-3 py-1.5 focus:ring-1 focus:ring-primary"
                    >
                      <option value="exchange">Cambio por otra talla/color (Entregar en el acto)</option>
                      <option value="store_credit">Devolución a Billetera Digital (Acreditar a fin de mes)</option>
                    </select>
                  </div>
                </div>

                <!-- Aviso según condición -->
                <div *ngIf="reviewDrafts[item.id].item_condition === 'factory_damaged'" class="text-xs bg-destructive/10 text-destructive p-2.5 rounded border border-destructive/20 flex items-start gap-2">
                  <ng-icon name="lucideAlertTriangle" class="w-4 h-4 shrink-0 mt-0.5"></ng-icon>
                  <span><b>Acción automática de Merma (CU24):</b> Esta prenda será dada de baja y aislada en cuarentena técnica oficial sin reingresar al catálogo vendible.</span>
                </div>

                <div *ngIf="reviewDrafts[item.id].item_condition === 'customer_damaged'" class="text-xs bg-amber-50 dark:bg-amber-950/30 text-amber-800 dark:text-amber-200 p-2.5 rounded border border-amber-200 dark:border-amber-900">
                  <b>Atención:</b> La prenda fue usada o dañada por el cliente. Si el reclamo original no fue por defecto de fábrica, se emitirá acta de rechazo para devolver la prenda sin mover inventario ni saldo.
                </div>

                <!-- Notas del dictamen -->
                <div>
                  <label class="block text-xs font-medium text-foreground mb-1">Notas de inspección técnica:</label>
                  <input
                    type="text"
                    hlmInput
                    size="sm"
                    [(ngModel)]="reviewDrafts[item.id].inspection_notes"
                    placeholder="Observaciones de la prenda (ej: Etiquetas intactas, se entrega talle L)"
                    class="text-xs h-8"
                  />
                </div>

                <!-- Botones de Acción para el Ítem -->
                <div class="flex items-center justify-end gap-2 pt-2">
                  <button
                    hlmBtn
                    variant="outline"
                    size="sm"
                    class="text-xs text-destructive hover:bg-destructive/10"
                    [disabled]="processingItemId() === item.id"
                    (click)="submitReview(item, 'rejected')"
                  >
                    <ng-icon name="lucideXCircle" class="w-3.5 h-3.5 mr-1"></ng-icon>
                    Rechazar Ítem
                  </button>

                  <button
                    hlmBtn
                    size="sm"
                    class="text-xs bg-emerald-600 text-white hover:bg-emerald-700"
                    [disabled]="processingItemId() === item.id"
                    (click)="submitReview(item, 'approved')"
                  >
                    <ng-icon name="lucideCheckCircle2" class="w-3.5 h-3.5 mr-1"></ng-icon>
                    {{ reviewDrafts[item.id].resolution === 'exchange' ? 'Aprobar y Entregar Cambio' : 'Aprobar y Programar Billetera' }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Modal Footer -->
          <div class="px-6 py-4 border-t bg-muted/20 flex items-center justify-between">
            <button
              hlmBtn
              variant="outline"
              size="sm"
              (click)="closeInspectionModal()"
            >
              Cerrar
            </button>

            <button
              hlmBtn
              size="sm"
              class="gap-1.5"
              (click)="downloadPdf(inspectingRma()!)"
            >
              <ng-icon name="lucideDownload" class="w-4 h-4"></ng-icon>
              Descargar Ficha Dictaminada
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class RmaReviewPageComponent {
  private readonly rmaApi = inject(RmaApiService);

  protected readonly rmaList = signal<RmaRequest[]>([]);
  protected readonly loading = signal(false);
  protected readonly settling = signal(false);
  protected selectedStatusFilter = '';

  // Inspection modal state
  protected readonly inspectingRma = signal<RmaRequest | null>(null);
  protected readonly processingItemId = signal<string | null>(null);
  protected reviewDrafts: Record<string, {
    item_condition: string;
    resolution: string;
    inspection_notes: string;
    replacement_variant_id: string | null;
  }> = {};

  constructor() {
    void this.loadRequests();
  }

  protected async loadRequests(): Promise<void> {
    this.loading.set(true);
    try {
      const res = await firstValueFrom(this.rmaApi.getRmaRequests(this.selectedStatusFilter || undefined));
      this.rmaList.set(res.data || []);
    } catch (err) {
      toast.error(getErrorMessage(err, 'No se pudieron cargar las solicitudes de RMA.'));
    } finally {
      this.loading.set(false);
    }
  }

  protected openInspectionModal(rma: RmaRequest): void {
    this.inspectingRma.set(rma);
    this.reviewDrafts = {};
    for (const item of rma.items) {
      this.reviewDrafts[item.id] = {
        item_condition: 'intact',
        resolution: item.preferred_resolution || 'exchange',
        inspection_notes: '',
        replacement_variant_id: item.requested_variant_id || null,
      };
    }
  }

  protected closeInspectionModal(): void {
    this.inspectingRma.set(null);
  }

  protected async submitReview(item: RmaItem, decisionStatus: 'approved' | 'rejected'): Promise<void> {
    const rma = this.inspectingRma();
    if (!rma) return;

    const draft = this.reviewDrafts[item.id];
    let action = 'restock_available';
    if (draft.item_condition === 'factory_damaged') {
      action = 'scrap_quarantine';
    } else if (draft.item_condition === 'customer_damaged' || decisionStatus === 'rejected') {
      action = 'return_to_customer';
    }

    const payload: ReviewRmaItemPayload = {
      status: decisionStatus,
      item_condition: draft.item_condition,
      action,
      resolution: draft.resolution,
      replacement_variant_id: draft.replacement_variant_id,
      inspection_notes: draft.inspection_notes.trim() || undefined,
    };

    this.processingItemId.set(item.id);
    try {
      const res = await firstValueFrom(this.rmaApi.reviewRmaItem(rma.id, item.id, payload));
      toast.success(`Ítem '${item.product_name}' dictaminado exitosamente.`);
      if (res.data) {
        this.inspectingRma.set(res.data);
      }
      await this.loadRequests();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Error al dictaminar el ítem de RMA.'));
    } finally {
      this.processingItemId.set(null);
    }
  }

  protected async triggerSettlement(): Promise<void> {
    this.settling.set(true);
    try {
      const res = await firstValueFrom(this.rmaApi.settleMonthlyWallets());
      if (res.data) {
        toast.success(
          `Cierre mensual procesado: ${res.data.settled_count} devoluciones acreditadas (Total: Bs. ${res.data.total_amount.toFixed(2)}).`,
        );
      }
      await this.loadRequests();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Error al procesar la liquidación mensual.'));
    } finally {
      this.settling.set(false);
    }
  }

  protected async downloadPdf(rma: RmaRequest): Promise<void> {
    try {
      await this.rmaApi.downloadRmaPdf(rma.id, rma.rma_number);
      toast.success(`Ficha ${rma.rma_number} descargada.`);
    } catch (err) {
      toast.error('No se pudo descargar la ficha en PDF.');
    }
  }

  protected statusLabel(status: string): string {
    const map: Record<string, string> = {
      pending_inspection: 'Pendiente de inspección física',
      approved: 'Aprobado',
      partially_approved: 'Aprobado parcial',
      rejected: 'Rechazado',
      completed: 'Completado',
    };
    return map[status] || status;
  }

  protected statusBadgeClass(status: string): string {
    const map: Record<string, string> = {
      pending_inspection: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
      approved: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300',
      partially_approved: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
      rejected: 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300',
      completed: 'bg-slate-100 text-slate-800 dark:bg-slate-950 dark:text-slate-300',
    };
    return map[status] || 'bg-muted text-muted-foreground';
  }

  protected itemStatusLabel(status: string): string {
    const map: Record<string, string> = {
      pending: 'Pendiente de revisión',
      approved_exchange: 'Aprobado (Cambio entregado)',
      approved_refund: 'Aprobado (Reembolso programado)',
      rejected: 'Rechazado',
    };
    return map[status] || status;
  }

  protected itemStatusBadgeClass(status: string): string {
    const map: Record<string, string> = {
      pending: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
      approved_exchange: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300',
      approved_refund: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
      rejected: 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300',
    };
    return map[status] || 'bg-muted text-muted-foreground';
  }

  protected reasonLabel(reason: string): string {
    const map: Record<string, string> = {
      wrong_size: 'Talle incorrecto',
      wrong_color: 'Color no deseado',
      factory_defect: 'Defecto de fábrica',
      change_of_mind: 'Cambio de opinión',
    };
    return map[reason] || reason;
  }

  protected conditionLabel(cond?: string | null): string {
    const map: Record<string, string> = {
      intact: 'Intacta (Apta venta comercial)',
      factory_damaged: 'Defecto de confección/fábrica',
      customer_damaged: 'Uso/Daño del cliente',
    };
    return cond ? map[cond] || cond : 'Sin inspección';
  }
}
