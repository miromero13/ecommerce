import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { toast } from '@spartan-ng/brain/sonner';

import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInput } from '../../../components/input/src';
import { HlmSelectImports } from '../../../components/select/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { GiftCard } from '../../shared/models/gift-card.model';
import { GiftCardApiService } from '../../shared/services/gift-card-api.service';

/** CU18: Emitir y comprar tarjetas de regalo (Gift Cards) con Spartan UI. */
@Component({
  selector: 'app-gift-cards-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    HlmButton,
    HlmInput,
    ...HlmCardImports,
    ...HlmFieldImports,
    ...HlmSelectImports,
  ],
  template: `
    <section class="space-y-8 text-slate-700">
      <header>
        <h1 class="text-2xl font-bold text-slate-900">Tarjetas de Regalo (Gift Cards)</h1>
        <p class="text-sm text-slate-500">
          Obsequia estilo y moda. Compra un voucher prepagado con dedicatoria personalizada, código único y QR enviado directamente al correo del destinatario.
        </p>
      </header>

      <div class="grid gap-8 lg:grid-cols-12">
        <!-- Columna Formulario & Selector de Monto con Spartan UI -->
        <div class="space-y-6 lg:col-span-7">
          <section hlmCard class="p-6 bg-white shadow-sm space-y-6 rounded-2xl border border-slate-200">
            <!-- Select de Spartan UI como en admin-user-page -->
            <div hlmField>
              <label hlmFieldLabel for="gift-amount-select">Monto de la tarjeta de regalo</label>
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

            @if (isCustom()) {
              <div hlmField>
                <label hlmFieldLabel for="custom-gift-amount">Monto personalizado (mínimo $10 BOB)</label>
                <input
                  id="custom-gift-amount"
                  hlmInput
                  class="w-full"
                  type="number"
                  min="10"
                  step="5"
                  [(ngModel)]="customAmount"
                  (ngModelChange)="onCustomAmountChange($event)"
                  placeholder="Ej. 150"
                />
              </div>
            }

            <div class="space-y-4 pt-2 border-t border-slate-100">
              <h3 class="text-sm font-semibold text-slate-900">Datos del destinatario</h3>
              <div hlmField>
                <label hlmFieldLabel for="recipient-name">Nombre completo</label>
                <input
                  id="recipient-name"
                  hlmInput
                  class="w-full"
                  type="text"
                  [(ngModel)]="recipientName"
                  placeholder="Ej. Camila Morales"
                />
              </div>

              <div hlmField>
                <label hlmFieldLabel for="recipient-email">Correo electrónico</label>
                <input
                  id="recipient-email"
                  hlmInput
                  class="w-full"
                  type="email"
                  [(ngModel)]="recipientEmail"
                  placeholder="camila@gmail.com"
                />
              </div>

              <div hlmField>
                <label hlmFieldLabel for="recipient-message">Dedicatoria o mensaje personal (opcional)</label>
                <input
                  id="recipient-message"
                  hlmInput
                  class="w-full"
                  type="text"
                  [(ngModel)]="customMessage"
                  placeholder="¡Feliz cumpleaños Cami!"
                />
              </div>
            </div>

            <button
              hlmBtn
              type="button"
              class="w-full font-bold"
              [disabled]="isSubmitting() || amount() < 10 || !recipientName.trim() || !recipientEmail.trim()"
              (click)="purchase()"
            >
              @if (isSubmitting()) {
                Procesando compra...
              } @else {
                Comprar Gift Card por \${{ amount() }} BOB
              }
            </button>
          </section>
        </div>

        <!-- Columna Vista Previa Interactiva de la Tarjeta -->
        <div class="space-y-4 lg:col-span-5">
          <div class="sticky top-6">
            <h2 class="text-sm font-semibold text-slate-900 mb-3">Vista previa de la tarjeta</h2>
            
            <div class="relative overflow-hidden rounded-3xl bg-gradient-to-tr from-indigo-900 via-indigo-700 to-violet-600 p-6 text-white shadow-xl aspect-[1.58/1] flex flex-col justify-between">
              <div class="flex items-start justify-between">
                <div>
                  <span class="text-xs font-semibold uppercase tracking-widest text-indigo-200">Fashion Store</span>
                  <p class="text-xl font-bold tracking-tight">Tarjeta de Regalo</p>
                </div>
                <div class="h-8 w-11 rounded-lg bg-amber-400/80 border border-amber-300 shadow-inner flex items-center justify-center">
                  <div class="h-4 w-7 rounded border border-amber-600/50"></div>
                </div>
              </div>

              <div class="my-auto py-2">
                <p class="text-xs text-indigo-200 uppercase tracking-wider">Monto del obsequio</p>
                <p class="text-3xl font-extrabold tracking-tight">\${{ amount() }} <span class="text-sm font-medium">BOB</span></p>
                @if (customMessage) {
                  <p class="mt-2 text-xs italic text-indigo-100 line-clamp-2">"{{ customMessage }}"</p>
                }
              </div>

              <div class="flex items-end justify-between border-t border-indigo-400/30 pt-3">
                <div>
                  <p class="text-[10px] text-indigo-200 uppercase tracking-wider">Para</p>
                  <p class="text-sm font-semibold truncate max-w-[180px]">{{ recipientName || 'Nombre del destinatario' }}</p>
                </div>
                <div class="text-right">
                  <p class="text-[10px] text-indigo-200 uppercase tracking-wider">Válida por</p>
                  <p class="text-xs font-medium">1 año</p>
                </div>
              </div>
            </div>

            <p class="mt-3 text-center text-xs text-slate-400">
              Al confirmar, el destinatario recibirá un correo con el código y el QR para canjear en su Billetera Digital.
            </p>
          </div>
        </div>
      </div>

      <!-- Sección Mis Compras de Gift Cards -->
      @if (myPurchases().length) {
        <div class="space-y-4 pt-6">
          <h2 class="text-lg font-bold text-slate-900">Mis Gift Cards Compradas</h2>
          <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            @for (card of myPurchases(); track card.id) {
              <section hlmCard class="p-5 shadow-sm space-y-3 rounded-2xl bg-white border border-slate-200">
                <div class="flex items-center justify-between">
                  <span class="font-mono text-sm font-bold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-lg">
                    {{ card.code }}
                  </span>
                  <span
                    class="rounded-full px-2.5 py-0.5 text-xs font-semibold"
                    [class.bg-emerald-100]="card.status === 'active'"
                    [class.text-emerald-800]="card.status === 'active'"
                    [class.bg-slate-100]="card.status === 'redeemed'"
                    [class.text-slate-600]="card.status === 'redeemed'"
                    [class.bg-rose-100]="card.status === 'expired'"
                    [class.text-rose-800]="card.status === 'expired'"
                  >
                    {{ card.status === 'active' ? 'Activa' : (card.status === 'redeemed' ? 'Canjeada' : 'Expirada') }}
                  </span>
                </div>

                <div>
                  <p class="text-xs text-slate-500">Para: <strong class="text-slate-800">{{ card.recipient_name }}</strong> ({{ card.recipient_email }})</p>
                  <p class="text-xl font-bold text-slate-900 mt-1">\${{ card.amount | number: '1.2-2' }} <span class="text-xs font-normal text-slate-500">BOB</span></p>
                  @if (card.custom_message) {
                    <p class="text-xs italic text-slate-500 mt-1">"{{ card.custom_message }}"</p>
                  }
                </div>

                @if (card.qr_code_url) {
                  <div class="flex items-center gap-3 pt-2 border-t border-slate-100">
                    <img [src]="card.qr_code_url" alt="QR Gift Card" class="h-14 w-14 rounded-lg border border-slate-200" />
                    <div class="text-xs text-slate-500">
                      <p>Escanea este QR para verificar o canjear en Billetera.</p>
                      <a [href]="card.qr_code_url" [download]="'gift-' + card.code + '.png'" class="text-indigo-600 font-semibold hover:underline">
                        Descargar QR
                      </a>
                    </div>
                  </div>
                }
              </section>
            }
          </div>
        </div>
      }
    </section>
  `,
})
export class GiftCardsPageComponent {
  private readonly giftCardApi = inject(GiftCardApiService);

