import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  lucideChevronDown,
  lucideGift,
  lucideLightbulb,
  lucideStar,
  lucideWallet,
  lucideX,
} from '@ng-icons/lucide';
import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInput } from '../../../components/input/src';
import { HlmSelectImports } from '../../../components/select/src';
import { HlmTable } from '../../../components/table/src';
import { HlmTabsImports } from '../../../components/tabs/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { LoyaltyBalance, LoyaltyMovement } from '../../shared/models/loyalty.model';
import { WalletBalance, WalletTransaction } from '../../shared/models/wallet.model';
import { GiftCardApiService } from '../../shared/services/gift-card-api.service';
import { GiftCardPaymentIntent } from '../../shared/models/gift-card.model';
import { StripeCardPaymentComponent } from '../../shared/components/stripe-card-payment.component';
import { LoyaltyApiService } from '../../shared/services/loyalty-api.service';
import { WalletApiService } from '../../shared/services/wallet-api.service';

const CONCEPT_LABELS: Record<string, string> = {
  gift_card_redeem: 'Canje de Gift Card',
  points_conversion: 'Conversión de Puntos a Saldo',
  order_payment: 'Pago de pedido web/móvil',
  sale_payment: 'Pago en caja física',
  rma_refund: 'Reembolso por devolución (RMA)',
};

const LOYALTY_LABELS: Record<LoyaltyMovement['type'], string> = {
  earn: 'Ganados',
  redeem: 'Canjeados',
  refund: 'Devueltos',
};

