import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

import { AdminBranch } from '../models/admin-branch.model';
import { AdminBranchService } from '../services/admin-branch.service';
import { getErrorMessage } from '../../../core/utils/http-error.util';

@Component({
  selector: 'app-admin-branch-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './admin-branch-page.component.html',
})
export class AdminBranchPageComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(AdminBranchService);

  protected readonly branches = signal<AdminBranch[]>([]);
  protected readonly errorMessage = signal('');
  protected readonly successMessage = signal('');
  protected readonly loading = signal(false);

  protected readonly form = this.fb.nonNullable.group({
    name: ['', [Validators.required]],
    city: ['', [Validators.required]],
  });

  constructor() {
    void this.loadBranches();
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
      await firstValueFrom(this.api.createBranch(this.form.getRawValue()));
      this.form.reset({ name: '', city: '' });
      await this.loadBranches();
      this.successMessage.set('Sucursal creada correctamente.');
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudo crear la sucursal.'));
    } finally {
      this.loading.set(false);
    }
  }

  private async loadBranches(): Promise<void> {
    try {
      const response = await firstValueFrom(this.api.listBranches());
      this.branches.set(response.data ?? []);
    } catch (error) {
      this.errorMessage.set(getErrorMessage(error, 'No se pudieron cargar las sucursales.'));
    }
  }
}
