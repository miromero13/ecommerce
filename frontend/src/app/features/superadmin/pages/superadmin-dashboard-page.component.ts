import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  lucideActivity,
  lucideArrowRight,
  lucideBuilding2,
  lucideCheckCircle2,
  lucidePlus,
  lucideShieldAlert,
  lucideStore,
  lucideUsers,
} from '@ng-icons/lucide';

import { HlmButtonImports } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmTableImports } from '../../../components/table/src';
import { Tenant } from '../../shared/models/tenant.model';
import { TenantApiService } from '../../shared/services/tenant-api.service';

@Component({
  selector: 'app-superadmin-dashboard-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    NgIcon,
    ...HlmButtonImports,
    ...HlmCardImports,
    ...HlmBadgeImports,
    ...HlmTableImports,
  ],
  providers: [
    provideIcons({
      lucideBuilding2,
      lucideStore,
      lucideUsers,
      lucideActivity,
      lucideShieldAlert,
      lucidePlus,
      lucideArrowRight,
      lucideCheckCircle2,
    }),
  ],
  templateUrl: './superadmin-dashboard-page.component.html',
})
export class SuperadminDashboardPageComponent {
  private readonly tenantApi = inject(TenantApiService);

  protected readonly loading = signal<boolean>(false);
  protected readonly tenants = signal<Tenant[]>([]);

  protected readonly metrics = computed(() => {
    const list = this.tenants();
    const total = list.length;
    const active = list.filter((t) => t.status === 'active').length;
    const suspended = list.filter((t) => t.status === 'suspended').length;
    const totalBranches = list.reduce((sum, t) => sum + (t.branches_count || 0), 0);
    const totalUsers = list.reduce((sum, t) => sum + (t.users_count || 0), 0);

    return {
      total,
      active,
      suspended,
      totalBranches,
      totalUsers,
    };
  });

  protected readonly recentTenants = computed(() => {
    return this.tenants().slice(0, 5);
  });

  constructor() {
    void this.loadData();
  }

  protected async loadData(): Promise<void> {
    this.loading.set(true);
    try {
      const res = await firstValueFrom(this.tenantApi.listTenants({ limit: 100 }));
      this.tenants.set(res.data ?? []);
    } catch {
      this.tenants.set([]);
    } finally {
      this.loading.set(false);
    }
  }
}