/** CU17, CU18 & CU19: Hub Unificado de Billetera Digital y Fidelización con Spartan UI y Select Nativo. */
@Component({
  selector: 'app-wallet-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    NgIcon,
    HlmButton,
    HlmInput,
    HlmTable,
    ...HlmTabsImports,
    ...HlmCardImports,
    ...HlmFieldImports,
    ...HlmSelectImports,
    ...HlmBadgeImports,
    StripeCardPaymentComponent,
  ],
  providers: [
    provideIcons({
      lucideGift,
      lucideWallet,
      lucideStar,
      lucideLightbulb,
      lucideChevronDown,
      lucideX,
    }),
  ],
  template: `
    <section class="space-y-6 text-slate-700">
      <header>
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 class="text-2xl font-semibold text-slate-900">Mi Billetera Digital</h1>
            <p class="text-sm text-slate-500">
              Administra tu saldo prepagado, convierte tus puntos de fidelidad y compra tarjetas de regalo.
            </p>
          </div>
          <button hlmBtn type="button" (click)="openGiftModal()" class="flex items-center gap-1.5">
            <ng-icon name="lucideGift" class="size-4"></ng-icon>
            <span>Comprar Gift Card</span>
          </button>
        </div>
      </header>

      <!-- Tarjeta Principal de Saldo y Canje Rápido -->
      <div class="grid gap-6 lg:grid-cols-12">
        <div class="lg:col-span-6">
          <div class="relative overflow-hidden rounded-3xl bg-gradient-to-tr from-slate-950 via-indigo-950 to-slate-900 p-7 text-white shadow-xl aspect-[1.75/1] flex flex-col justify-between border border-indigo-900/40">
            <div class="flex items-center justify-between">
              <div>
                <span class="text-[10px] font-semibold uppercase tracking-widest text-indigo-300">Fashion Store Hub</span>
                <p class="text-lg font-bold tracking-tight">Saldo en Billetera</p>
              </div>
              <div class="h-8 w-11 rounded-lg bg-amber-400/90 border border-amber-300 shadow flex items-center justify-center">
                <div class="h-4 w-7 rounded border border-amber-700/60"></div>
              </div>
            </div>

            <div class="my-auto py-2">
              <p class="text-xs text-indigo-200 uppercase tracking-wider">Saldo total disponible</p>
              <div class="flex items-baseline gap-2">
                <span class="text-4xl font-extrabold tracking-tight">
                  \${{ (wallet()?.balance ?? 0) | number: '1.2-2' }}
                </span>
                <span class="text-sm font-semibold text-indigo-400 uppercase">
                  {{ wallet()?.currency ?? 'BOB' }}
                </span>
              </div>
            </div>

            <div class="flex items-center justify-between border-t border-white/10 pt-3 text-xs text-slate-300">
              <span class="flex items-center gap-1.5">
                <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>Activa para compras en cualquier tienda</span>
              </span>
              <span class="text-indigo-300 font-medium">100 Puntos = 1 Bs</span>
            </div>
          </div>
        </div>

        <!-- Caja de Canje Rápido de Gift Card con Spartan HlmCard y HlmInput -->
        <div class="lg:col-span-6">
          <section hlmCard class="h-full bg-white p-6 shadow-sm flex flex-col justify-between rounded-3xl border border-slate-200">
            <div class="space-y-4">
              <div class="flex items-center gap-3">
                <div class="flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
                  <ng-icon name="lucideGift" class="size-5"></ng-icon>
                </div>
                <div>
                  <h2 class="text-sm font-bold text-slate-900">¿Tienes una Tarjeta de Regalo?</h2>
                  <p class="text-xs text-slate-500">Ingresa el código para acreditar el saldo de inmediato a tu billetera.</p>
                </div>
              </div>

              <div class="flex gap-2 pt-2">
                <input
                  hlmInput
                  class="w-full font-mono uppercase"
                  [(ngModel)]="cardCodeInput"
                  placeholder="GIFT-2026-X89Q"
                  (keyup.enter)="redeemCard()"
                />
                <button
                  hlmBtn
                  type="button"
                  [disabled]="isRedeeming() || !cardCodeInput.trim()"
                  (click)="redeemCard()"
                >
                  {{ isRedeeming() ? 'Canjeando...' : 'Canjear' }}
                </button>
              </div>
            </div>

            <div class="pt-4 border-t border-slate-100 flex items-center justify-between text-xs">
              <span class="text-slate-500">¿Quieres obsequiar un voucher a alguien?</span>
              <button
                hlmBtn
                variant="link"
                size="sm"
                type="button"
                (click)="openGiftModal()"
                class="!px-0 font-semibold text-indigo-600"
              >
                + Comprar Gift Card →
              </button>
            </div>
          </section>
        </div>
      </div>

      <!-- Tabs de Spartan UI -->
      <hlm-tabs [tab]="activeTab()" class="w-full" (tabActivated)="selectTab($event)">
        <hlm-tabs-list aria-label="Secciones de billetera" class="!flex !w-fit !flex-wrap !gap-2 !border-0 !bg-transparent !p-0 !rounded-md">
          <button
            hlmTabsTrigger="movimientos"
            type="button"
            class="!w-fit !min-h-9 !rounded-xl !px-4 !py-1 text-xs font-semibold flex items-center gap-1.5"
          >
            <ng-icon name="lucideWallet" class="size-3.5"></ng-icon>
            <span>Mi Saldo y Movimientos</span>
          </button>
          <button
            hlmTabsTrigger="puntos"
            type="button"
            class="!w-fit !min-h-9 !rounded-xl !px-4 !py-1 text-xs font-semibold flex items-center gap-1.5"
          >
            <ng-icon name="lucideStar" class="size-3.5"></ng-icon>
            <span>Puntos de Fidelidad ({{ totalPoints() }})</span>
            @if (totalPoints() >= 100) {
              <span class="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-800">
                Convertibles
              </span>
            }
          </button>
        </hlm-tabs-list>
      </hlm-tabs>

      <!-- TAB 1: MOVIMIENTOS DE SALDO CON HLMTABLE -->
      @if (activeTab() === 'movimientos') {
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-base font-bold text-slate-900">Historial de Transacciones de Billetera</h2>
            <span class="text-xs text-slate-400">{{ transactions().length }} registros</span>
          </div>

          <div class="overflow-hidden rounded-xl border border-slate-200 bg-white">
            <table hlmTable class="w-full">
              <thead class="bg-primary text-left text-xs font-bold uppercase tracking-wide text-white">
                <tr>
                  <th class="px-4 py-3">Fecha</th>
                  <th class="px-4 py-3">Concepto</th>
                  <th class="px-4 py-3">Detalle</th>
                  <th class="px-4 py-3 text-right">Monto</th>
                  <th class="px-4 py-3 text-right">Saldo posterior</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-200 text-sm">
                @for (tx of transactions(); track tx.id) {
                  <tr class="hover:bg-slate-50">
                    <td class="px-4 py-3 text-xs text-slate-600">{{ tx.created_at | date: 'dd/MM/yyyy HH:mm' }}</td>
                    <td class="px-4 py-3 font-medium text-slate-900">{{ label(tx.concept) }}</td>
                    <td class="px-4 py-3 text-xs text-slate-500">{{ tx.description || '-' }}</td>
                    <td class="px-4 py-3 text-right font-semibold" [class.text-emerald-600]="tx.type === 'credit'" [class.text-rose-600]="tx.type === 'debit'">
                      {{ tx.type === 'credit' ? '+' : '-' }}\${{ tx.amount | number: '1.2-2' }}
                    </td>
                    <td class="px-4 py-3 text-right font-mono text-xs text-slate-700">\${{ tx.balance_after | number: '1.2-2' }}</td>
                  </tr>
                }
                @if (!transactions().length) {
                  <tr>
                    <td class="px-4 py-8 text-center text-sm text-slate-500" colspan="5">
                      Aún no tienes movimientos en tu billetera digital. Canjea una Gift Card o convierte tus puntos a saldo para empezar.
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        </div>
      }

      <!-- TAB 2: PUNTOS DE FIDELIDAD Y CONVERSIÓN A SALDO -->
      @if (activeTab() === 'puntos') {
        <div class="space-y-6">
          <div class="rounded-2xl border border-amber-200 bg-amber-50/60 p-4 text-xs text-amber-900 flex items-start gap-3">
            <ng-icon name="lucideLightbulb" class="size-5 shrink-0 text-amber-700 mt-0.5"></ng-icon>
            <div>
              <p class="font-bold">¿Cómo funcionan tus puntos?</p>
              <p class="mt-0.5">
                Por cada 10 Bs que pagas en prendas ganas 1 punto. Cada 100 puntos equivalen a 1 Bs. 
                Puedes <strong>convertir tus puntos a saldo directo de tu Billetera</strong> para usarlos en cualquier compra sin restricciones.
              </p>
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            @for (row of loyaltyBalances(); track row.tenant_id) {
              <section hlmCard class="p-5 shadow-sm space-y-4 flex flex-col justify-between rounded-2xl bg-white border border-slate-200">
                <div>
                  <div class="flex items-center justify-between">
                    <p class="font-bold text-slate-900">{{ row.tenant_name }}</p>
                    <span class="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800">
                      {{ row.tier }}
                    </span>
                  </div>
                  <p class="mt-2 text-3xl font-black text-slate-900">
                    {{ row.points_balance }} <span class="text-xs font-normal text-slate-500">puntos</span>
                  </p>
                  <p class="text-xs text-slate-500 mt-0.5">
                    Equivalen a <strong>\${{ row.balance_value | number: '1.2-2' }} BOB</strong> · {{ row.lifetime_points }} acumulados de por vida
                  </p>
                </div>

                <div class="pt-3 border-t border-slate-100">
                  @if (row.points_balance >= 100) {
                    <button
                      hlmBtn
                      class="w-full bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs"
                      type="button"
                      [disabled]="convertingTenantId() === row.tenant_id"
                      (click)="convertPoints(row)"
                    >
                      {{ convertingTenantId() === row.tenant_id ? 'Convirtiendo...' : 'Convertir a $' + (row.points_balance / 100 | number: '1.2-2') + ' BOB en Billetera' }}
                    </button>
                  } @else {
                    <p class="text-[11px] text-center text-slate-400 font-medium">
                      Necesitas al menos 100 puntos para convertirlos a saldo.
                    </p>
                  }
                </div>
              </section>
            } @empty {
              <div class="col-span-full rounded-2xl border border-dashed border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
                Aún no tienes puntos de fidelidad. Acumularás puntos automáticamente con tus compras en cada marca.
              </div>
            }
          </div>

          <!-- Historial de Puntos Colapsable (por defecto cerrado) -->
          @if (loyaltyMovements().length) {
            <div class="rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-sm">
              <button
                type="button"
                (click)="showPointsHistory.set(!showPointsHistory())"
                class="w-full flex items-center justify-between p-4 text-left transition hover:bg-slate-50"
              >
                <div class="flex items-center gap-2">
                  <span class="text-sm font-bold text-slate-900">Historial de Puntos Ganados y Canjeados</span>
                  <span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600 font-medium">
                    {{ loyaltyMovements().length }} movimientos
                  </span>
                </div>
                <span class="text-xs text-indigo-600 font-semibold flex items-center gap-1">
                  <span>{{ showPointsHistory() ? 'Ocultar historial' : 'Ver historial completo' }}</span>
                  <ng-icon name="lucideChevronDown" class="size-4 transition-transform duration-200" [class.rotate-180]="showPointsHistory()"></ng-icon>
                </span>
              </button>

              @if (showPointsHistory()) {
                <div class="border-t border-slate-100 overflow-x-auto">
                  <table hlmTable class="w-full text-xs">
                    <thead class="bg-primary text-left uppercase text-white font-bold">
                      <tr>
                        <th class="px-4 py-3">Fecha</th>
                        <th class="px-4 py-3">Empresa</th>
                        <th class="px-4 py-3">Movimiento</th>
                        <th class="px-4 py-3">Origen</th>
                        <th class="px-4 py-3 text-right">Puntos</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                      @for (m of loyaltyMovements(); track m.id) {
                        <tr class="hover:bg-slate-50">
                          <td class="px-4 py-3 text-slate-600">{{ m.created_at | date: 'dd/MM/yyyy HH:mm' }}</td>
                          <td class="px-4 py-3 font-semibold text-slate-800">{{ m.tenant_name }}</td>
                          <td class="px-4 py-3">{{ loyaltyLabel(m.type) }}</td>
                          <td class="px-4 py-3 text-slate-500">
                            {{ m.source_type === 'order' ? 'Pedido web' : (m.source_type === 'sale' ? 'Venta en tienda' : 'Billetera Digital') }}
                          </td>
                          <td class="px-4 py-3 text-right font-bold" [class.text-emerald-700]="m.type !== 'redeem'" [class.text-rose-700]="m.type === 'redeem'">
                            {{ m.type === 'redeem' ? '-' : '+' }}{{ m.points }}
                          </td>
                        </tr>
                      }
                    </tbody>
                  </table>
                </div>
              }
            </div>
          }
        </div>
      }

      <!-- MODAL COMPRAR GIFT CARD (Estilo Spartan con hlmCard, hlmField, hlmSelect y hlmInput) -->
      @if (showGiftModal()) {
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4 py-6 backdrop-blur-sm" (click)="showGiftModal.set(false)">
          <section hlmCard class="w-full max-w-2xl bg-white shadow-2xl rounded-2xl" (click)="$event.stopPropagation()">
            <div hlmCardHeader class="space-y-1 border-b border-slate-200 pb-4 flex items-center justify-between">
              <div>
                <h2 hlmCardTitle class="text-xl flex items-center gap-2">
                  <ng-icon name="lucideGift" class="size-5 text-indigo-600"></ng-icon>
                  <span>Comprar Tarjeta de Regalo</span>
                </h2>
                <p class="text-xs text-slate-500">El destinatario recibirá un correo con el voucher y código QR para canjear.</p>
              </div>
              <button hlmBtn variant="outline" size="sm" type="button" (click)="showGiftModal.set(false)">
                <ng-icon name="lucideX" class="size-4"></ng-icon>
              </button>
            </div>

            <div class="grid gap-6 p-6 sm:grid-cols-12">
              <div class="space-y-4 sm:col-span-7">
                <!-- Select de Spartan UI para monto -->
                <div hlmField>
                  <label hlmFieldLabel for="gift-amount-select">Monto del regalo</label>
                  <div hlmSelect [value]="selectAmountValue()" [itemToString]="amountSelectLabel" (selectedChange)="onAmountSelectChange($event)">
                    <hlm-select-trigger buttonId="gift-amount-select">
                      <span hlmSelectValue placeholder="Selecciona un monto"></span>
                    </hlm-select-trigger>
                    <hlm-select-content>
                      <hlm-select-item [value]="20">$20.00 BOB</hlm-select-item>
                      <hlm-select-item [value]="50">$50.00 BOB</hlm-select-item>
                      <hlm-select-item [value]="100">$100.00 BOB</hlm-select-item>
                      <hlm-select-item value="custom">Monto personalizado</hlm-select-item>
                    </hlm-select-content>
                  </div>
                </div>

                @if (isCustomGift()) {
                  <div hlmField>
                    <label hlmFieldLabel for="custom-gift-amount">Monto personalizado (BOB, mínimo $10)</label>
                    <input
                      id="custom-gift-amount"
                      hlmInput
                      class="w-full"
                      type="number"
                      min="10"
                      step="5"
                      [(ngModel)]="customGiftAmount"
                      (ngModelChange)="onCustomGiftAmountChange($event)"
                      placeholder="Ej. 150"
                    />
                  </div>
                }

                <div hlmField>
                  <label hlmFieldLabel for="gift-recipient-name">Nombre del destinatario</label>
                  <input
                    id="gift-recipient-name"
                    hlmInput
                    class="w-full"
                    type="text"
                    [(ngModel)]="recipientName"
                    placeholder="Ej. Camila Morales"
                  />
                </div>

                <div hlmField>
                  <label hlmFieldLabel for="gift-recipient-email">Correo electrónico</label>
                  <input
                    id="gift-recipient-email"
                    hlmInput
                    class="w-full"
                    type="email"
                    [(ngModel)]="recipientEmail"
                    placeholder="camila@gmail.com"
                  />
                </div>

                <div hlmField>
                  <label hlmFieldLabel for="gift-custom-message">Mensaje o dedicatoria (opcional)</label>
                  <input
                    id="gift-custom-message"
                    hlmInput
                    class="w-full"
                    type="text"
                    [(ngModel)]="customGiftMessage"
                    placeholder="¡Feliz cumpleaños Cami!"
                  />
                </div>
              </div>

              <!-- Vista previa compacta dentro del modal -->
              <div class="sm:col-span-5 flex flex-col justify-between">
                <div class="relative overflow-hidden rounded-2xl bg-gradient-to-tr from-indigo-900 via-indigo-700 to-violet-600 p-5 text-white shadow-lg aspect-[1.58/1] flex flex-col justify-between">
                  <div class="flex items-start justify-between">
                    <div>
                      <span class="text-[9px] font-semibold uppercase tracking-widest text-indigo-200">Fashion Store</span>
                      <p class="text-sm font-bold">Tarjeta de Regalo</p>
                    </div>
                    <div class="h-6 w-9 rounded bg-amber-400/80 border border-amber-300 shadow-inner flex items-center justify-center">
                      <div class="h-3 w-5 rounded border border-amber-600/50"></div>
                    </div>
                  </div>
                  <div class="my-auto py-1">
                    <p class="text-[9px] text-indigo-200 uppercase">Monto</p>
                    <p class="text-2xl font-black">\${{ giftAmount() }} <span class="text-[10px] font-medium">BOB</span></p>
                    @if (customGiftMessage) {
                      <p class="mt-1 text-[10px] italic text-indigo-100 line-clamp-1">"{{ customGiftMessage }}"</p>
                    }
                  </div>
                  <div class="border-t border-indigo-400/30 pt-1.5 text-[10px] text-indigo-100 flex justify-between">
                    <span class="truncate max-w-[120px]">Para: {{ recipientName || 'Destinatario' }}</span>
                    <span>1 año</span>
                  </div>
                </div>

                @if (pendingGiftPayment(); as pago) {
                  <div class="pt-4">
                    <app-stripe-card-payment
                      [title]="'Pagar la tarjeta de regalo de ' + pago.amount + ' BOB'"
                      [clientSecret]="pago.client_secret"
                      (paid)="onGiftCardPaid()"
                    />
                  </div>
                } @else {
                  <div class="pt-4 flex gap-2 justify-end">
                    <button hlmBtn variant="outline" type="button" (click)="showGiftModal.set(false)">
                      Cancelar
                    </button>
                    <button
                      hlmBtn
                      type="button"
                      [disabled]="isPurchasingGift() || giftAmount() < 10 || !recipientName.trim() || !recipientEmail.trim()"
                      (click)="purchaseGiftCard()"
                    >
                      {{ isPurchasingGift() ? 'Comprando...' : 'Comprar ($' + giftAmount() + ')' }}
                    </button>
                  </div>
                }
              </div>
            </div>
          </section>
        </div>
      }
    </section>
  `,
})
export class WalletPageComponent {
  private readonly walletApi = inject(WalletApiService);
  private readonly loyaltyApi = inject(LoyaltyApiService);
  private readonly giftCardApi = inject(GiftCardApiService);

