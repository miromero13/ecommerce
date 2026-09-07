import { Routes } from '@angular/router';

import { AppShellComponent } from './core/layouts/app-shell.component';
import {
  authenticatedGuard,
  publicOnlyGuard,
  roleGuard,
} from './features/shared/guards/auth.guards';

export const routes: Routes = [
  {
    path: 'auth/login',
    loadComponent: () =>
      import('./features/shared/pages/login-page.component').then(
        (m) => m.LoginPageComponent,
      ),
    canActivate: [publicOnlyGuard],
  },
  {
    path: 'auth/register',
    loadComponent: () =>
      import('./features/shared/pages/register-page.component').then(
        (m) => m.RegisterPageComponent,
      ),
    canActivate: [publicOnlyGuard],
  },
  {
    path: 'app',
    component: AppShellComponent,
    canActivate: [authenticatedGuard],
    children: [
      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'perfil',
      },
      {
        path: 'perfil',
        loadComponent: () =>
          import('./features/shared/pages/profile-page.component').then(
            (m) => m.ProfilePageComponent,
          ),
      },
      {
        path: 'cliente',
        loadComponent: () =>
          import('./features/cliente/pages/catalog-page.component').then((m) => m.CatalogPageComponent),
      },
      {
        path: 'cliente/catalog',
        loadComponent: () =>
          import('./features/cliente/pages/catalog-page.component').then((m) => m.CatalogPageComponent),
      },
      {
        path: 'cliente/reservations',
        loadComponent: () =>
          import('./features/cliente/pages/reservations-page.component').then((m) => m.ReservationsPageComponent),
      },
      {
        path: 'cliente/cart',
        loadComponent: () =>
          import('./features/cliente/pages/cart-page.component').then((m) => m.CartPageComponent),
      },
      {
        path: 'proveedor',
        loadComponent: () =>
          import('./features/proveedor/pages/proveedor-home-page.component').then(
            (m) => m.ProveedorHomePageComponent,
          ),
      },
      {
        path: 'encargado',
        loadComponent: () =>
          import('./features/encargado/pages/encargado-home-page.component').then(
            (m) => m.EncargadoHomePageComponent,
          ),
      },
      {
        path: 'encargado/reservations',
        loadComponent: () =>
          import('./features/encargado/pages/reservations-page.component').then((m) => m.ReservationsPageComponent),
      },
      {
        path: 'cajero',
        loadComponent: () =>
          import('./features/cajero/pages/cajero-home-page.component').then((m) => m.CajeroHomePageComponent),
      },
      {
        path: 'cajero/sales',
        loadComponent: () =>
          import('./features/cajero/pages/sales-page.component').then((m) => m.SalesPageComponent),
      },
      {
        path: 'delivery',
        loadComponent: () =>
          import('./features/delivery/pages/delivery-home-page.component').then(
            (m) => m.DeliveryHomePageComponent,
          ),
      },
      {
        path: 'admin',
        canActivate: [roleGuard(['administrador'])],
        children: [
          {
            path: '',
            loadComponent: () =>
              import('./features/admin/pages/admin-home-page.component').then(
                (m) => m.AdminHomePageComponent,
              ),
          },
          {
            path: 'catalog',
            loadComponent: () =>
              import('./features/admin/pages/admin-catalog-page.component').then(
                (m) => m.AdminCatalogPageComponent,
              ),
          },
          {
            path: 'inventory',
            loadComponent: () =>
              import('./features/admin/pages/admin-inventory-page.component').then(
                (m) => m.AdminInventoryPageComponent,
              ),
          },
          {
            path: 'user',
            loadComponent: () =>
              import('./features/admin/pages/admin-user-page.component').then(
                (m) => m.AdminUserPageComponent,
              ),
          },
          {
            path: 'branch',
            loadComponent: () =>
              import('./features/admin/pages/admin-branch-page.component').then(
                (m) => m.AdminBranchPageComponent,
              ),
          },
          {
            path: 'provider',
            loadComponent: () =>
              import('./features/admin/pages/admin-provider-page.component').then(
                (m) => m.AdminProviderPageComponent,
              ),
          },
          {
            path: 'reports',
            loadComponent: () =>
              import('./features/admin/pages/admin-reports-page.component').then(
                (m) => m.AdminReportsPageComponent,
              ),
          },
        ],
      },
    ],
  },
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'app',
  },
  {
    path: '**',
    redirectTo: 'app',
  },
];
