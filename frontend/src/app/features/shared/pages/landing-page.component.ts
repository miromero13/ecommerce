import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  lucideArrowRight,
  lucideBot,
  lucideBoxes,
  lucideCamera,
  lucideCheckCircle2,
  lucideLayers,
  lucideShieldCheck,
  lucideSparkles,
  lucideStore,
  lucideWifiOff,
} from '@ng-icons/lucide';

import { HlmButtonImports } from '../../../components/button/src';
import { PricingTableComponent } from '../components/pricing-table.component';
import { SubscriptionPlan } from '../models/subscription.model';
import { SessionService } from '../services/session.service';

@Component({
  selector: 'app-landing-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    NgIcon,
    ...HlmButtonImports,
    PricingTableComponent,
  ],
  providers: [
    provideIcons({
      lucideArrowRight,
      lucideBot,
      lucideBoxes,
      lucideCamera,
      lucideCheckCircle2,
      lucideLayers,
      lucideShieldCheck,
      lucideSparkles,
      lucideStore,
      lucideWifiOff,
    }),
  ],
  templateUrl: './landing-page.component.html',
})
export class LandingPageComponent {
  private readonly router = inject(Router);
  protected readonly session = inject(SessionService);
  protected readonly isAuthenticated = this.session.isAuthenticated;

  onPlanSelected(event: { plan: SubscriptionPlan; billingCycle: 'monthly' | 'yearly' }): void {
    // Navigate to onboarding / checkout modal flow with selected plan
    this.router.navigate(['/onboarding'], {
      queryParams: {
        plan: event.plan.id,
        cycle: event.billingCycle,
      },
    });
  }

  scrollToSection(sectionId: string): void {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  scrollToTop(event?: Event): void {
    if (this.router.url === '/' || this.router.url.startsWith('/#') || this.router.url.startsWith('/?')) {
      event?.preventDefault();
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}
