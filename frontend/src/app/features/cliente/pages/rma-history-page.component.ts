import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  lucideArrowRight,
  lucideCheckCircle2,
  lucideClock,
  lucideDownload,
  lucideFileText,
  lucideHelpCircle,
  lucideInfo,
  lucidePackage,
  lucidePlus,
  lucideRotateCcw,
  lucideX,
  lucideXCircle,
} from '@ng-icons/lucide';
import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmInput } from '../../../components/input/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import {
  CreateRmaItemPayload,
  CreateRmaRequestPayload,
  EligibleOrder,
  EligibleOrderItem,
  RmaItem,
  RmaRequest,
} from '../../shared/models/rma.model';
import { RmaApiService } from '../../shared/services/rma-api.service';

interface SelectedItemDraft {
  order_item_id: string;
  item: EligibleOrderItem;
  selected: boolean;
  reason: string;
  preferred_resolution: string;
  requested_variant_id: string | null;
  customer_notes: string;
}

@Component({
  selector: 'app-rma-history-page',
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
      lucidePlus,
      lucideDownload,
      lucideFileText,
      lucidePackage,
      lucideCheckCircle2,
      lucideXCircle,
      lucideClock,
      lucideX,
      lucideArrowRight,
      lucideInfo,
      lucideHelpCircle,
    }),
  ],
  template: `
    <div class="space-y-6 max-w-6xl mx-auto px-4 py-6">
      <!-- Encabezado -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <h1 class="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <ng-icon name="lucideRotateCcw" class="text-primary w-6 h-6"></ng-icon>
            Mis Devoluciones y Cambios
          </h1>
          <p class="text-sm text-muted-foreground mt-1">
            Gestioná cambios de talla/color o devoluciones con reembolso para tus compras dentro de los 30 días posteriores a la entrega.
          </p>
        </div>

        <button
          hlmBtn
          class="gap-2 shrink-0 bg-primary text-primary-foreground shadow hover:bg-primary/90"
          (click)="openWizard()"
        >
          <ng-icon name="lucidePlus" class="w-4 h-4"></ng-icon>
          Solicitar Devolución / Cambio
        </button>
      </div>

      <!-- Estado de carga -->
      <div *ngIf="loading()" class="py-12 text-center text-muted-foreground">
        Cargando tus solicitudes de devolución...
      </div>

      <!-- Listado vacío -->
      <div *ngIf="!loading() && rmaList().length === 0" class="text-center py-16 border rounded-xl border-dashed bg-muted/20">
        <div class="w-16 h-16 rounded-full bg-primary/10 text-primary mx-auto flex items-center justify-center mb-4">
          <ng-icon name="lucidePackage" class="w-8 h-8"></ng-icon>
        </div>
        <h3 class="text-lg font-semibold text-foreground">No tenés solicitudes activas</h3>
        <p class="text-sm text-muted-foreground max-w-md mx-auto mt-1 mb-6">
          Si compraste una prenda hace menos de 30 días y necesitás cambiarla por otra talla o devolverla por falla, podés iniciar el trámite ahora.
        </p>
        <button hlmBtn variant="outline" (click)="openWizard()">
          Iniciar Solicitud
        </button>
      </div>

      <!-- Listado de Solicitudes -->
      <div *ngIf="!loading() && rmaList().length > 0" class="space-y-4">
        <div *ngFor="let rma of rmaList()" class="border rounded-xl bg-card shadow-sm overflow-hidden">
          <!-- Card Header -->
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
                class="gap-1.5 text-xs h-8 border-primary/30 text-primary hover:bg-primary/10"
                [disabled]="downloadingId() === rma.id"
                (click)="downloadPdf(rma)"
              >
                <ng-icon name="lucideDownload" class="w-3.5 h-3.5"></ng-icon>
                {{ downloadingId() === rma.id ? 'Descargando...' : 'Descargar Ficha PDF' }}
              </button>
            </div>
          </div>

          <!-- Card Body -->
          <div class="p-4 sm:p-5 space-y-4">
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-muted-foreground bg-muted/10 p-3 rounded-lg">
              <div>
                <span class="font-semibold text-foreground">Orden de origen:</span>
                <span class="ml-1">{{ rma.order_number }}</span>
              </div>
              <div>
                <span class="font-semibold text-foreground">Fecha de solicitud:</span>
                <span class="ml-1">{{ rma.created_at | date:'dd/MM/yyyy HH:mm' }}</span>
              </div>
              <div>
                <span class="font-semibold text-foreground">Prendas en trámite:</span>
                <span class="ml-1">{{ rma.items.length }} {{ rma.items.length === 1 ? 'prenda' : 'prendas' }}</span>
              </div>
            </div>

            <!-- Prendas solicitadas -->
            <div class="divide-y divide-border/60">
              <div *ngFor="let item of rma.items" class="py-3 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 rounded-md bg-muted border overflow-hidden shrink-0 flex items-center justify-center">
                    <img *ngIf="item.image_url" [src]="item.image_url" [alt]="item.product_name" class="w-full h-full object-cover" />
                    <ng-icon *ngIf="!item.image_url" name="lucidePackage" class="w-6 h-6 text-muted-foreground"></ng-icon>
                  </div>
                  <div>
                    <h4 class="font-semibold text-sm text-foreground">{{ item.product_name }}</h4>
                    <p class="text-xs text-muted-foreground">
                      Talle original: <span class="font-medium text-foreground">{{ item.original_size || '-' }}</span> · 
                      Color: <span class="font-medium text-foreground">{{ item.original_color || '-' }}</span> · 
                      Bs. {{ item.unit_price | number:'1.2-2' }} (Cant: {{ item.quantity }})
                    </p>
                    <div class="text-xs text-muted-foreground mt-0.5 flex flex-wrap gap-2">
                      <span class="inline-flex items-center gap-1 font-medium text-foreground">
                        Motivo: {{ reasonLabel(item.reason) }}
                      </span>
                      <span>·</span>
                      <span class="inline-flex items-center gap-1 text-primary font-medium">
                        {{ item.preferred_resolution === 'exchange' ? 'Cambio por: ' + (item.requested_variant_label || 'Talle/Color alternativo') : 'Reembolso a Billetera' }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Dictamen individual del ítem -->
                <div class="sm:text-right shrink-0">
                  <span
                    class="px-2 py-0.5 rounded text-[11px] font-semibold inline-block"
                    [ngClass]="itemStatusBadgeClass(item.status)"
                  >
                    {{ itemStatusLabel(item.status) }}
                  </span>

                  <!-- Detalles según resolución dictaminada -->
                  <div *ngIf="item.status === 'approved_exchange'" class="text-xs text-emerald-600 mt-1">
                    Cambio entregado: {{ item.replacement_variant_label || 'Nueva prenda entregada' }}
                  </div>
                  <div *ngIf="item.status === 'approved_refund'" class="text-xs text-amber-600 mt-1">
                    Bs. {{ item.refund_amount | number:'1.2-2' }} programado al cierre de mes ({{ item.wallet_settlement_date | date:'dd/MM/yyyy' }})
                  </div>
                  <div *ngIf="item.quarantine_record" class="text-[11px] text-muted-foreground font-mono mt-0.5">
                    Acta Merma: {{ item.quarantine_record }}
                  </div>
                  <div *ngIf="item.status === 'rejected' && item.inspection_notes" class="text-xs text-destructive mt-1">
                    Motivo: {{ item.inspection_notes }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- MODAL ASISTENTE: NUEVA SOLICITUD -->
      <div
        *ngIf="showWizard()"
        class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto"
      >
        <div class="bg-card w-full max-w-3xl rounded-xl shadow-2xl border my-8 overflow-hidden animate-in fade-in-50 zoom-in-95">
          <!-- Wizard Header -->
          <div class="px-6 py-4 border-b flex items-center justify-between bg-muted/30">
            <div>
              <h2 class="text-lg font-bold text-foreground flex items-center gap-2">
                <ng-icon name="lucideRotateCcw" class="text-primary w-5 h-5"></ng-icon>
                Solicitar Cambio o Devolución (RMA)
              </h2>
              <p class="text-xs text-muted-foreground">Paso {{ wizardStep() }} de 2: {{ wizardStep() === 1 ? 'Seleccioná la orden' : 'Seleccioná las prendas y motivo' }}</p>
            </div>
            <button
              class="text-muted-foreground hover:text-foreground p-1 rounded-md"
              (click)="closeWizard()"
            >
              <ng-icon name="lucideX" class="w-5 h-5"></ng-icon>
            </button>
          </div>

          <!-- Wizard Body: Paso 1 (Seleccionar Orden) -->
          <div *ngIf="wizardStep() === 1" class="p-6 space-y-4">
            <div class="bg-blue-50/50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900 p-3 rounded-lg flex items-start gap-2.5 text-xs text-blue-900 dark:text-blue-200">
              <ng-icon name="lucideInfo" class="w-4 h-4 shrink-0 mt-0.5 text-blue-600"></ng-icon>
              <span>Mostrando compras entregadas en los últimos 30 días con prendas elegibles para cambio o devolución.</span>
            </div>

            <div *ngIf="loadingEligible()" class="text-center py-8 text-muted-foreground text-sm">
              Buscando tus compras elegibles...
            </div>

            <div *ngIf="!loadingEligible() && eligibleOrders().length === 0" class="text-center py-10 space-y-3">
              <p class="text-sm text-muted-foreground">No tenés compras de los últimos 30 días que califiquen para devolución.</p>
              <button hlmBtn variant="outline" size="sm" (click)="closeWizard()">Entendido</button>
            </div>

            <div *ngIf="!loadingEligible() && eligibleOrders().length > 0" class="space-y-3 max-h-96 overflow-y-auto pr-1">
              <div
                *ngFor="let order of eligibleOrders()"
                class="p-4 border rounded-xl hover:border-primary/50 cursor-pointer transition-colors"
                [ngClass]="selectedOrder()?.order_id === order.order_id ? 'border-primary ring-2 ring-primary/20 bg-primary/5' : 'bg-card'"
                (click)="selectOrder(order)"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <span class="font-bold text-sm">{{ order.order_number }}</span>
                    <span class="text-xs text-muted-foreground">
                      Entregado hace {{ order.days_since_delivery }} {{ order.days_since_delivery === 1 ? 'día' : 'días' }}
                    </span>
                  </div>
                  <span class="text-xs font-semibold text-primary">
                    {{ order.items.length }} {{ order.items.length === 1 ? 'prenda' : 'prendas' }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Wizard Body: Paso 2 (Configurar Prendas) -->
          <div *ngIf="wizardStep() === 2" class="p-6 space-y-5 max-h-[75vh] overflow-y-auto">
            <div class="text-xs text-muted-foreground flex items-center justify-between border-b pb-2">
              <span>Orden: <b class="text-foreground">{{ selectedOrder()?.order_number }}</b></span>
              <button class="text-primary hover:underline" (click)="wizardStep.set(1)">Cambiar orden</button>
            </div>

            <div class="space-y-4">
              <h3 class="text-sm font-semibold text-foreground">Seleccioná las prendas que deseás devolver o cambiar:</h3>

              <div *ngFor="let draft of itemDrafts()" class="border rounded-xl p-4 transition-colors" [ngClass]="draft.selected ? 'border-primary/70 bg-primary/5' : 'bg-card'">
                <!-- Checkbox Prenda -->
                <div class="flex items-start gap-3">
                  <input
                    type="checkbox"
                    [id]="'check-' + draft.order_item_id"
                    [(ngModel)]="draft.selected"
                    [disabled]="!draft.item.eligible_for_rma"
                    class="mt-1 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                  />
                  <div class="flex-1">
                    <label [for]="'check-' + draft.order_item_id" class="font-semibold text-sm text-foreground cursor-pointer flex items-center justify-between">
                      <span>{{ draft.item.product_name }}</span>
                      <span class="text-muted-foreground font-normal">Bs. {{ draft.item.unit_price | number:'1.2-2' }}</span>
                    </label>
                    <p class="text-xs text-muted-foreground">
                      Talle original: <span class="font-medium text-foreground">{{ draft.item.size_name || '-' }}</span> · 
                      Color original: <span class="font-medium text-foreground">{{ draft.item.color_name || '-' }}</span>
                    </p>

                    <p *ngIf="!draft.item.eligible_for_rma" class="text-xs text-amber-600 mt-1 font-medium">
                      {{ draft.item.ineligible_reason }}
                    </p>
                  </div>
                </div>

                <!-- Opciones configurables si está seleccionada -->
                <div *ngIf="draft.selected" class="mt-4 pt-3 border-t border-border/60 space-y-3 pl-7">
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <!-- Motivo -->
                    <div>
                      <label class="block text-xs font-medium text-foreground mb-1">Motivo:</label>
                      <select
                        [(ngModel)]="draft.reason"
                        class="w-full text-xs rounded-md border border-input bg-background px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
                      >
                        <option value="wrong_size">Talle incorrecto (muy chico o grande)</option>
                        <option value="wrong_color">Color no deseado</option>
                        <option value="factory_defect">Defecto de fábrica / costura rota</option>
                        <option value="change_of_mind">Cambio de opinión / no me gustó</option>
                      </select>
                    </div>

                    <!-- Resolución deseada -->
                    <div>
                      <label class="block text-xs font-medium text-foreground mb-1">Resolución deseada:</label>
                      <select
                        [(ngModel)]="draft.preferred_resolution"
                        class="w-full text-xs rounded-md border border-input bg-background px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
                      >
                        <option value="exchange">Cambio por otra talla / color (en el acto)</option>
                        <option value="store_credit">Crédito en Billetera (a fin de mes)</option>
                      </select>
                    </div>
                  </div>

                  <!-- Selector de variante si eligió cambio -->
                  <div *ngIf="draft.preferred_resolution === 'exchange'">
                    <label class="block text-xs font-medium text-foreground mb-1">
                      Seleccioná el talle/color de reemplazo (mismo modelo):
                    </label>
                    <select
                      [(ngModel)]="draft.requested_variant_id"
                      class="w-full text-xs rounded-md border border-input bg-background px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
                    >
                      <option [ngValue]="null">-- Seleccionar variante deseada --</option>
                      <option
                        *ngFor="let opt of draft.item.same_product_variants"
                        [ngValue]="opt.variant_id"
                      >
                        Talle {{ opt.size_name || '-' }} · Color {{ opt.color_name || '-' }} (Stock disponible: {{ opt.stock }})
                      </option>
                    </select>
                    <p class="text-[11px] text-muted-foreground mt-1">
                      El cambio se entregará en el mostrador de la sucursal sujeta a disponibilidad de stock.
                    </p>
                  </div>

                  <!-- Aviso de Billetera a fin de mes -->
                  <div *ngIf="draft.preferred_resolution === 'store_credit'" class="text-xs text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/30 p-2.5 rounded border border-amber-200 dark:border-amber-900">
                    Por política de cierre contable y de inventario, el saldo de <b>Bs. {{ draft.item.unit_price | number:'1.2-2' }}</b> se acreditará en tu Billetera Digital al finalizar el mes corriente una vez aprobada la inspección.
                  </div>

                  <!-- Notas adicionales -->
                  <div>
                    <label class="block text-xs font-medium text-foreground mb-1">Detalle o aclaración adicional (opcional):</label>
                    <input
                      type="text"
                      hlmInput
                      size="sm"
                      [(ngModel)]="draft.customer_notes"
                      placeholder="Ej: Me queda ajustada de hombros, prefiero talle L"
                      class="text-xs h-8"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- Nota general -->
            <div>
              <label class="block text-xs font-medium text-foreground mb-1">Comentarios generales para el encargado (opcional):</label>
              <textarea
                [(ngModel)]="generalNotes"
                rows="2"
                placeholder="Observaciones generales de la solicitud..."
                class="w-full text-xs rounded-md border border-input bg-background p-2.5 focus:outline-none focus:ring-1 focus:ring-primary"
              ></textarea>
            </div>
          </div>

          <!-- Wizard Footer -->
          <div class="px-6 py-4 border-t bg-muted/20 flex items-center justify-between">
            <button
              hlmBtn
              variant="outline"
              size="sm"
              (click)="wizardStep() === 2 ? wizardStep.set(1) : closeWizard()"
            >
              {{ wizardStep() === 2 ? 'Volver' : 'Cancelar' }}
            </button>

            <button
              *ngIf="wizardStep() === 1"
              hlmBtn
              size="sm"
              class="gap-1.5"
              [disabled]="!selectedOrder()"
              (click)="continueToItems()"
            >
              Continuar
              <ng-icon name="lucideArrowRight" class="w-4 h-4"></ng-icon>
            </button>

            <button
              *ngIf="wizardStep() === 2"
              hlmBtn
              size="sm"
              class="gap-1.5 bg-primary text-primary-foreground hover:bg-primary/90"
              [disabled]="submitting() || selectedItemsCount() === 0"
              (click)="submitRequest()"
            >
              {{ submitting() ? 'Generando solicitud...' : 'Confirmar y Descargar Ficha' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class RmaHistoryPageComponent {
  private readonly rmaApi = inject(RmaApiService);

  protected readonly rmaList = signal<RmaRequest[]>([]);
  protected readonly loading = signal(false);
  protected readonly downloadingId = signal<string | null>(null);

  // Wizard state
  protected readonly showWizard = signal(false);
  protected readonly wizardStep = signal<1 | 2>(1);
  protected readonly loadingEligible = signal(false);
  protected readonly eligibleOrders = signal<EligibleOrder[]>([]);
  protected readonly selectedOrder = signal<EligibleOrder | null>(null);
  protected readonly itemDrafts = signal<SelectedItemDraft[]>([]);
  protected readonly submitting = signal(false);
  protected generalNotes = '';

  constructor() {
    void this.loadRequests();
  }

  protected async loadRequests(): Promise<void> {
    this.loading.set(true);
    try {
      const res = await firstValueFrom(this.rmaApi.getRmaRequests());
      this.rmaList.set(res.data || []);
    } catch (err) {
      toast.error(getErrorMessage(err, 'No se pudieron cargar tus devoluciones.'));
    } finally {
      this.loading.set(false);
    }
  }

  // [CU21 - Secuencia: Paso 1] El Cliente ejecuta openWizard() en RmaHistoryPageComponent
  protected async openWizard(): Promise<void> {
    this.showWizard.set(true);
    this.wizardStep.set(1);
    this.selectedOrder.set(null);
    this.itemDrafts.set([]);
    this.generalNotes = '';
    this.loadingEligible.set(true);
    try {
      const res = await firstValueFrom(this.rmaApi.getEligibleOrders());
      this.eligibleOrders.set(res.data || []);
    } catch (err) {
      toast.error(getErrorMessage(err, 'No se pudieron obtener las órdenes elegibles.'));
    } finally {
      this.loadingEligible.set(false);
    }
  }

  protected closeWizard(): void {
    this.showWizard.set(false);
  }

  protected selectOrder(order: EligibleOrder): void {
    this.selectedOrder.set(order);
  }

  protected continueToItems(): void {
    const order = this.selectedOrder();
    if (!order) return;

    const drafts: SelectedItemDraft[] = order.items.map((item) => ({
      order_item_id: item.order_item_id,
      item,
      selected: item.eligible_for_rma,
      reason: 'wrong_size',
      preferred_resolution: 'exchange',
      requested_variant_id: item.same_product_variants.length > 0 ? item.same_product_variants[0].variant_id : null,
      customer_notes: '',
    }));

    this.itemDrafts.set(drafts);
    this.wizardStep.set(2);
  }

  protected selectedItemsCount(): number {
    return this.itemDrafts().filter((d) => d.selected).length;
  }

  // [CU21 - Secuencia: Paso 2] El Cliente ejecuta submitRequest() en RmaHistoryPageComponent
  protected async submitRequest(): Promise<void> {
    const order = this.selectedOrder();
    if (!order) return;

    const selectedDrafts = this.itemDrafts().filter((d) => d.selected);
    if (selectedDrafts.length === 0) {
      toast.error('Seleccioná al menos una prenda para la devolución.');
      return;
    }

    const itemsPayload: CreateRmaItemPayload[] = selectedDrafts.map((d) => ({
      order_item_id: d.order_item_id,
      quantity: 1,
      reason: d.reason,
      preferred_resolution: d.preferred_resolution,
      requested_variant_id: d.preferred_resolution === 'exchange' ? d.requested_variant_id : null,
      customer_notes: d.customer_notes.trim() || undefined,
    }));

    const payload: CreateRmaRequestPayload = {
      order_id: order.order_id,
      customer_notes: this.generalNotes.trim() || undefined,
      items: itemsPayload,
    };

    this.submitting.set(true);
    try {
      const res = await firstValueFrom(this.rmaApi.createRmaRequest(payload));
      const createdRma = res.data;
      if (createdRma) {
        toast.success(`Solicitud ${createdRma.rma_number} creada con éxito.`);
        this.closeWizard();
        await this.loadRequests();

        // Descarga automática de la ficha
        try {
          await this.rmaApi.downloadRmaPdf(createdRma.id, createdRma.rma_number);
          toast.info('Se descargó tu Ficha Oficial de Devolución en PDF.');
        } catch (pdfErr) {
          console.error('Error al descargar PDF:', pdfErr);
        }
      }
    } catch (err) {
      toast.error(getErrorMessage(err, 'No se pudo registrar la solicitud de devolución.'));
    } finally {
      this.submitting.set(false);
    }
  }

  protected async downloadPdf(rma: RmaRequest): Promise<void> {
    this.downloadingId.set(rma.id);
    try {
      await this.rmaApi.downloadRmaPdf(rma.id, rma.rma_number);
      toast.success(`Ficha ${rma.rma_number} descargada.`);
    } catch (err) {
      toast.error('No se pudo descargar la ficha en PDF.');
    } finally {
      this.downloadingId.set(null);
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
}