  protected readonly activeTab = signal<string>('movimientos');
  protected readonly showGiftModal = signal<boolean>(false);
  protected readonly showPointsHistory = signal<boolean>(false);

  // Wallet
  protected readonly wallet = signal<WalletBalance | null>(null);
  protected readonly transactions = signal<WalletTransaction[]>([]);
  protected cardCodeInput = '';
  protected readonly isRedeeming = signal<boolean>(false);

  // Loyalty
  protected readonly loyaltyBalances = signal<LoyaltyBalance[]>([]);
  protected readonly loyaltyMovements = signal<LoyaltyMovement[]>([]);
  protected readonly convertingTenantId = signal<string | null>(null);

  // Gift Card purchase in modal
  protected readonly giftAmount = signal<number>(50);
  protected readonly isCustomGift = signal<boolean>(false);
  protected customGiftAmount: number | null = null;
  protected recipientName = '';
  protected recipientEmail = '';
  protected customGiftMessage = '';
  protected readonly isPurchasingGift = signal<boolean>(false);
  protected readonly pendingGiftPayment = signal<GiftCardPaymentIntent | null>(null);

  constructor() {
    void this.loadAll();
  }

  protected get totalPoints(): () => number {
    return () => this.loyaltyBalances().reduce((acc, row) => acc + row.points_balance, 0);
  }

