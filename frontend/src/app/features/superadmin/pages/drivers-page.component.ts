import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { toast } from '@spartan-ng/brain/sonner';
import { firstValueFrom } from 'rxjs';

import { HlmButton } from '../../../components/button/src';
import { HlmInput } from '../../../components/input/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { UsuarioAuth } from '../../shared/models/auth.model';
import { DeliveryApiService } from '../../shared/services/delivery-api.service';

// CU20: drivers belong to the platform and deliver for every company.
@Component({
  selector: 'app-drivers-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HlmButton, HlmInput],
  template: `
    <section class="space-y-6 text-slate-700">
      <header>
        <h1 class="text-2xl font-semibold">Repartidores de la plataforma</h1>
        <p class="text-sm text-slate-500">Los repartidores no pertenecen a una empresa: toman pedidos con envío de todas las empresas.</p>
      </header>

      <form class="grid gap-3 rounded-xl border border-slate-200 bg-white p-4 sm:grid-cols-5" [formGroup]="form" (ngSubmit)="create()">
        <input hlmInput placeholder="Nombre" formControlName="name" />
        <input hlmInput placeholder="Correo" type="email" formControlName="email" />
        <input hlmInput placeholder="Contraseña (mín. 8)" type="password" formControlName="password" />
        <select class="h-9 rounded-md border border-slate-300 bg-white px-3 text-sm" formControlName="gender">
          <option value="masculino">Masculino</option>
          <option value="femenino">Femenino</option>
        </select>
        <button hlmBtn type="submit" [disabled]="form.invalid || saving()">Registrar repartidor</button>
      </form>

      <div class="overflow-hidden rounded-xl border border-slate-200 bg-white">
        @for (driver of drivers(); track driver.id) {
          <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3 text-sm last:border-0">
            <div><p class="font-medium text-slate-900">{{ driver.name }}</p><p class="text-xs text-slate-500">{{ driver.email }}</p></div>
            <span class="rounded-full px-2.5 py-1 text-xs font-medium" [class]="driver.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'">{{ driver.is_active ? 'Activo' : 'Inactivo' }}</span>
          </div>
        } @empty {
          <p class="p-4 text-sm text-slate-500">Aún no hay repartidores registrados.</p>
        }
      </div>
    </section>
  `,
})
export class DriversPageComponent {
  private readonly api = inject(DeliveryApiService);
  private readonly fb = inject(FormBuilder);
  protected readonly drivers = signal<UsuarioAuth[]>([]);
  protected readonly saving = signal(false);
  protected readonly form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
    gender: ['masculino' as 'masculino' | 'femenino', [Validators.required]],
  });

  constructor() {
    void this.load();
  }

  private async load(): Promise<void> {
    try {
      this.drivers.set((await firstValueFrom(this.api.drivers())).data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar los repartidores.'));
    }
  }

  protected async create(): Promise<void> {
    this.saving.set(true);
    try {
      toast.success((await firstValueFrom(this.api.createDriver(this.form.getRawValue()))).message);
      this.form.reset({ name: '', email: '', password: '', gender: 'masculino' });
      await this.load();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo registrar al repartidor.'));
    } finally {
      this.saving.set(false);
    }
  }
}
