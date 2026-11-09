import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { SwUpdate, VersionReadyEvent } from '@angular/service-worker';
import { filter } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export interface PwaManifestData {
  name: string;
  short_name: string;
  start_url: string;
  display: string;
  background_color: string;
  theme_color: string;
  icons: Array<{ src: string; sizes: string; type: string; purpose?: string }>;
}

interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed';
    platform: string;
  }>;
  prompt(): Promise<void>;
}

@Injectable({
  providedIn: 'root'
})
export class PwaService {
  private readonly http = inject(HttpClient);
  private readonly swUpdate = inject(SwUpdate, { optional: true });

  private deferredPrompt: BeforeInstallPromptEvent | null = null;

  readonly canInstall = signal<boolean>(false);
  readonly showBanner = signal<boolean>(false);
  readonly showInstallGuide = signal<boolean>(false);
  readonly updateAvailable = signal<boolean>(false);
  readonly isInstalled = signal<boolean>(false);
  readonly manifestConfig = signal<PwaManifestData | null>(null);

  constructor() {
    this.checkIfInstalled();
    this.listenForInstallPrompt();
    this.listenForUpdates();
    this.loadDynamicManifest();
  }

  private checkIfInstalled(): void {
    if (typeof window !== 'undefined') {
      const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
        (window.navigator as unknown as { standalone?: boolean }).standalone === true;
      this.isInstalled.set(isStandalone);
      if (!isStandalone) {
        this.canInstall.set(true);
        this.showBanner.set(true);
      } else {
        this.canInstall.set(false);
        this.showBanner.set(false);
      }
    }
  }

  private listenForInstallPrompt(): void {
    if (typeof window === 'undefined') return;

    window.addEventListener('beforeinstallprompt', (e: Event) => {
      // Prevent the mini-infobar from appearing on mobile
      e.preventDefault();
      this.deferredPrompt = e as BeforeInstallPromptEvent;

      if (!this.isInstalled()) {
        this.canInstall.set(true);
        this.showBanner.set(true);
      }
    });

    window.addEventListener('appinstalled', () => {
      this.deferredPrompt = null;
      this.canInstall.set(false);
      this.showBanner.set(false);
      this.isInstalled.set(true);
    });
  }

  private listenForUpdates(): void {
    if (!this.swUpdate || !this.swUpdate.isEnabled) return;

    this.swUpdate.versionUpdates
      .pipe(filter((evt): evt is VersionReadyEvent => evt.type === 'VERSION_READY'))
      .subscribe(() => {
        this.updateAvailable.set(true);
      });
  }

  // [CU22 - Secuencia: Paso 1] El sistema dispara loadDynamicManifest() en PwaService (evento del navegador)
  loadDynamicManifest(): void {
    const apiUrl = environment.apiBaseUrl || '/api';
    this.http.get<{ statusCode: number; data: PwaManifestData }>(`${apiUrl}/pwa/manifest`).subscribe({
      next: (res) => {
        if (res?.data) {
          this.manifestConfig.set(res.data);
          this.applyThemeColor(res.data.theme_color);
        }
      },
      error: () => {
        // Fallback silently to static manifest
      }
    });
  }

  private applyThemeColor(color?: string): void {
    if (!color || typeof document === 'undefined') return;
    let meta = document.querySelector('meta[name="theme-color"]');
    if (!meta) {
      meta = document.createElement('meta');
      meta.setAttribute('name', 'theme-color');
      document.head.appendChild(meta);
    }
    meta.setAttribute('content', color);
  }

  // [CU22 - Secuencia: Paso 2.1] PwaInstallPromptComponent invoca promptInstall() en PwaService
  async promptInstall(): Promise<boolean> {
    if (this.deferredPrompt) {
      try {
        await this.deferredPrompt.prompt();
        const choice = await this.deferredPrompt.userChoice;
        if (choice.outcome === 'accepted') {
          this.canInstall.set(false);
          this.showBanner.set(false);
          this.deferredPrompt = null;
          return true;
        }
      } catch {
        // Fallback to guide
      }
    }
    // If native prompt is unavailable or was blocked by browser heuristic, show visual instructions
    this.showBanner.set(false);
    this.showInstallGuide.set(true);
    return false;
  }

  dismissInstall(): void {
    this.showBanner.set(false);
  }

  closeInstallGuide(): void {
    this.showInstallGuide.set(false);
  }

  // [CU22 - Secuencia: Paso 3.1] PwaUpdatePromptComponent invoca applyUpdate() en PwaService
  async applyUpdate(): Promise<void> {
    if (!this.swUpdate || !this.swUpdate.isEnabled) {
      if (typeof window !== 'undefined') {
        window.location.reload();
      }
      return;
    }
    try {
      await this.swUpdate.activateUpdate();
      window.location.reload();
    } catch {
      window.location.reload();
    }
  }
}
