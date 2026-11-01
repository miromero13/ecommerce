import { environment } from '../../../environments/environment';

/**
 * Resuelve la URL de la imagen del producto usando directamente environment.apiBaseUrl:
 * - Si es una URL externa (Cloudinary), la usa tal cual.
 * - Si es una ruta relativa guardada en la base de datos (ej. /demo-assets/catalog/...),
 *   le antepone la URL base del backend sin '/api'.
 */
export function resolveAssetUrl(url: string | null | undefined): string {
  if (!url) return '';
  const trimmed = url.trim();
  if (!trimmed) return '';

  // URL externa absoluta (Cloudinary, etc.)
  if (/^https?:\/\//i.test(trimmed)) {
    return trimmed;
  }

  // Toma la apiBaseUrl configurada y le quita el /api final
  const backendBase = environment.apiBaseUrl.replace(/\/api\/?$/, '');
  const path = trimmed.startsWith('/') ? trimmed : `/${trimmed}`;
  return `${backendBase}${path}`;
}
