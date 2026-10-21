import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { toast } from '@spartan-ng/brain/sonner';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  lucideArrowLeft,
  lucideArrowRight,
  lucideBuilding2,
  lucideCheck,
  lucideCheckCircle2,
  lucideCreditCard,
  lucideCrown,
  lucideLock,
  lucideMail,
  lucideShieldCheck,
  lucideSparkles,
  lucideUser,
  lucideZap,
} from '@ng-icons/lucide';

import { HlmButtonImports } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmInputImports } from '../../../components/input/src';
import { HlmLabelImports } from '../../../components/label/src';
import { COUNTRIES_LIST } from '../../../core/utils/countries-data.util';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { SubscriptionPlan } from '../models/subscription.model';
import { SubscriptionApiService } from '../services/subscription-api.service';

@Component({
  selector: 'app-onboarding-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    NgIcon,
    ...HlmButtonImports,
    ...HlmCardImports,
    ...HlmBadgeImports,
    ...HlmInputImports,
    ...HlmLabelImports,
  ],
  providers: [
    provideIcons({
      lucideArrowLeft,
      lucideArrowRight,
      lucideBuilding2,
      lucideCheck,
      lucideCheckCircle2,
      lucideCreditCard,
      lucideCrown,
      lucideLock,
      lucideMail,
      lucideShieldCheck,
      lucideSparkles,
      lucideUser,
      lucideZap,
    }),
  ],
  templateUrl: './onboarding-page.component.html',
})
export class OnboardingPageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly subscriptionApi = inject(SubscriptionApiService);

  readonly countries = COUNTRIES_LIST;
  readonly plans = signal<SubscriptionPlan[]>([]);
  readonly loadingPlans = signal<boolean>(true);

  // Form Model
  companyName = '';
  slug = '';
  country = 'Bolivia';
  currency = 'BOB';
  adminName = '';
  adminEmail = '';
  selectedPlanId = 'plan_pro';
  billingCycle: 'monthly' | 'yearly' = 'monthly';

  // Simulated Payment
  cardNumber = '4242 4242 4242 4242';
  cardHolder = 'Titular de Prueba';
  cardExp = '12/28';
  cardCvv = '123';

  // Submission State
  readonly submitting = signal<boolean>(false);
  readonly completed = signal<boolean>(false);
  readonly createdInfo = signal<any>(null);

  ngOnInit(): void {
    this.route.queryParams.subscribe((params) => {
      if (params['plan']) {
        this.selectedPlanId = params['plan'];
      }
      if (params['cycle'] === 'yearly' || params['cycle'] === 'monthly') {
        this.billingCycle = params['cycle'];
      }
    });

    this.loadPlans();
  }

  async loadPlans(): Promise<void> {
    this.loadingPlans.set(true);
    try {
      const res = await firstValueFrom(this.subscriptionApi.getPlans());
      if (res.data) {
        this.plans.set(res.data);
      }
    } catch (err) {
      console.error('Error cargando planes:', err);
    } finally {
      this.loadingPlans.set(false);
    }
  }

  get selectedPlan(): SubscriptionPlan | undefined {
    return this.plans().find((p) => p.id === this.selectedPlanId);
  }

  get planPrice(): number {
    const plan = this.selectedPlan;
    if (!plan) return 0;
    return this.billingCycle === 'yearly' ? plan.price_yearly : plan.price_monthly;
  }

  onCompanyNameChange(): void {
    if (!this.slug || this.slug.trim() === '') {
      this.slug = this.companyName
        .toLowerCase()
        .trim()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_-]+/g, '-')
        .replace(/^-+|-+$/g, '');
    }
  }

  onCountryChange(): void {
    const found = this.countries.find((c) => c.name === this.country);
    if (found && found.currency) {
      this.currency = found.currency;
    }
  }

  useTestCard(): void {
    this.cardNumber = '4242 4242 4242 4242';
    this.cardHolder = this.adminName.trim() || 'Titular de Prueba';
    this.cardExp = '12/28';
    this.cardCvv = '123';
    toast.info('Datos de tarjeta simulada de prueba completados.');
  }

  async submitOrder(): Promise<void> {
    if (!this.companyName.trim()) {
      toast.warning('Ingresá el nombre de tu empresa.');
      return;
    }
    if (!this.adminName.trim()) {
      toast.warning('Ingresá el nombre del administrador.');
      return;
    }
    if (!this.adminEmail.trim()) {
      toast.warning('Ingresá el correo electrónico del administrador.');
      return;
    }
    if (!this.selectedPlanId) {
      toast.warning('Seleccioná un plan de suscripción.');
      return;
    }

    this.submitting.set(true);
    try {
      const payload = {
        company_name: this.companyName.trim(),
        slug: this.slug.trim() || undefined,
        country: this.country,
        currency: this.currency,
        admin_name: this.adminName.trim(),
        admin_email: this.adminEmail.trim().toLowerCase(),
        plan_id: this.selectedPlanId,
        billing_cycle: this.billingCycle,
        card_number: this.cardNumber.replace(/\s/g, ''),
        card_holder: this.cardHolder.trim(),
        card_exp: this.cardExp.trim(),
        card_cvv: this.cardCvv.trim(),
      };

      const res = await firstValueFrom(this.subscriptionApi.purchaseSimulated(payload));
      this.createdInfo.set(res.data);
      this.completed.set(true);
      toast.success(res.message || 'Suscripción activada con éxito.');
    } catch (err: any) {
      toast.error(getErrorMessage(err, 'No se pudo completar la suscripción.'));
    } finally {
      this.submitting.set(false);
    }
  }
}
