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
          import('./features/cliente/pages/cliente-home-page.component').then((m) => m.ClienteHomePageComponent),
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
        path: 'cajero',
        loadComponent: () =>
          import('./features/cajero/pages/cajero-home-page.component').then((m) => m.CajeroHomePageComponent),
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
