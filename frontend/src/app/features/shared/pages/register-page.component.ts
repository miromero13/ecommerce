import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { toast } from '@spartan-ng/brain/sonner';

import { GeneroUsuario } from '../models/auth.model';
import { SessionService } from '../services/session.service';
import { getDefaultRouteForRole } from '../../../core/utils/role-route.util';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmInput } from '../../../components/input/src';
import { HlmSelectImports } from '../../../components/select/src';

@Component({
  selector: 'app-register-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, HlmButton, HlmInput, ...HlmCardImports, ...HlmSelectImports],
  templateUrl: './register-page.component.html',
})
export class RegisterPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly session = inject(SessionService);
  private readonly router = inject(Router);

  protected readonly loading = signal(false);

  protected readonly form = this.fb.nonNullable.group({
    name: ['', [Validators.required]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
    gender: ['masculino' as GeneroUsuario, [Validators.required]],
  });

  protected normalizeEmailInput(event: Event): void {
    const input = event.target as HTMLInputElement | null;
    if (!input) return;

    const value = input.value.trim().toLowerCase();
    this.form.controls.email.setValue(value, { emitEvent: false });
  }

  protected async submit(): Promise<void> {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    try {
      const payload = this.form.getRawValue();
      const request = this.session.register({ ...payload, email: payload.email.trim().toLowerCase() });
      toast.promise(request, {
        loading: 'Creando cuenta...',
        success: 'Cuenta creada correctamente.',
        error: () => 'No se pudo registrar la cuenta. Verifica los datos.',
      });
      await request;
      await this.router.navigateByUrl(getDefaultRouteForRole(this.session.user()?.rol));
    } catch {
      // El toast de error ya se mostró con toast.promise
    } finally {
      this.loading.set(false);
    }
  }
}
