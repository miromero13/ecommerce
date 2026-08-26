import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { GeneroUsuario } from '../models/auth.model';
import { SessionService } from '../services/session.service';
import { getDefaultRouteForRole } from '../../../core/utils/role-route.util';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmInput } from '../../../components/input/src';

@Component({
  selector: 'app-register-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, HlmButton, HlmInput, ...HlmCardImports],
  templateUrl: './register-page.component.html',
})
export class RegisterPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly session = inject(SessionService);
  private readonly router = inject(Router);

  protected readonly loading = signal(false);
  protected readonly errorMessage = signal('');

  protected readonly form = this.fb.nonNullable.group({
    name: ['', [Validators.required]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
    gender: ['masculino' as GeneroUsuario, [Validators.required]],
  });

  protected async submit(): Promise<void> {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    this.errorMessage.set('');
    try {
      await this.session.register(this.form.getRawValue());
      await this.router.navigateByUrl(getDefaultRouteForRole(this.session.user()?.rol));
    } catch {
      this.errorMessage.set('No se pudo registrar la cuenta. Verifica los datos.');
    } finally {
      this.loading.set(false);
    }
  }
}
