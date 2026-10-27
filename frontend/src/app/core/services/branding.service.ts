import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { TenantBranding } from '../../features/shared/models/tenant.model';
import { TenantApiService } from '../../features/shared/services/tenant-api.service';
import type { PdfBrand } from '../utils/simple-pdf.util';

/**
 * CU1 company branding (logo, color, name). `current` is the signed-in staff member's
 * company; `forTenant` serves any company (e.g. the store of a customer's order).
 */
@Injectable({ providedIn: 'root' })
export class BrandingService {
  private readonly api = inject(TenantApiService);
  private readonly cache = new Map<string, Promise<TenantBranding | null>>();
  readonly current = signal<TenantBranding | null>(null);

  async loadCurrent(tenantId: string | null | undefined): Promise<void> {
    this.current.set(tenantId ? await this.forTenant(tenantId) : null);
  }

  /** Call after the admin edits the branding so every view shows the new values. */
  refresh(branding: TenantBranding): void {
    this.cache.set(branding.tenant_id, Promise.resolve(branding));
    if (this.current()?.tenant_id === branding.tenant_id) this.current.set(branding);
  }

  forTenant(tenantId: string): Promise<TenantBranding | null> {
    if (!this.cache.has(tenantId)) {
      this.cache.set(tenantId, firstValueFrom(this.api.getBranding(tenantId)).then(
        (response) => response.data ?? null,
        () => null, // receipts and the panel still work without branding
      ));
    }
    return this.cache.get(tenantId)!;
  }

  /** Branding ready for jsPDF: the logo is embedded as a data URL. */
  async pdfBrand(tenantId: string | null | undefined): Promise<PdfBrand | undefined> {
    const branding = tenantId ? await this.forTenant(tenantId) : null;
    if (!branding) return undefined;
    return { name: branding.name, color: branding.primary_color, logoDataUrl: await this.toDataUrl(branding.logo_url) };
  }

  private async toDataUrl(url: string | null): Promise<string | null> {
    if (!url) return null;
    try {
      // Cloudinary converts on delivery; jsPDF embeds PNG reliably (not WEBP).
      const png = url.includes('/upload/') ? url.replace('/upload/', '/upload/f_png/') : url;
      const blob = await (await fetch(png)).blob();
      return await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result));
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(blob);
      });
    } catch {
      return null; // a missing or blocked logo never prevents downloading the receipt
    }
  }
}
