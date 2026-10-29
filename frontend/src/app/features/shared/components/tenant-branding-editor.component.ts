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
        <p class="text-sm text-muted-foreground">Logo y color que ve tu personal en el panel y que se imprimen en comprobantes y notas de venta.</p>
      </div>
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div class="flex size-20 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-border bg-muted">
          @if (branding()?.logo_url) {
            <img [src]="branding()!.logo_url" alt="Logo de la empresa" class="size-full object-contain" />
          } @else {
            <span class="text-xs text-muted-foreground">Sin logo</span>
          }
        </div>
        <div class="flex flex-1 flex-col gap-3">
          <label class="inline-flex w-fit cursor-pointer items-center gap-2 text-sm font-medium text-foreground">
            <input type="file" class="hidden" accept="image/png,image/jpeg,image/webp" [disabled]="saving()" (change)="uploadLogo($event)" />
            <span class="rounded-lg border border-border px-3 py-2 hover:bg-muted">{{ branding()?.logo_url ? 'Cambiar logo' : 'Subir logo' }}</span>
            <span class="text-xs text-muted-foreground">PNG, JPG o WEBP · máx. 2 MB</span>
          </label>
          <div class="flex items-center gap-3">
            <input type="color" class="h-9 w-14 cursor-pointer rounded border border-border bg-transparent" [value]="color()" (input)="color.set($any($event.target).value)" aria-label="Color principal" />
            <span class="font-mono text-xs text-muted-foreground">{{ color() }}</span>
            <button hlmBtn type="button" variant="outline" [disabled]="saving()" (click)="saveColor()">Guardar color</button>
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

  protected async saveColor(): Promise<void> {
    const request = this.tenantId
      ? this.api.updateTenant(this.tenantId, { primary_color: this.color() })
      : this.api.updateMyBranding(this.color());
    await this.run(request as Observable<ApiResponse<unknown>>, 'No se pudo guardar el color.');
  }

  protected async uploadLogo(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (!file) return;
    // Same limits as the backend, checked first for immediate feedback.
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

  private async run(request: Observable<ApiResponse<unknown>>, fallback: string): Promise<void> {
    this.saving.set(true);
    try {
      const response = await firstValueFrom(request);
      toast.success(response.message);
      const id = this.tenantId ?? this.currentTenantId ?? this.branding()?.tenant_id;
      // Reload the public branding so the panel and receipts pick up the change.
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
    if (branding?.primary_color) this.color.set(branding.primary_color);
  }
}
