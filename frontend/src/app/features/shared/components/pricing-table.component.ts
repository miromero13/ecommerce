import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnInit, Output, inject, signal } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  lucideCheck,
  lucideX,
  lucideSparkles,
  lucideZap,
  lucideCrown,
  lucideCamera,
  lucideBrainCircuit,
  lucideStore,
} from '@ng-icons/lucide';
import { firstValueFrom } from 'rxjs';

import { HlmButtonImports } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmBadgeImports } from '../../../components/badge/src';
import { PLAN_FEATURES, PlanFeatureInfo, SubscriptionPlan } from '../models/subscription.model';
import { SubscriptionApiService } from '../services/subscription-api.service';

@Component({
  selector: 'app-pricing-table',
  standalone: true,
  imports: [
    CommonModule,
    NgIcon,
    ...HlmButtonImports,
    ...HlmCardImports,
    ...HlmBadgeImports,
  ],
  providers: [
    provideIcons({
      lucideCheck,
      lucideX,
      lucideSparkles,
      lucideZap,
      lucideCrown,
      lucideCamera,
      lucideBrainCircuit,
      lucideStore,
    }),
  ],
  templateUrl: './pricing-table.component.html',
})
export class PricingTableComponent implements OnInit {
  private readonly subscriptionApi = inject(SubscriptionApiService);

  @Input() set initialPlans(plans: SubscriptionPlan[]) {
    if (plans && plans.length > 0) {
      this.plans.set(plans);
      this.loading.set(false);
    }
  }

  /** Marks the company's current plan (subscription page). */
  @Input() currentPlanId: string | null = null;
  @Input() showComparison = true;

  readonly features = PLAN_FEATURES;

  @Output() selectPlan = new EventEmitter<{
    plan: SubscriptionPlan;
    billingCycle: 'monthly' | 'yearly';
  }>();

  readonly plans = signal<SubscriptionPlan[]>([]);
  readonly loading = signal<boolean>(true);
  readonly billingCycle = signal<'monthly' | 'yearly'>('monthly');

  ngOnInit(): void {
    if (this.plans().length === 0) {
      this.loadPlans();
    }
  }

  async loadPlans(): Promise<void> {
    this.loading.set(true);
    try {
      const res = await firstValueFrom(this.subscriptionApi.getPlans());
      if (res.data) {
        this.plans.set(res.data);
      }
    } catch (err) {
      console.error('Error cargando planes de suscripción:', err);
    } finally {
      this.loading.set(false);
    }
  }

  setBillingCycle(cycle: 'monthly' | 'yearly'): void {
    this.billingCycle.set(cycle);
  }

  onChoose(plan: SubscriptionPlan): void {
    this.selectPlan.emit({
      plan,
      billingCycle: this.billingCycle(),
    });
  }

  getPrice(plan: SubscriptionPlan): number {
    return this.billingCycle() === 'yearly' ? plan.price_yearly : plan.price_monthly;
  }

  /** Plans arrive ordered by price; each card lists only what it adds over the previous one. */
  previousPlan(index: number): SubscriptionPlan | null {
    return index > 0 ? this.plans()[index - 1] : null;
  }

  addedFeatures(plan: SubscriptionPlan, index: number): PlanFeatureInfo[] {
    const previous = new Set(this.previousPlan(index)?.features ?? []);
    return plan.features.filter((key) => !previous.has(key)).map((key) => this.featureInfo(key));
  }

  featureInfo(key: string): PlanFeatureInfo {
    return this.features.find((feature) => feature.key === key) ?? { key, label: key, description: '' };
  }

  hasFeature(plan: SubscriptionPlan, key: string): boolean {
    return plan.features.includes(key);
  }
}
