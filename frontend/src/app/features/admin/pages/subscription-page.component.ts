import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
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
import { SubscriptionSummary } from '../../shared/models/subscription.model';
import { SubscriptionApiService } from '../../shared/services/subscription-api.service';

@Component({
  selector: 'app-subscription-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    NgIcon,
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

  readonly summary = signal<SubscriptionSummary | null>(null);
  readonly loading = signal<boolean>(true);
  readonly error = signal<string | null>(null);

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
      }
    } catch (err: any) {
      this.error.set(err?.error?.message || 'No se pudo cargar la información de la suscripción.');
    } finally {
      this.loading.set(false);
    }
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
