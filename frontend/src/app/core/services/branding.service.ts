import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { TenantBranding } from '../../features/shared/models/tenant.model';
import { TenantApiService } from '../../features/shared/services/tenant-api.service';
import type { PdfBrand } from '../utils/simple-pdf.util';

export const BRANDING_STORAGE_KEY = 'tenant_branding';
export const PRIMARY_COLOR_STORAGE_KEY = 'tenant_primary_color';

/**
 * Calculates high-contrast text color (white or dark slate) for a given HEX color.
 */
export function getContrastTextColor(hex: string): string {
  if (!hex || typeof hex !== 'string' || !hex.startsWith('#')) return '#ffffff';
  const clean = hex.replace('#', '');
  if (clean.length !== 6 && clean.length !== 3) return '#ffffff';
  const full = clean.length === 3 ? clean.split('').map((c) => c + c).join('') : clean;
  const r = parseInt(full.slice(0, 2), 16);
  const g = parseInt(full.slice(2, 4), 16);
  const b = parseInt(full.slice(4, 6), 16);
  const yiq = (r * 299 + g * 587 + b * 114) / 1000;
  return yiq >= 150 ? '#0f172a' : '#ffffff';
}

/**
 * CU1 company branding (logo, color, name). `current` is the signed-in staff member's
 * company; `forTenant` serves any company (e.g. the store of a customer's order).
 * Persists active company brand in localStorage and applies its primary color globally.
 */
@Injectable({ providedIn: 'root' })
export class BrandingService {
  private readonly api = inject(TenantApiService);
  private readonly cache = new Map<string, Promise<TenantBranding | null>>();
  readonly current = signal<TenantBranding | null>(null);

  constructor() {
    this.restoreFromStorage();
  }

  async loadCurrent(tenantId: string | null | undefined): Promise<void> {
    if (!tenantId) {
      this.current.set(null);
      this.clearStoredBranding();
      this.applyPrimaryColor(null);
      return;
    }

    const branding = await this.forTenant(tenantId);
    this.current.set(branding);
    if (branding) {
      this.storeBranding(branding);
      this.applyPrimaryColor(branding.primary_color);
    } else {
      this.clearStoredBranding();
      this.applyPrimaryColor(null);
    }
  }

  /** Call after the admin edits the branding so every view shows the new values. */
  refresh(branding: TenantBranding): void {
    this.cache.set(branding.tenant_id, Promise.resolve(branding));
    if (this.current()?.tenant_id === branding.tenant_id || !this.current()) {
      this.current.set(branding);
      this.storeBranding(branding);
      this.applyPrimaryColor(branding.primary_color);
    }
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

  /**
   * Applies the company's primary color dynamically to CSS variables across the entire application.
   */
  applyPrimaryColor(color: string | null | undefined): void {
    if (typeof document === 'undefined') return;
    const root = document.documentElement;
    if (!color) {
      root.style.removeProperty('--primary');
      root.style.removeProperty('--primary-foreground');
      root.style.removeProperty('--sidebar-primary');
      root.style.removeProperty('--sidebar-primary-foreground');
      root.style.removeProperty('--ring');
      return;
    }
    const foreground = getContrastTextColor(color);
    root.style.setProperty('--primary', color);
    root.style.setProperty('--primary-foreground', foreground);
    root.style.setProperty('--sidebar-primary', color);
    root.style.setProperty('--sidebar-primary-foreground', foreground);
    root.style.setProperty('--ring', color);
  }

  private restoreFromStorage(): void {
    if (typeof localStorage === 'undefined') return;
    try {
      const cachedColor = localStorage.getItem(PRIMARY_COLOR_STORAGE_KEY);
      if (cachedColor) {
        this.applyPrimaryColor(cachedColor);
      }
      const cachedBranding = localStorage.getItem(BRANDING_STORAGE_KEY);
      if (cachedBranding) {
        this.current.set(JSON.parse(cachedBranding) as TenantBranding);
      }
    } catch {
      // ignore storage errors
    }
  }

  private storeBranding(branding: TenantBranding): void {
    if (typeof localStorage === 'undefined') return;
    try {
      localStorage.setItem(BRANDING_STORAGE_KEY, JSON.stringify(branding));
      if (branding.primary_color) {
        localStorage.setItem(PRIMARY_COLOR_STORAGE_KEY, branding.primary_color);
      } else {
        localStorage.removeItem(PRIMARY_COLOR_STORAGE_KEY);
      }
    } catch {
      // storage quota or private mode
    }
  }

  private clearStoredBranding(): void {
    if (typeof localStorage === 'undefined') return;
    try {
      localStorage.removeItem(BRANDING_STORAGE_KEY);
      localStorage.removeItem(PRIMARY_COLOR_STORAGE_KEY);
    } catch {
      // ignore
    }
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
