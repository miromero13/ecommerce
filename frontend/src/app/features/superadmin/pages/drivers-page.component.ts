import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { toast } from '@spartan-ng/brain/sonner';
import { firstValueFrom } from 'rxjs';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucidePlus, lucideUserPlus, lucideUsers, lucideX } from '@ng-icons/lucide';

import { HlmButton } from '../../../components/button/src';
import { HlmInput } from '../../../components/input/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { UsuarioAuth } from '../../shared/models/auth.model';
import { DeliveryApiService } from '../../shared/services/delivery-api.service';

// CU20: drivers belong to the platform and deliver for every company.
@Component({
  selector: 'app-drivers-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, NgIcon, HlmButton, HlmInput],
  providers: [
    provideIcons({
      lucidePlus,
      lucideUserPlus,
      lucideUsers,
      lucideX,
    }),
  ],
  template: `
    <section class="space-y-6 text-slate-700 max-w-5xl mx-auto px-4 py-6">
      <header class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 class="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <ng-icon name="lucideUsers" class="w-6 h-6 text-primary"></ng-icon>
            Repartidores de la plataforma
          </h1>
          <p class="text-sm text-slate-500 mt-1">
            Los repartidores son globales a la plataforma: toman pedidos listos para despacho de todas las empresas.
          </p>
        </div>

        <button
          hlmBtn
          class="gap-1.5 shrink-0 bg-primary text-primary-foreground shadow hover:bg-primary/90"
          (click)="openModal()"
        >
          <ng-icon name="lucidePlus" class="w-4 h-4"></ng-icon>
          Nuevo Repartidor
        </button>
      </header>

      <!-- Tabla de repartidores -->
      <div class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div class="px-5 py-3.5 bg-slate-50 border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500 flex justify-between">
          <span>Repartidor</span>
          <span>Estado</span>
        </div>
        @for (driver of drivers(); track driver.id) {
          <div class="flex items-center justify-between border-b border-slate-100 px-5 py-3.5 text-sm last:border-0 hover:bg-slate-50/50 transition-colors">
            <div>
              <p class="font-semibold text-slate-900">{{ driver.name }}</p>
              <p class="text-xs text-slate-500">{{ driver.email }}</p>
            </div>
            <span
              class="rounded-full px-2.5 py-1 text-xs font-medium"
              [class]="driver.is_active ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-500 border border-slate-200'"
            >
              {{ driver.is_active ? 'Activo' : 'Inactivo' }}
            </span>
          </div>
        } @empty {
          <div class="p-8 text-center text-sm text-slate-500">
            Aún no hay repartidores registrados en la plataforma. Hacé clic en "Nuevo Repartidor" para dar de alta uno.
          </div>
        }
      </div>

      <!-- MODAL FLOTANTE DE ALTA DE REPARTIDOR -->
      <div
        *ngIf="showModal()"
        class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto"
      >
        <div class="bg-white w-full max-w-lg rounded-xl shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in-50 zoom-in-95 my-8">
          <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
            <h2 class="text-base font-bold text-slate-900 flex items-center gap-2">
              <ng-icon name="lucideUserPlus" class="w-5 h-5 text-primary"></ng-icon>
              Registrar Nuevo Repartidor
            </h2>
            <button
              class="text-slate-400 hover:text-slate-600 p-1 rounded-md"
              (click)="closeModal()"
            >
              <ng-icon name="lucideX" class="w-5 h-5"></ng-icon>
            </button>
          </div>

          <form class="p-6 space-y-4" [formGroup]="form" (ngSubmit)="create()">
            <div>
              <label class="block text-xs font-medium text-slate-700 mb-1">Nombre Completo</label>
              <input hlmInput placeholder="Ej. Carlos Mendoza" formControlName="name" class="w-full" />
            </div>

            <div>
              <label class="block text-xs font-medium text-slate-700 mb-1">Correo Electrónico</label>
              <input hlmInput placeholder="repartidor@delivery.demo.bo" type="email" formControlName="email" class="w-full" />
            </div>

            <div>
              <label class="block text-xs font-medium text-slate-700 mb-1">Contraseña (mínimo 8 caracteres)</label>
              <input hlmInput placeholder="••••••••" type="password" formControlName="password" class="w-full" />
            </div>

            <div>
              <label class="block text-xs font-medium text-slate-700 mb-1">Género</label>
              <select
                class="w-full h-9 rounded-md border border-slate-300 bg-white px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                formControlName="gender"
              >
                <option value="masculino">Masculino</option>
                <option value="femenino">Femenino</option>
              </select>
            </div>

            <div class="pt-4 border-t border-slate-100 flex items-center justify-end gap-2">
              <button hlmBtn variant="outline" type="button" (click)="closeModal()">
                Cancelar
              </button>
              <button hlmBtn type="submit" [disabled]="form.invalid || saving()">
                {{ saving() ? 'Registrando...' : 'Registrar Repartidor' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </section>
  `,
})
export class DriversPageComponent {
  private readonly api = inject(DeliveryApiService);
  private readonly fb = inject(FormBuilder);
  protected readonly drivers = signal<UsuarioAuth[]>([]);
  protected readonly saving = signal(false);
  protected readonly showModal = signal(false);

  protected readonly form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
    gender: ['masculino' as 'masculino' | 'femenino', [Validators.required]],
  });

  constructor() {
    void this.load();
  }

  protected openModal(): void {
    this.form.reset({ name: '', email: '', password: '', gender: 'masculino' });
    this.showModal.set(true);
  }

  protected closeModal(): void {
    this.showModal.set(false);
  }

  private async load(): Promise<void> {
    try {
      this.drivers.set((await firstValueFrom(this.api.drivers())).data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar los repartidores.'));
    }
  }

  protected async create(): Promise<void> {
    if (this.form.invalid) return;

    this.saving.set(true);
    try {
      toast.success((await firstValueFrom(this.api.createDriver(this.form.getRawValue()))).message);
      this.closeModal();
      await this.load();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo registrar al repartidor.'));
    } finally {
      this.saving.set(false);
    }
  }
}
