import { CommonModule } from '@angular/common';
import { Component, effect, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { provideIcons } from '@ng-icons/core';
import { lucidePencil } from '@ng-icons/lucide';

import { HlmButton } from '../../../components/button/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmIconImports } from '../../../components/icon/src';
import { HlmInput } from '../../../components/input/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { UpdateProfileRequest } from '../models/auth.model';
import { PerfilUsuario } from '../models/user.model';
import { SessionService } from '../services/session.service';
import { UserApiService } from '../services/user-api.service';

@Component({
  selector: 'app-profile-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HlmButton, HlmInput, ...HlmFieldImports, ...HlmIconImports],
  providers: [provideIcons({ lucidePencil })],
  templateUrl: './profile-page.component.html',
})
export class ProfilePageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly session = inject(SessionService);
  private readonly userApi = inject(UserApiService);

  protected readonly user = signal<PerfilUsuario | null>(this.session.user());
  protected readonly userRoleLabel = signal('');
  protected readonly errorMessage = signal('');
  protected readonly successMessage = signal('');
  protected readonly loading = signal(false);
  protected readonly isEditing = signal(false);

  protected readonly form = this.fb.nonNullable.group({
    name: ['', [Validators.required]],
    email: ['', [Validators.required, Validators.email]],
    gender: ['masculino', [Validators.required]],
  });

  protected normalizeEmailInput(event: Event): void {
    const input = event.target as HTMLInputElement | null;
    if (!input) return;

    const value = input.value.trim().toLowerCase();
    this.form.controls.email.setValue(value, { emitEvent: false });
  }

  private setEditingState(isEditing: boolean): void {
    this.isEditing.set(isEditing);
    if (isEditing) {
      this.form.enable({ emitEvent: false });
    } else {
      this.form.disable({ emitEvent: false });
    }
  }

  protected startEditing(): void {
    this.setEditingState(true);
  }

  protected cancelEditing(): void {
    const currentUser = this.session.user();
    if (currentUser) {
      this.form.reset({
        name: currentUser.name,
        email: currentUser.email,
        gender: currentUser.gender,
      });
    }

    this.errorMessage.set('');
    this.setEditingState(false);
  }

  constructor() {
    effect(() => {
      const currentUser = this.session.user();
      this.user.set(currentUser);

      if (!currentUser) {
        this.userRoleLabel.set('');
        return;
      }

      this.form.reset({
        name: currentUser.name,
        email: currentUser.email,
        gender: currentUser.gender,
      });

      switch (currentUser.rol) {
        case 'administrador':
          this.userRoleLabel.set('Administrador');
          break;
        case 'proveedor':
          this.userRoleLabel.set('Proveedor');
          break;
        case 'encargado':
          this.userRoleLabel.set('Encargado');
          break;
        case 'cajero':
          this.userRoleLabel.set('Cajero');
          break;
        case 'delivery':
          this.userRoleLabel.set('Delivery');
          break;
        default:
          this.userRoleLabel.set('Cliente');
      }

      if (!this.isEditing()) {
        this.form.disable({ emitEvent: false });
      }
    });
  }

  protected async submit(): Promise<void> {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');
    try {
      const payload = this.form.getRawValue();
      const request: UpdateProfileRequest = {
        name: payload.name,
        email: payload.email.trim().toLowerCase(),
        gender: payload.gender as UpdateProfileRequest['gender'],
      };

      await firstValueFrom(this.userApi.updateMe(request));
      await this.session.refreshMe();
      this.user.set(this.session.user());
      this.successMessage.set('Perfil actualizado correctamente.');
      this.setEditingState(false);
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo actualizar el perfil.'));
    } finally {
      this.loading.set(false);
    }
  }
}