  protected selectTab(tab: string): void {
    this.activeTab.set(tab);
  }

  protected label(concept: string): string {
    return CONCEPT_LABELS[concept] || concept;
  }

  protected loyaltyLabel(type: LoyaltyMovement['type']): string {
    return LOYALTY_LABELS[type] || type;
  }

  protected openGiftModal(): void {
    this.pendingGiftPayment.set(null);
    this.showGiftModal.set(true);
  }

  protected readonly amountSelectLabel = (val: any): string => {
    if (!val) return 'Selecciona un monto';
    if (val === 'custom') return 'Monto personalizado';
    return `$${val}.00 BOB`;
  };

  protected selectAmountValue(): string | number {
    return this.isCustomGift() ? 'custom' : this.giftAmount();
  }

  protected onAmountSelectChange(val: any): void {
    if (val === 'custom') {
      this.isCustomGift.set(true);
      if (!this.customGiftAmount || this.customGiftAmount < 10) {
        this.customGiftAmount = 150;
      }
      this.giftAmount.set(this.customGiftAmount);
    } else {
      this.isCustomGift.set(false);
      this.giftAmount.set(Number(val));
    }
  }

  protected onCustomGiftAmountChange(val: number): void {
    if (val && val >= 10) {
      this.giftAmount.set(val);
    }
  }

