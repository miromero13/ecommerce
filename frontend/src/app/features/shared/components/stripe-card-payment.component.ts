import { CommonModule } from '@angular/common';
import { Component, ElementRef, EventEmitter, Input, OnInit, Output, ViewChild, signal } from '@angular/core';
import { toast } from '@spartan-ng/brain/sonner';
import { Stripe, StripeElements, StripePaymentElement, loadStripe } from '@stripe/stripe-js';

import { HlmButton } from '../../../components/button/src';
import { environment } from '../../../../environments/environment';

/**
 * Card payment with Stripe Elements for an existing PaymentIntent. The backend webhook
 * is the source of truth: `paid` only means Stripe accepted the card.
 */
@Component({
  selector: 'app-stripe-card-payment',
  standalone: true,
  imports: [CommonModule, HlmButton],
  template: `
    <div class="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
      <p class="text-sm font-semibold text-slate-900">{{ title }}</p>
      <div #paymentElement class="min-h-24"></div>
      <button hlmBtn type="button" class="w-full" [disabled]="!ready() || busy()" (click)="confirm()">
        {{ busy() ? 'Procesando...' : 'Pagar con tarjeta' }}
      </button>
    </div>
  `,
})
export class StripeCardPaymentComponent implements OnInit {
  @Input({ required: true }) clientSecret!: string;
  @Input() title = 'Datos de la tarjeta';
  @Output() readonly paid = new EventEmitter<void>();

  protected readonly ready = signal(false);
  protected readonly busy = signal(false);
  private stripe: Stripe | null = null;
  private elements: StripeElements | null = null;
  private element: StripePaymentElement | null = null;

  @ViewChild('paymentElement', { static: true })
  private host!: ElementRef<HTMLDivElement>;

  async ngOnInit(): Promise<void> {
    if (!environment.stripePublishableKey) {
      toast.error('Stripe no está configurado para esta aplicación.');
      return;
    }
    try {
      this.stripe = await loadStripe(environment.stripePublishableKey);
    } catch {
      this.stripe = null;
    }
    if (!this.stripe) {
      toast.error('No se pudo cargar Stripe.');
      return;
    }
    this.elements = this.stripe.elements({ clientSecret: this.clientSecret });
    this.element = this.elements.create('payment');
    this.element.mount(this.host.nativeElement);
    this.ready.set(true);
  }

  protected async confirm(): Promise<void> {
    if (!this.stripe || !this.elements) return;
    this.busy.set(true);
    try {
      const { error, paymentIntent } = await this.stripe.confirmPayment({ elements: this.elements, redirect: 'if_required' });
      if (error) {
        toast.error(error.message ?? 'No se pudo procesar el pago.');
      } else if (paymentIntent?.status === 'succeeded' || paymentIntent?.status === 'processing') {
        toast.success('Pago recibido. Lo confirmaremos en unos segundos.');
        this.paid.emit();
      } else {
        toast.info('El pago está pendiente de confirmación.');
      }
    } catch {
      toast.error('No se pudo procesar el pago.');
    } finally {
      this.busy.set(false);
    }
  }
}