  protected readonly amount = signal<number>(50);
  protected readonly isCustom = signal<boolean>(false);
  protected customAmount: number | null = null;

  protected recipientName = '';
  protected recipientEmail = '';
  protected customMessage = '';

  protected readonly isSubmitting = signal<boolean>(false);
  protected readonly myPurchases = signal<GiftCard[]>([]);

  constructor() {
    void this.loadPurchases();
  }

  protected readonly amountSelectLabel = (val: any): string => {
    if (!val) return 'Selecciona un monto';
    if (val === 'custom') return 'Monto personalizado';
    return `$${val}.00 BOB`;
  };

  protected selectAmountValue(): string | number {
    return this.isCustom() ? 'custom' : this.amount();
  }

  protected onAmountSelectChange(val: any): void {
    if (val === 'custom') {
      this.isCustom.set(true);
      if (!this.customAmount || this.customAmount < 10) {
        this.customAmount = 150;
      }
      this.amount.set(this.customAmount);
    } else {
      this.isCustom.set(false);
      this.amount.set(Number(val));
    }
  }

  protected onCustomAmountChange(val: number): void {
    if (val && val >= 10) {
      this.amount.set(val);
    }
  }

  private async loadPurchases(): Promise<void> {
    try {
      const res = await firstValueFrom(this.giftCardApi.myPurchases());
      this.myPurchases.set(res.data ?? []);
    } catch {
      // Ignore background fetch error
    }
  }

  protected async purchase(): Promise<void> {
    if (this.amount() < 10) {
      toast.error('El importe de la tarjeta de regalo debe ser mayor o igual a $10.00');
      return;
    }
    this.isSubmitting.set(true);
    try {
      const res = await firstValueFrom(
        this.giftCardApi.purchase({
          amount: this.amount(),
          recipient_name: this.recipientName.trim(),
          recipient_email: this.recipientEmail.trim(),
          custom_message: this.customMessage.trim() || undefined,
          payment_method: 'stripe',
        })
      );
      toast.success(res.message || 'Tarjeta de regalo adquirida y enviada por correo al destinatario');
      this.recipientName = '';
      this.recipientEmail = '';
      this.customMessage = '';
      void this.loadPurchases();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo completar la compra de la tarjeta de regalo.'));
    } finally {
      this.isSubmitting.set(false);
    }
  }
}
