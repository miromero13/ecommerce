import { HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { map } from 'rxjs';
import { resolveAssetUrl } from '../utils/asset-url.util';

const IMAGE_KEYS = new Set(['image_url', 'try_on_image_url', 'garment_image_url', 'logo_url']);

function normalizeImageUrlsInObject(data: any): any {
  if (!data || typeof data !== 'object') {
    return data;
  }
  if (Array.isArray(data)) {
    return data.map((item) => normalizeImageUrlsInObject(item));
  }
  const copy: any = { ...data };
  for (const key of Object.keys(copy)) {
    const val = copy[key];
    if (typeof val === 'string' && IMAGE_KEYS.has(key)) {
      copy[key] = resolveAssetUrl(val);
    } else if (typeof val === 'object' && val !== null) {
      copy[key] = normalizeImageUrlsInObject(val);
    }
  }
  return copy;
}

export const assetUrlInterceptor: HttpInterceptorFn = (req, next) => {
  return next(req).pipe(
    map((event) => {
      if (event instanceof HttpResponse && event.body) {
        return event.clone({ body: normalizeImageUrlsInObject(event.body) });
      }
      return event;
    }),
  );
};
