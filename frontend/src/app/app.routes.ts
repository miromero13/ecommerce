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
