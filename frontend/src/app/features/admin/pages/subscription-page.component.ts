import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { toast } from '@spartan-ng/brain/sonner';
import { firstValueFrom } from 'rxjs';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  lucideArrowUpRight,
  lucideBot,
  lucideBrainCircuit,
  lucideBuilding2,
  lucideCalendar,
  lucideCamera,
  lucideCheck,
  lucideCheckCircle2,
  lucideCreditCard,
  lucideCrown,
  lucideShieldAlert,
  lucideShieldCheck,
  lucideSparkles,
  lucideStore,
  lucideX,
  lucideZap,
} from '@ng-icons/lucide';

import { HlmButtonImports } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmBadgeImports } from '../../../components/badge/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { PricingTableComponent } from '../../shared/components/pricing-table.component';
import { PLAN_FEATURES, SubscriptionPayment, SubscriptionPlan, SubscriptionSummary } from '../../shared/models/subscription.model';
import { SubscriptionApiService } from '../../shared/services/subscription-api.service';
import { TenantBrandingEditorComponent } from '../../shared/components/tenant-branding-editor.component';
import { SessionService } from '../../shared/services/session.service';
import { ReceiptActionsComponent } from '../../shared/components/receipt-actions.component';

@Component({
  selector: 'app-subscription-page',
  standalone: true,
  imports: [
    TenantBrandingEditorComponent,
    CommonModule,
    FormsModule,
    NgIcon,
    PricingTableComponent,
    ReceiptActionsComponent,
    ...HlmButtonImports,
    ...HlmCardImports,
    ...HlmBadgeImports,
  ],
  providers: [
    provideIcons({
      lucideArrowUpRight,
      lucideBot,
      lucideBrainCircuit,
      lucideBuilding2,
      lucideCalendar,
      lucideCamera,
      lucideCheck,
      lucideCheckCircle2,
      lucideCreditCard,
      lucideCrown,
      lucideShieldAlert,
      lucideShieldCheck,
      lucideSparkles,
      lucideStore,
      lucideX,
      lucideZap,
    }),
  ],
  templateUrl: './subscription-page.component.html',
})
export class SubscriptionPageComponent implements OnInit {
  private readonly subscriptionApi = inject(SubscriptionApiService);
  protected readonly tenantId = inject(SessionService).user()?.tenant_id ?? null;

  readonly summary = signal<SubscriptionSummary | null>(null);
  readonly payments = signal<SubscriptionPayment[]>([]);
  readonly loading = signal<boolean>(true);
  readonly error = signal<string | null>(null);
  readonly features = PLAN_FEATURES;

  readonly showPlans = signal(false);
  readonly selected = signal<{ plan: SubscriptionPlan; billingCycle: 'monthly' | 'yearly' } | null>(null);
  readonly changing = signal(false);
  // Sandbox card: the payment is simulated, same as the onboarding purchase.
  cardNumber = '4242 4242 4242 4242';
  cardHolder = 'Titular de Prueba';
  cardExp = '12/28';
  cardCvv = '123';

  ngOnInit(): void {
    this.loadSubscription();
  }

  async loadSubscription(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    try {
      const res = await firstValueFrom(this.subscriptionApi.getCurrentSubscription());
      if (res.data) {
        this.summary.set(res.data);
        // Without a current plan the company is blocked: offer the plans right away.
        if (!res.data.has_active_subscription) this.showPlans.set(true);
      }
      await this.loadPayments();
    } catch (err: any) {
      this.error.set(err?.error?.message || 'No se pudo cargar la información de la suscripción.');
    } finally {
      this.loading.set(false);
    }
  }

  togglePlans(): void {
    this.showPlans.update((open) => !open);
    this.selected.set(null);
  }

  choosePlan(choice: { plan: SubscriptionPlan; billingCycle: 'monthly' | 'yearly' }): void {
    this.selected.set(choice);
  }

  selectedPrice(): number {
    const choice = this.selected();
    if (!choice) return 0;
    return choice.billingCycle === 'yearly' ? choice.plan.price_yearly : choice.plan.price_monthly;
  }

  async confirmChange(): Promise<void> {
    const choice = this.selected();
    if (!choice || this.changing()) return;
    this.changing.set(true);
    try {
      const res = await firstValueFrom(this.subscriptionApi.changePlan({
        plan_id: choice.plan.id,
        billing_cycle: choice.billingCycle,
        card_number: this.cardNumber.replace(/\s/g, ''),
        card_holder: this.cardHolder.trim(),
        card_exp: this.cardExp.trim(),
        card_cvv: this.cardCvv.trim(),
      }));
      toast.success(res.message);
      if (res.data) this.summary.set(res.data);
      await this.loadPayments();
      this.selected.set(null);
      this.showPlans.set(false);
    } catch (err) {
      toast.error(getErrorMessage(err, 'No se pudo cambiar el plan.'));
    } finally {
      this.changing.set(false);
    }
  }

  private async loadPayments(): Promise<void> {
    try {
      this.payments.set((await firstValueFrom(this.subscriptionApi.getPaymentHistory())).data ?? []);
    } catch {
      this.payments.set([]); // the history is informative; the page still works without it
    }
  }

  hasFeature(key: string): boolean {
    return this.summary()?.features?.includes(key) ?? false;
  }

  getBranchPercentage(): number {
    const s = this.summary();
    if (!s || !s.usage.branches_max) return 0;
    return Math.min(100, Math.round((s.usage.branches_count / s.usage.branches_max) * 100));
  }

  getGarmentPercentage(): number {
    const s = this.summary();
    if (!s || !s.usage.garments_max) return 0;
    return Math.min(100, Math.round((s.usage.garments_count / s.usage.garments_max) * 100));
  }
}
