import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { CatalogGarmentResponse } from '../models/catalog.model';

const MAX_URL_LENGTH = 2048;

@Injectable({ providedIn: 'root' })
export class CatalogoPrendaService {
  private readonly api = inject(ApiService);
  private readonly cache = new Map<string, Promise<string>>();

  prepare(sourceUrl: string | null | undefined): Promise<string> {
    const normalizedUrl = sourceUrl?.trim() ?? '';
    if (!this.isValidSourceUrl(normalizedUrl)) {
      return Promise.reject(new Error('La imagen de la prenda no es válida.'));
    }

    const cached = this.cache.get(normalizedUrl);
    if (cached) return cached;

    const request = firstValueFrom(
      this.api.post<ApiResponse<CatalogGarmentResponse>>('/catalog/garment', { source_url: normalizedUrl }),
    )
      .then((response) => {
        const dataUrl = response.data?.image_data_url;
        if (!dataUrl || !/^data:image\/[\w.+-]+;base64,[A-Za-z0-9+/]+=*$/.test(dataUrl)) {
          throw new Error('El servidor no devolvió una imagen de prenda válida.');
        }
        return dataUrl;
      })
      .catch((error) => {
        this.cache.delete(normalizedUrl);
        if (error instanceof Error && error.message.startsWith('El servidor')) throw error;
        throw new Error(getErrorMessage(error, 'No se pudo preparar la prenda.'));
      });

    this.cache.set(normalizedUrl, request);
    return request;
  }

  private isValidSourceUrl(sourceUrl: string): boolean {
    if (!sourceUrl || sourceUrl.length > MAX_URL_LENGTH) return false;
    try {
      const url = new URL(sourceUrl);
      return (url.protocol === 'http:' || url.protocol === 'https:') && !url.username && !url.password;
    } catch {
      return false;
    }
  }
}
