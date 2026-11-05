import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideRefreshCw } from '@ng-icons/lucide';
import { PwaService } from '../../../core/services/pwa.service';

@Component({
  selector: 'app-pwa-update-prompt',
  standalone: true,
  imports: [CommonModule, NgIcon],
  providers: [provideIcons({ lucideRefreshCw })],
  template: `
    @if (pwaService.updateAvailable()) {
      <aside
        class="fixed top-4 left-1/2 -translate-x-1/2 z-50 w-11/12 max-w-lg bg-emerald-600 text-white rounded-xl shadow-2xl px-4 py-3 flex items-center justify-between gap-3 animate-in fade-in slide-in-from-top-4"
        aria-label="Aviso de actualización disponible"
      >
        <div class="flex items-center gap-2.5 min-w-0">
          <ng-icon name="lucideRefreshCw" class="text-lg shrink-0 animate-spin" />
          <p class="text-xs sm:text-sm font-medium truncate">
            Hay una nueva versión disponible de la plataforma. Hacé clic para actualizar.
          </p>
        </div>

        <button
          type="button"
          (click)="update()"
          class="shrink-0 px-3 py-1 text-xs font-bold rounded-lg bg-white text-emerald-900 hover:bg-emerald-50 transition-colors shadow-sm"
        >
          Actualizar ahora
        </button>
      </aside>
    }
  `
})
export class PwaUpdatePromptComponent {
  readonly pwaService = inject(PwaService);

  update(): void {
    this.pwaService.applyUpdate();
  }
}
