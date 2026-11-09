import { CommonModule } from '@angular/common';
import { Component, Input, OnInit, inject, signal } from '@angular/core';
import { toast } from '@spartan-ng/brain/sonner';
import { Observable, firstValueFrom } from 'rxjs';

import { HlmButton } from '../../../components/button/src';
import { ApiResponse } from '../../../core/models/api.model';
import { BrandingService } from '../../../core/services/branding.service';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { TenantBranding } from '../models/tenant.model';
import { TenantApiService } from '../services/tenant-api.service';

const LOGO_TYPES = ['image/png', 'image/jpeg', 'image/webp'];
const LOGO_MAX_BYTES = 2 * 1024 * 1024;

/**
 * CU1 branding editor. Without `tenantId` the company admin edits its own company;
 * the superadmin passes the company id from tenant management.
 */
@Component({
  selector: 'app-tenant-branding-editor',
  standalone: true,
  imports: [CommonModule, HlmButton],
  template: `
    <section class="space-y-4 rounded-2xl border border-border bg-card p-5">
      <div>
        <h2 class="text-base font-bold text-foreground">Marca de la empresa</h2>
        <p class="text-xs sm:text-sm text-muted-foreground">Logo y color que ve tu personal en el panel y que se imprimen en comprobantes y notas de venta.</p>
      </div>

      <div class="flex flex-col gap-4 sm:flex-row sm:items-center">
        <!-- Logo Preview Box -->
        <div class="flex size-20 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-border bg-muted">
          @if (branding()?.logo_url) {
            <img [src]="branding()!.logo_url" alt="Logo de la empresa" class="size-full object-contain p-1" />
          } @else {
            <span class="text-xs text-muted-foreground">Sin logo</span>
          }
        </div>

        <div class="flex flex-1 flex-col gap-3">
          <!-- Logo Actions: Upload, Change and Remove -->
          <div class="flex flex-wrap items-center gap-2">
            <label class="inline-flex w-fit cursor-pointer items-center gap-2 text-xs font-medium text-foreground">
              <input type="file" class="hidden" accept="image/png,image/jpeg,image/webp" [disabled]="saving()" (change)="uploadLogo($event)" />
              <span class="rounded-lg border border-border px-3 py-1.5 hover:bg-muted font-semibold transition-colors cursor-pointer">
                {{ branding()?.logo_url ? 'Cambiar logo' : 'Subir logo' }}
              </span>
            </label>

            @if (branding()?.logo_url) {
              <button
                hlmBtn
                type="button"
                variant="outline"
                size="sm"
                class="text-xs text-destructive hover:bg-destructive/10 cursor-pointer"
                [disabled]="saving()"
                (click)="removeLogo()"
              >
                Dejar sin foto
              </button>
            }
            <span class="text-[11px] text-muted-foreground block w-full sm:w-auto">PNG, JPG o WEBP · máx. 2 MB</span>
          </div>

          <!-- Color Actions: Picker, Hex, Save and Reset to System Default -->
          <div class="flex flex-wrap items-center gap-2 pt-1 border-t border-border/50">
            <div class="flex items-center gap-2">
              <input
                type="color"
                class="size-8 cursor-pointer rounded-md border border-border bg-transparent p-0.5"
                [value]="color()"
                (input)="color.set($any($event.target).value)"
                aria-label="Color principal"
              />
              <span class="font-mono text-xs text-muted-foreground">{{ color() }}</span>
            </div>

            <button hlmBtn type="button" variant="default" size="sm" [disabled]="saving()" (click)="saveColor()" class="cursor-pointer">
              Guardar color
            </button>

            @if (branding()?.primary_color) {
              <button
                hlmBtn
                type="button"
                variant="ghost"
                size="sm"
                [disabled]="saving()"
                (click)="resetColor()"
                class="text-xs text-muted-foreground hover:text-foreground cursor-pointer"
              >
                Reestablecer al color del sistema
              </button>
            }
          </div>
        </div>
      </div>
    </section>
  `,
})
export class TenantBrandingEditorComponent implements OnInit {
  private readonly api = inject(TenantApiService);
  private readonly brandingService = inject(BrandingService);

  @Input() tenantId?: string;
  @Input() currentTenantId?: string | null;

  protected readonly branding = signal<TenantBranding | null>(null);
  protected readonly color = signal('#111827');
  protected readonly saving = signal(false);

  async ngOnInit(): Promise<void> {
    const id = this.tenantId ?? this.currentTenantId;
    if (!id) return;
    this.show(await this.brandingService.forTenant(id));
  }

  // [CU26 - Secuencia: Paso 1] El Administrador del tenant ejecuta saveColor() en TenantBrandingEditorComponent
  protected async saveColor(): Promise<void> {
    const request = this.tenantId
      ? this.api.updateTenant(this.tenantId, { primary_color: this.color() })
      : this.api.updateMyBranding(this.color());
    await this.run(request as Observable<ApiResponse<unknown>>, 'No se pudo guardar el color.');
  }

  // [CU26 - Secuencia: Paso 4] El Administrador del tenant ejecuta resetColor() en TenantBrandingEditorComponent
  protected async resetColor(): Promise<void> {
    const request = this.tenantId
      ? this.api.updateTenant(this.tenantId, { primary_color: null })
      : this.api.updateMyBranding(null);
    await this.run(request as Observable<ApiResponse<unknown>>, 'No se pudo reestablecer el color.');
  }

  // [CU26 - Secuencia: Paso 2] El Administrador del tenant ejecuta uploadLogo(event) en TenantBrandingEditorComponent
  protected async uploadLogo(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (!file) return;
    if (!LOGO_TYPES.includes(file.type)) {
      toast.error('El logo debe ser una imagen PNG, JPG o WEBP');
      return;
    }
    if (file.size > LOGO_MAX_BYTES) {
      toast.error('El logo no puede superar los 2 MB');
      return;
    }
    await this.run(this.api.uploadLogo(file, this.tenantId), 'No se pudo subir el logo.');
  }

  // [CU26 - Secuencia: Paso 3] El Administrador del tenant ejecuta removeLogo() en TenantBrandingEditorComponent
  protected async removeLogo(): Promise<void> {
    await this.run(this.api.deleteLogo(this.tenantId), 'No se pudo quitar el logo.');
  }

  private async run(request: Observable<ApiResponse<unknown>>, fallback: string): Promise<void> {
    this.saving.set(true);
    try {
      const response = await firstValueFrom(request);
      toast.success(response.message);
      const id = this.tenantId ?? this.currentTenantId ?? this.branding()?.tenant_id;
      if (id) {
        const fresh = await firstValueFrom(this.api.getBranding(id));
        if (fresh.data) {
          this.brandingService.refresh(fresh.data);
          this.show(fresh.data);
        }
      }
    } catch (error) {
      toast.error(getErrorMessage(error, fallback));
    } finally {
      this.saving.set(false);
    }
  }

  private show(branding: TenantBranding | null): void {
    this.branding.set(branding);
    this.color.set(branding?.primary_color || '#111827');
  }
}
