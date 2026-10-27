import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { SessionService } from '../services/session.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const session = inject(SessionService);
  const router = inject(Router);

  const token = session.getToken();
  // Staff belong to one company (CU1); the backend rejects a mismatch with the JWT.
  const tenantId = session.user()?.tenant_id;
  const request = token
    ? req.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`,
          ...(tenantId ? { 'X-Tenant-ID': tenantId } : {}),
        },
      })
    : req;

  return next(request).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && session.getToken()) {
        session.clearSession();
        void router.navigate(['/auth/login']);
      }
      return throwError(() => error);
    }),
  );
};