  // [CU19 - Secuencia: Paso 1] El Cliente ejecuta loadAll() en WalletPageComponent
  private async loadAll(): Promise<void> {
    try {
      const [balRes, txRes, loyaltyBalRes, loyaltyMovRes] = await Promise.all([
        firstValueFrom(this.walletApi.balance()),
        firstValueFrom(this.walletApi.transactions()),
        firstValueFrom(this.loyaltyApi.balances()),
        firstValueFrom(this.loyaltyApi.transactions()),
      ]);
      this.wallet.set(balRes.data ?? { balance: 0, currency: 'BOB' });
      this.transactions.set(txRes.data ?? []);
      this.loyaltyBalances.set(loyaltyBalRes.data ?? []);
      this.loyaltyMovements.set(loyaltyMovRes.data ?? []);
    } catch {
      // Ignored
    }
  }

  // [CU19 - Secuencia: Paso 2] El Cliente ejecuta redeemCard() en WalletPageComponent
  protected async redeemCard(): Promise<void> {
    const code = this.cardCodeInput.trim();
    if (!code) return;

    this.isRedeeming.set(true);
    try {
      const res = await firstValueFrom(this.walletApi.redeem(code));
      toast.success(res.message || 'Gift Card canjeada exitosamente.');
      this.cardCodeInput = '';
      void this.loadAll();
    } catch (error) {
      toast.error(getErrorMessage(error, 'El código de la tarjeta de regalo no es válido o ya fue canjeado'));
    } finally {
      this.isRedeeming.set(false);
    }
  }

