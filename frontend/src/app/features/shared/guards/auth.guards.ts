import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { RolUsuario } from '../models/auth.model';
import { SessionService } from '../services/session.service';
import { getDefaultRouteForRole } from '../../../core/utils/role-route.util';

export const authenticatedGuard: CanActivateFn = () => {
  const session = inject(SessionService);
  const router = inject(Router);

  if (session.getToken()) {
    return true;
  }

  return router.createUrlTree(['/auth/login']);
};

export const publicOnlyGuard: CanActivateFn = () => {
  const session = inject(SessionService);
  const router = inject(Router);

  if (session.getToken()) {
    return router.createUrlTree([getDefaultRouteForRole(session.user()?.rol)]);
  }

  return true;
};

export function roleGuard(roles: RolUsuario[]): CanActivateFn {
  return () => {
    const session = inject(SessionService);
    const router = inject(Router);
    const user = session.user();

    if (!user) {
      return router.createUrlTree(['/auth/login']);
    }

    if (!roles.includes(user.rol)) {
      return router.createUrlTree([getDefaultRouteForRole(user.rol)]);
    }

    return true;
  };
}
