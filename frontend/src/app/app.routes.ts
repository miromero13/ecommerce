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
    path: '',
    pathMatch: 'full',
    loadComponent: () =>
      import('./features/shared/pages/landing-page.component').then(
        (m) => m.LandingPageComponent,
      ),
  },
  {
    path: 'landing',
    redirectTo: '',
    pathMatch: 'full',
  },
  {
    path: 'planes',
    redirectTo: '',
    pathMatch: 'full',
  },
  {
    path: 'onboarding',
    loadComponent: () =>
      import('./features/shared/pages/onboarding-page.component').then(
        (m) => m.OnboardingPageComponent,
      ),
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
        path: 'notifications',
        loadComponent: () => import('./features/shared/pages/notification-page.component').then((m) => m.NotificationPageComponent),
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
        path: 'cliente/products/:productId',
        loadComponent: () =>
          import('./features/cliente/pages/product-detail-page.component').then((m) => m.ProductDetailPageComponent),
      },
      {
        path: 'cliente/my-reservations',
        canActivate: [roleGuard(['cliente'])],
        loadComponent: () =>
          import('./features/cliente/pages/my-reservations-page.component').then((m) => m.MyReservationsPageComponent),
      },
      {
        path: 'cliente/wishlist',
        canActivate: [roleGuard(['cliente'])],
        loadComponent: () => import('./features/cliente/pages/wishlist-page.component').then((m) => m.WishlistPageComponent),
      },
      {
        path: 'cliente/loyalty',
        canActivate: [roleGuard(['cliente'])],
        loadComponent: () => import('./features/cliente/pages/loyalty-page.component').then((m) => m.LoyaltyPageComponent),
      },
      {
        path: 'cliente/cart',
        loadComponent: () =>
          import('./features/cliente/pages/cart-page.component').then((m) => m.CartPageComponent),
      },
      {
        path: 'cliente/orders',
        canActivate: [roleGuard(['cliente'])],
        loadComponent: () => import('./features/cliente/pages/orders-page.component').then((m) => m.OrdersPageComponent),
      },
      {
        path: 'proveedor',
        loadComponent: () =>
          import('./features/proveedor/pages/proveedor-home-page.component').then(
            (m) => m.ProveedorHomePageComponent,
          ),
      },
      {
        path: 'proveedor/products',
        canActivate: [roleGuard(['proveedor'])],
        loadComponent: () => import('./features/proveedor/pages/provider-products-page.component').then((m) => m.ProviderProductsPageComponent),
      },
      {
        path: 'proveedor/rpa-ingest',
        canActivate: [roleGuard(['proveedor'])],
        loadComponent: () => import('./features/proveedor/pages/provider-rpa-ingest-page.component').then((m) => m.ProviderRpaIngestPageComponent),
      },
      {
        path: 'encargado/rpa-ingest',
        canActivate: [roleGuard(['encargado'])],
        loadComponent: () => import('./features/proveedor/pages/provider-rpa-ingest-page.component').then((m) => m.ProviderRpaIngestPageComponent),
      },
      {
        path: 'proveedor/replenishment',
        canActivate: [roleGuard(['proveedor'])],
        loadComponent: () => import('./features/shared/pages/replenishment-page.component').then((m) => m.ReplenishmentPageComponent),
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
        path: 'encargado/inventory',
        canActivate: [roleGuard(['encargado'])],
        loadComponent: () =>
          import('./features/admin/pages/admin-inventory-page.component').then((m) => m.AdminInventoryPageComponent),
      },
      {
        path: 'encargado/orders',
        canActivate: [roleGuard(['encargado'])],
        loadComponent: () => import('./features/encargado/pages/orders-page.component').then((m) => m.EncargadoOrdersPageComponent),
      },
      {
        path: 'encargado/promotions',
        canActivate: [roleGuard(['encargado'])],
        loadComponent: () => import('./features/shared/pages/promotions-page.component').then((m) => m.PromotionsPageComponent),
      },
      {
        path: 'encargado/replenishment',
        canActivate: [roleGuard(['encargado'])],
        loadComponent: () => import('./features/shared/pages/replenishment-page.component').then((m) => m.ReplenishmentPageComponent),
      },
      {
        path: 'encargado/providers',
        canActivate: [roleGuard(['encargado'])],
        loadComponent: () => import('./features/admin/pages/admin-provider-page.component').then((m) => m.AdminProviderPageComponent),
      },
      {
        path: 'encargado/provider/:providerId/products',
        canActivate: [roleGuard(['encargado'])],
        loadComponent: () => import('./features/proveedor/pages/provider-products-page.component').then((m) => m.ProviderProductsPageComponent),
      },
      {
        path: 'encargado/sales',
        canActivate: [roleGuard(['encargado'])],
        loadComponent: () => import('./features/shared/pages/sales-history-page.component').then((m) => m.SalesHistoryPageComponent),
      },
      {
        path: 'cajero',
        canActivate: [roleGuard(['cajero'])],
        loadComponent: () =>
          import('./features/cajero/pages/cajero-home-page.component').then((m) => m.CajeroHomePageComponent),
      },
      {
        path: 'cajero/receipts',
        canActivate: [roleGuard(['cajero'])],
        loadComponent: () => import('./features/shared/pages/receipts-page.component').then((m) => m.ReceiptsPageComponent),
      },
      {
        path: 'cajero/caja',
        canActivate: [roleGuard(['cajero'])],
        loadComponent: () =>
          import('./features/cajero/pages/caja-page.component').then((m) => m.CajaPageComponent),
      },
      {
        path: 'cajero/orders',
        canActivate: [roleGuard(['cajero'])],
        loadComponent: () => import('./features/encargado/pages/orders-page.component').then((m) => m.EncargadoOrdersPageComponent),
      },
      {
        path: 'cajero/sales',
        canActivate: [roleGuard(['cajero'])],
        loadComponent: () => import('./features/shared/pages/sales-history-page.component').then((m) => m.SalesHistoryPageComponent),
      },
      {
        path: 'delivery',
        loadComponent: () =>
          import('./features/delivery/pages/delivery-home-page.component').then(
            (m) => m.DeliveryHomePageComponent,
          ),
      },
      {
        path: 'superadmin',
        canActivate: [roleGuard(['superadministrador'])],
        children: [
          {
            path: '',
            pathMatch: 'full',
            redirectTo: 'dashboard',
          },
          {
            path: 'dashboard',
            loadComponent: () =>
              import('./features/superadmin/pages/superadmin-dashboard-page.component').then(
                (m) => m.SuperadminDashboardPageComponent,
              ),
          },
          {
            path: 'tenants',
            loadComponent: () =>
              import('./features/superadmin/pages/tenant-management-page.component').then(
                (m) => m.TenantManagementPageComponent,
              ),
          },
          {
            path: 'plans',
            loadComponent: () =>
              import('./features/superadmin/pages/plan-management-page.component').then(
                (m) => m.PlanManagementPageComponent,
              ),
          },
          {
            path: 'drivers',
            loadComponent: () =>
              import('./features/superadmin/pages/drivers-page.component').then((m) => m.DriversPageComponent),
          },
          {
            path: 'settlements',
            loadComponent: () =>
              import('./features/superadmin/pages/settlements-page.component').then((m) => m.SettlementsPageComponent),
          },
        ],
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
            path: 'promotions',
            loadComponent: () => import('./features/shared/pages/promotions-page.component').then((m) => m.PromotionsPageComponent),
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
            path: 'branch/:branchId',
            loadComponent: () =>
              import('./features/admin/pages/admin-branch-detail-page.component').then(
                (m) => m.AdminBranchDetailPageComponent,
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
            path: 'provider/:providerId/products',
            loadComponent: () => import('./features/proveedor/pages/provider-products-page.component').then((m) => m.ProviderProductsPageComponent),
          },
          {
            path: 'sales',
            loadComponent: () => import('./features/shared/pages/sales-history-page.component').then((m) => m.SalesHistoryPageComponent),
          },
          {
            path: 'reports',
            loadComponent: () => import('./features/admin/pages/admin-reports-page.component').then((m) => m.AdminReportsPageComponent),
          },
          {
            path: 'replenishment',
            loadComponent: () => import('./features/shared/pages/replenishment-page.component').then((m) => m.ReplenishmentPageComponent),
          },
          {
            path: 'rpa-ingest',
            loadComponent: () => import('./features/proveedor/pages/provider-rpa-ingest-page.component').then((m) => m.ProviderRpaIngestPageComponent),
          },
          {
            path: 'receipts',
            loadComponent: () => import('./features/shared/pages/receipts-page.component').then((m) => m.ReceiptsPageComponent),
          },
          {
            path: 'payouts',
            loadComponent: () => import('./features/admin/pages/admin-payouts-page.component').then((m) => m.AdminPayoutsPageComponent),
          },
          {
            path: 'subscription',
            loadComponent: () =>
              import('./features/admin/pages/subscription-page.component').then(
                (m) => m.SubscriptionPageComponent,
              ),
          },
          {
            path: 'roles',
            loadComponent: () =>
              import('./features/admin/pages/rbac-roles-page.component').then(
                (m) => m.RbacRolesPageComponent,
              ),
          },
          {
            path: 'expert-replenishment',
            loadComponent: () =>
              import(
                './features/admin/pages/admin-expert-replenishment-page.component'
              ).then((m) => m.AdminExpertReplenishmentPageComponent),
          },
        ],
      },
    ],
  },
  {
    path: 'notifications',
    redirectTo: 'app/notifications',
  },
  {
    path: '**',
    redirectTo: '',
  },
];
