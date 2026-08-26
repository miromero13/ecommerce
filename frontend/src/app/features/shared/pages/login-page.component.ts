import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { RolUsuario } from '../models/auth.model';
import { SessionService } from '../services/session.service';
import { getDefaultRouteForRole } from '../../../core/utils/role-route.util';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInput } from '../../../components/input/src';
import { HlmTabsImports } from '../../../components/tabs/src';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, HlmButton, HlmInput, ...HlmCardImports, ...HlmFieldImports, ...HlmTabsImports],
  templateUrl: './login-page.component.html',
})
export class LoginPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly session = inject(SessionService);
  private readonly router = inject(Router);

  protected readonly loading = signal(false);
  protected readonly errorMessage = signal('');
  protected readonly activeRole = signal<RolUsuario>('cliente');

  protected readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required]],
    rol: ['cliente' as RolUsuario, [Validators.required]],
  });

  protected selectRole(role: RolUsuario | string): void {
    const selectedRole = role as RolUsuario;
    this.activeRole.set(selectedRole);
    this.form.controls.rol.setValue(selectedRole);
  }

  protected async submit(): Promise<void> {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    this.errorMessage.set('');
    try {
      const { email, password, rol } = this.form.getRawValue();
      await this.session.login(email, password, rol);
      await this.router.navigateByUrl(getDefaultRouteForRole(this.session.user()?.rol));
    } catch {
      this.errorMessage.set('No se pudo iniciar sesión. Verifica tus credenciales.');
    } finally {
      this.loading.set(false);
    }
  }
}
