import { Component, OnDestroy, effect, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideCheck, lucideDownload, lucideMonitor, lucideSmartphone, lucideX } from '@ng-icons/lucide';
import { PwaService } from '../../../core/services/pwa.service';

@Component({
  selector: 'app-pwa-install-prompt',
  standalone: true,
  imports: [CommonModule, NgIcon],
  providers: [provideIcons({ lucideCheck, lucideDownload, lucideMonitor, lucideSmartphone, lucideX })],
  template: `
    <!-- Banner flotante auto-cerrable a los 5 segundos -->
    @if (pwaService.showBanner()) {
      <aside
        (mouseenter)="pauseTimer()"
        (mouseleave)="resumeTimer()"
        class="fixed bottom-4 left-4 right-4 sm:left-auto sm:right-6 sm:max-w-md z-50 bg-white/95 dark:bg-zinc-900/95 backdrop-blur-md border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-2xl p-4 transition-all duration-300 animate-in fade-in slide-in-from-bottom-4 overflow-hidden"
        aria-label="Aviso de instalación de la aplicación"
      >
        <div class="flex items-start gap-3">
          <div class="h-10 w-10 shrink-0 rounded-xl bg-primary/10 text-primary flex items-center justify-center font-bold">
            <ng-icon name="lucideSmartphone" class="text-xl" />
          </div>

          <div class="flex-1 min-w-0">
            <h4 class="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
              Instalar FashionStore
            </h4>
            <p class="text-xs text-zinc-600 dark:text-zinc-400 mt-0.5 leading-relaxed">
              Instalá nuestra app en tu dispositivo para un acceso rápido y directo.
            </p>

            <div class="flex items-center gap-2 mt-3">
              <button
                type="button"
                (click)="install()"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-zinc-900 text-white hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200 transition-colors shadow-sm cursor-pointer"
              >
                <ng-icon name="lucideDownload" class="text-xs" />
                Instalar app
              </button>
              <button
                type="button"
                (click)="dismiss()"
                class="px-2.5 py-1.5 text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors cursor-pointer"
              >
                Cerrar
              </button>
            </div>
          </div>

          <button
            type="button"
            (click)="dismiss()"
            class="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 p-1 rounded-md transition-colors cursor-pointer"
            title="Cerrar"
          >
            <ng-icon name="lucideX" class="text-sm" />
          </button>
        </div>

        <!-- Barra animada de 5 segundos que va achicándose -->
        <div class="absolute bottom-0 left-0 right-0 h-1 bg-zinc-100 dark:bg-zinc-800">
          <div class="h-full bg-primary/80 animate-shrink-bar"></div>
        </div>
      </aside>
    }

    <!-- Modal con guía de instalación si el navegador no soporta el prompt nativo directo -->
    @if (pwaService.showInstallGuide()) {
      <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in">
        <div class="relative w-full max-w-md bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl shadow-2xl p-6 overflow-hidden">
          <div class="flex items-start justify-between gap-3">
            <div class="flex items-center gap-3">
              <div class="h-11 w-11 rounded-2xl bg-primary/10 text-primary flex items-center justify-center">
                <ng-icon name="lucideMonitor" class="text-2xl" />
              </div>
              <div>
                <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100">
                  Instalar en tu dispositivo
                </h3>
                <p class="text-xs text-zinc-500 dark:text-zinc-400">
                  FashionStore PWA
                </p>
              </div>
            </div>

            <button
              type="button"
              (click)="pwaService.closeInstallGuide()"
              class="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 p-1.5 rounded-lg transition-colors cursor-pointer"
            >
              <ng-icon name="lucideX" class="text-base" />
            </button>
          </div>

          <div class="mt-5 space-y-3.5 text-xs text-zinc-700 dark:text-zinc-300">
            <div class="p-3 rounded-xl bg-zinc-50 dark:bg-zinc-800/60 border border-zinc-100 dark:border-zinc-800">
              <span class="font-semibold text-zinc-900 dark:text-zinc-100 block mb-1">
                💻 En Chrome o Edge (Computadora):
              </span>
              Hacé clic en el ícono de instalación (monitor o símbolo ⊕) ubicado en la parte derecha de la barra de direcciones de tu navegador, o abrí el menú (⋮) y elegí <strong>"Instalar FashionStore"</strong>.
            </div>

            <div class="p-3 rounded-xl bg-zinc-50 dark:bg-zinc-800/60 border border-zinc-100 dark:border-zinc-800">
              <span class="font-semibold text-zinc-900 dark:text-zinc-100 block mb-1">
                📱 En Celulares Android (Chrome):
              </span>
              Tocá el menú de tres puntos (⋮) en la esquina superior derecha y seleccioná <strong>"Instalar aplicación"</strong> o <strong>"Agregar a la pantalla principal"</strong>.
            </div>

            <div class="p-3 rounded-xl bg-zinc-50 dark:bg-zinc-800/60 border border-zinc-100 dark:border-zinc-800">
              <span class="font-semibold text-zinc-900 dark:text-zinc-100 block mb-1">
                🍏 En iPhone / iPad (Safari):
              </span>
              Tocá el botón <strong>"Compartir"</strong> (cuadrado con flecha hacia arriba) en la barra inferior y elegí <strong>"Agregar a pantalla de inicio"</strong>.
            </div>
          </div>

          <div class="mt-6 flex justify-end">
            <button
              type="button"
              (click)="pwaService.closeInstallGuide()"
              class="px-4 py-2 text-xs font-semibold rounded-xl bg-zinc-900 text-white hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200 transition-colors shadow-sm cursor-pointer"
            >
              Entendido
            </button>
          </div>
        </div>
      </div>
    }
  `,
  styles: [`
    @keyframes shrink {
      from { width: 100%; }
      to { width: 0%; }
    }
    .animate-shrink-bar {
      animation: shrink 5s linear forwards;
    }
  `]
})
export class PwaInstallPromptComponent implements OnDestroy {
  readonly pwaService = inject(PwaService);
  private autoCloseTimer: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    effect(() => {
      if (this.pwaService.showBanner()) {
        this.startAutoCloseTimer();
      } else {
        this.clearTimer();
      }
    });
  }

  private startAutoCloseTimer(): void {
    this.clearTimer();
    this.autoCloseTimer = setTimeout(() => {
      this.pwaService.dismissInstall();
    }, 5000);
  }

  pauseTimer(): void {
    this.clearTimer();
  }

  resumeTimer(): void {
    this.startAutoCloseTimer();
  }

  private clearTimer(): void {
    if (this.autoCloseTimer) {
      clearTimeout(this.autoCloseTimer);
      this.autoCloseTimer = null;
    }
  }

  // [CU22 - Secuencia: Paso 2] El Cliente ejecuta install() en PwaInstallPromptComponent
  install(): void {
    this.clearTimer();
    this.pwaService.promptInstall();
  }

  dismiss(): void {
    this.clearTimer();
    this.pwaService.dismissInstall();
  }

  ngOnDestroy(): void {
    this.clearTimer();
  }
}
