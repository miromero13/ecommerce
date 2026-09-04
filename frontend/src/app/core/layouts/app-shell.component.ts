import { CommonModule } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideLayoutDashboard, lucideLogOut, lucideUserRound, lucideUsers } from '@ng-icons/lucide';

import {
  HlmSidebar,
  HlmSidebarContent,
  HlmSidebarFooter,
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
    HlmSidebarFooter,
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
      lucideLogOut,
      lucideUserRound,
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
      case 'proveedor':
        return 'Proveedor';
      case 'encargado':
        return 'Encargado';
      case 'cajero':
        return 'Cajero';
      case 'delivery':
        return 'Delivery';
      default:
        return 'Sin sesión';
    }
  });

  protected readonly userBranchLabel = computed(() => {
    const branchId = this.session.user()?.branch_id;
    return branchId ? `Sucursal ${branchId.slice(0, 8)}` : 'Sin sucursal';
  });

  protected readonly homeItem = computed(() => {
    switch (this.userRole()) {
      case 'administrador':
        return { label: 'Dashboard', route: '/app/admin', icon: 'lucideLayoutDashboard', exact: true };
      case 'cliente':
        return { label: 'Inicio', route: '/app/cliente', icon: 'lucideUserRound', exact: true };
      case 'proveedor':
        return { label: 'Inicio', route: '/app/proveedor', icon: 'lucideUserRound', exact: true };
      case 'encargado':
        return { label: 'Inicio', route: '/app/encargado', icon: 'lucideUserRound', exact: true };
      case 'cajero':
        return { label: 'Inicio', route: '/app/cajero', icon: 'lucideUserRound', exact: true };
      case 'delivery':
        return { label: 'Inicio', route: '/app/delivery', icon: 'lucideUserRound', exact: true };
      default:
        return { label: 'Inicio', route: '/app/perfil', icon: 'lucideUserRound', exact: true };
    }
  });

  protected readonly profileItem = {
    label: 'Mi perfil',
    route: '/app/perfil',
    icon: 'lucideUserRound',
    exact: true,
  };

  protected readonly sidebarSections = computed<SidebarSection[]>(() => {
    switch (this.userRole()) {
      case 'administrador':
        return [
          {
            title: 'Administración',
            items: [
              { label: 'Dashboard', route: '/app/admin', icon: 'lucideLayoutDashboard', exact: true },
              { label: 'Catálogo', route: '/app/admin/catalog', icon: 'lucideLayoutDashboard' },
              { label: 'Usuarios', route: '/app/admin/user', icon: 'lucideUsers' },
              { label: 'Sucursales', route: '/app/admin/branch', icon: 'lucideLayoutDashboard' },
              { label: 'Proveedores', route: '/app/admin/provider', icon: 'lucideUsers' },
            ],
          },
        ];
      case 'cliente':
        return [
          {
            title: 'Navegación',
            items: [
              { label: 'Catálogo', route: '/app/cliente/catalog', icon: 'lucideLayoutDashboard', exact: true },
            ],
          },
        ];
      default:
        return [
          {
            title: 'Navegación',
            items: [this.homeItem()],
          },
        ];
    }
  });

  protected async logout(): Promise<void> {
    await this.session.logout(true);
  }
}
