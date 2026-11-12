import { HttpErrorResponse, HttpEvent, HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Observable, catchError, from, of, switchMap, tap, throwError } from 'rxjs';

import { IndexedDbService, STORES } from '../services/indexeddb.service';

interface CachedResponse {
  key: string;
  body: unknown;
  saved_at: string;
}

/** Catálogo público de lectura (productos, categorías, tallas, colores, temporadas, colecciones, sucursales y empresas públicas). */
function isCatalogRead(url: string): boolean {
  const path = url.split('?')[0];
  return /\/catalog\/(products|categories|sizes|colors|seasons|collections)(\/[^/]+)?$/.test(path) || path.endsWith('/branches/public') || path.endsWith('/saas/tenants/public');
}

/**
 * CU23 (cliente): guarda en IndexedDB la última respuesta con conexión del catálogo y la devuelve cuando el servidor
 * no responde (status 0: sin internet, Wi-Fi sin salida o servidor caído), para que el catálogo se vuelva a mostrar
 * al navegar al carrito y regresar sin conexión. Con una respuesta real del servidor (aunque sea un error) no interviene.
 */
export const catalogCacheInterceptor: HttpInterceptorFn = (req, next) => {
  if (req.method !== 'GET' || !isCatalogRead(req.urlWithParams)) return next(req);
  const idb = inject(IndexedDbService);
  const key = req.urlWithParams;
  const fromCache = (error: unknown): Observable<HttpEvent<unknown>> =>
    // Si la base local no responde en 3 s se devuelve el error original en vez de dejar el catálogo cargando para siempre.
    from(Promise.race([idb.getItem<CachedResponse>(STORES.HTTP_CACHE, key), new Promise<null>((r) => setTimeout(() => r(null), 3000))]).catch(() => null)).pipe(
      switchMap((cached) => (cached ? of(new HttpResponse({ status: 200, body: cached.body })) : throwError(() => error))),
    );

  return next(req).pipe(
    tap((event) => {
      if (event instanceof HttpResponse && event.status === 200) {
        void idb.putItem<CachedResponse>(STORES.HTTP_CACHE, { key, body: event.body, saved_at: new Date().toISOString() }).catch(() => {});
      }
    }),
    catchError((error: unknown) => (error instanceof HttpErrorResponse && error.status === 0 ? fromCache(error) : throwError(() => error))),
  );
};
