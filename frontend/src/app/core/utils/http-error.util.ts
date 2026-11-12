import { HttpErrorResponse } from '@angular/common/http';

/**
 * El servidor no respondió: status 0 (sin red) o 504 "Gateway Timeout" que fabrica el service worker de Angular
 * (ngsw) cuando la red falla y no tiene copia de esa petición. Ambos significan "sin conexión", no un error del negocio.
 */
export function isNoResponse(error: unknown): boolean {
  return error instanceof HttpErrorResponse && (error.status === 0 || (error.status === 504 && error.statusText === 'Gateway Timeout'));
}

export function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof HttpErrorResponse) {
    const detail = error.error?.detail;
    if (typeof detail === 'string' && detail.trim().length > 0) {
      return detail;
    }
    const message = error.error?.message;
    if (typeof message === 'string' && message.trim().length > 0) {
      return message;
    }
  }
  return fallback;
}