  // [CU19 - Secuencia: Paso 3] El Cliente ejecuta convertPoints(row) en WalletPageComponent
  protected async convertPoints(row: LoyaltyBalance): Promise<void> {
    const pointsToConvert = Math.floor(row.points_balance / 100) * 100;
    if (pointsToConvert < 100) return;

    this.convertingTenantId.set(row.tenant_id);
    try {
      const res = await firstValueFrom(
        this.walletApi.convertPoints({
          tenant_id: row.tenant_id,
          points: pointsToConvert,
        })
      );
      toast.success(res.message || '¡Puntos convertidos exitosamente a saldo en tu Billetera!');
      void this.loadAll();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron convertir los puntos.'));
    } finally {
      this.convertingTenantId.set(null);
    }
  }

  protected async purchaseGiftCard(): Promise<void> {
    if (this.giftAmount() < 10) {
      toast.error('El importe de la tarjeta de regalo debe ser mayor o igual a $10.00');
      return;
    }
    this.isPurchasingGift.set(true);
    try {
      const res = await firstValueFrom(
        this.giftCardApi.purchase({
          amount: this.giftAmount(),
          recipient_name: this.recipientName.trim(),
          recipient_email: this.recipientEmail.trim(),
          custom_message: this.customGiftMessage.trim() || undefined,
          payment_method: 'stripe',
        })
      );
      this.pendingGiftPayment.set(res.data ?? null);
      toast.info(res.message || 'Pago con Stripe iniciado: ingresa los datos de la tarjeta');
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo completar la compra de la tarjeta de regalo.'));
    } finally {
      this.isPurchasingGift.set(false);
    }
  }

  protected async onGiftCardPaid(): Promise<void> {
    const pago = this.pendingGiftPayment();
    if (!pago) return;
    try {
      const res = await firstValueFrom(this.giftCardApi.confirmPayment(pago.id));
      toast.success(res.message || 'Tarjeta de regalo adquirida y enviada por correo al destinatario');
      this.pendingGiftPayment.set(null);
      this.recipientName = '';
      this.recipientEmail = '';
      this.customGiftMessage = '';
      this.showGiftModal.set(false);
      void this.loadAll();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo confirmar el pago de la tarjeta de regalo.'));
    }
  }
}
