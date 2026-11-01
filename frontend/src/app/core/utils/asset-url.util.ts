import { environment } from '../../../environments/environment';

/**
 * Resolves an asset or garment image URL:
 * - If it's a Cloudinary or external URL (https://res.cloudinary.com/...), keeps it.
 * - If it mistakenly contains localhost:8000, rewrites it to the current backend origin.
 * - If it's a relative path (e.g. /catalog/..., /demo-assets/...), prepends the current backend origin (local or prod).
 */
export function resolveAssetUrl(url: string | null | undefined): string {
  if (!url) return '';
  const trimmed = url.trim();
  if (!trimmed) return '';

  // Get active backend host (stripping /api)
  const backendOrigin = environment.apiBaseUrl.replace(/\/api\/?$/, '');

  // If it's already an absolute URL
  if (/^https?:\/\//i.test(trimmed)) {
    // If it contains localhost:8000, replace with current backend origin
    if (trimmed.includes('localhost:8000')) {
      return trimmed.replace(/^https?:\/\/localhost:8000/, backendOrigin);
    }
    return trimmed;
  }

  // Relative path: ensure single leading slash
  const path = trimmed.startsWith('/') ? trimmed : `/${trimmed}`;
  if (path.startsWith('/catalog/') || path.startsWith('/try-on/')) {
    return `${backendOrigin}/demo-assets${path}`;
  }
  return `${backendOrigin}${path}`;
}
