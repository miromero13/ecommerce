import { CommonModule } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideLayoutDashboard, lucideUser, lucideUsers } from '@ng-icons/lucide';

import {
  HlmSidebar,
  HlmSidebarContent,
  HlmSidebarHeader,
  HlmSidebarInset,
  HlmSidebarMenu,
  HlmSidebarMenuButton,
  HlmSidebarMenuItem,
  HlmSidebarTrigger,
  HlmSidebarWrapper,
} from '../../components/sidebar/src';
import { SessionService } from '../../features/shared/services/session.service';

type SidebarItem = {
  label: string;
  route: string;
  icon: string;
  exact?: boolean;
};

type SidebarSection = {
  title?: string;
  items: SidebarItem[];
};

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    RouterLinkActive,
    RouterOutlet,
    NgIcon,
    HlmSidebar,
    HlmSidebarContent,
    HlmSidebarHeader,
    HlmSidebarInset,
    HlmSidebarMenu,
    HlmSidebarMenuButton,
    HlmSidebarMenuItem,
    HlmSidebarTrigger,
    HlmSidebarWrapper,
  ],
  providers: [
    provideIcons({
      lucideLayoutDashboard,
      lucideUser,
      lucideUsers,
    }),
  ],
  templateUrl: './app-shell.component.html',
})
export class AppShellComponent {
  private readonly session = inject(SessionService);

  protected readonly fullName = computed(() => {
    const user = this.session.user();
    return user ? user.name : 'Sin sesión';
  });

  protected readonly userRole = computed(() => this.session.user()?.rol ?? '-');

  protected readonly userRoleLabel = computed(() => {
    switch (this.userRole()) {
      case 'administrador':
        return 'Administrador';
      case 'cliente':
        return 'Cliente';
      case 'delivery':
        return 'Delivery';
      default:
        return 'Sin sesión';
    }
  });

  protected readonly sidebarSections = computed<SidebarSection[]>(() => {
    const shared: SidebarSection = {
      items: [{ label: 'Mi perfil', route: '/app/perfil', icon: 'lucideUser', exact: true }],
    };

    switch (this.userRole()) {
      case 'administrador':
        return [
          shared,
          {
            title: 'Administración',
            items: [
              { label: 'Dashboard', route: '/app/admin', icon: 'lucideLayoutDashboard', exact: true },
              { label: 'Usuarios', route: '/app/admin/user', icon: 'lucideUsers' },
            ],
          },
        ];
      default:
        return [shared];
    }
  });

  protected async logout(): Promise<void> {
    await this.session.logout(true);
  }
}
