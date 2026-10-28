import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { toast } from '@spartan-ng/brain/sonner';

import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmFieldImports } from '../../../components/field/src';
import { HlmInput } from '../../../components/input/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import {
  ExpertRule,
  ExpertSuggestion,
  SuggestionStatus,
} from '../../shared/models/expert-replenishment.model';
import { ExpertReplenishmentApiService } from '../../shared/services/expert-replenishment-api.service';

@Component({
  selector: 'app-admin-expert-replenishment-page',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    HlmButton,
    HlmInput,
    ...HlmCardImports,
    ...HlmFieldImports,
  ],
  templateUrl: './admin-expert-replenishment-page.component.html',
})
export class AdminExpertReplenishmentPageComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly replenishmentApi = inject(ExpertReplenishmentApiService);

  protected readonly rules = signal<ExpertRule | null>(null);
  protected readonly suggestions = signal<ExpertSuggestion[]>([]);
  protected readonly selectedSuggestionIds = signal<Set<string>>(new Set());

  protected readonly isLoadingRules = signal(false);
  protected readonly isSavingRules = signal(false);
  protected readonly isEvaluating = signal(false);
  protected readonly isApplying = signal(false);
  protected readonly statusFilter = signal<string>('pending');

  protected readonly rulesForm = this.fb.group({
    lookback_days: [7, [Validators.required, Validators.min(1), Validators.max(90)]],
    coverage_days: [14, [Validators.required, Validators.min(1), Validators.max(90)]],
    is_auto_enabled: [false],
  });

  protected readonly filteredSuggestions = computed(() => {
    const filter = this.statusFilter();
    const list = this.suggestions();
    if (!filter || filter === 'all') {
      return list;
    }
    return list.filter((s) => s.status === filter);
  });

  protected readonly pendingCount = computed(() => {
    return this.suggestions().filter((s) => s.status === 'pending').length;
  });

  protected readonly selectedCount = computed(() => {
    return this.selectedSuggestionIds().size;
  });

  protected readonly allPendingSelected = computed(() => {
    const pending = this.filteredSuggestions().filter((s) => s.status === 'pending');
    if (pending.length === 0) return false;
    const selected = this.selectedSuggestionIds();
    return pending.every((s) => selected.has(s.id));
  });

  async ngOnInit(): Promise<void> {
    await Promise.all([this.loadRules(), this.loadSuggestions()]);
  }

  async loadRules(): Promise<void> {
    this.isLoadingRules.set(true);
    try {
      const res = await firstValueFrom(this.replenishmentApi.getRules());
      if (res.data) {
        this.rules.set(res.data);
        this.rulesForm.patchValue({
          lookback_days: res.data.lookback_days,
          coverage_days: res.data.coverage_days,
          is_auto_enabled: res.data.is_auto_enabled,
        });
      }
    } catch (err) {
      toast.error('Error al cargar reglas', {
        description: getErrorMessage(err, 'No se pudieron obtener las reglas de reabastecimiento'),
      });
    } finally {
      this.isLoadingRules.set(false);
    }
  }

  async saveRules(): Promise<void> {
    if (this.rulesForm.invalid) {
      this.rulesForm.markAllAsTouched();
      return;
    }
    this.isSavingRules.set(true);
    try {
      const formVal = this.rulesForm.value;
      const res = await firstValueFrom(
        this.replenishmentApi.updateRules({
          lookback_days: formVal.lookback_days ?? 7,
          coverage_days: formVal.coverage_days ?? 14,
          is_auto_enabled: formVal.is_auto_enabled ?? false,
        })
      );
      if (res.data) {
        this.rules.set(res.data);
      }
      toast.success(res.message || 'Reglas de reabastecimiento actualizadas');
    } catch (err) {
      toast.error('Error al guardar reglas', {
        description: getErrorMessage(err, 'No se pudieron actualizar los parámetros'),
      });
    } finally {
      this.isSavingRules.set(false);
    }
  }

  async loadSuggestions(): Promise<void> {
    try {
      const res = await firstValueFrom(this.replenishmentApi.getSuggestions());
      this.suggestions.set(res.data ?? []);
      this.selectedSuggestionIds.set(new Set());
    } catch (err) {
      toast.error('Error al cargar sugerencias', {
        description: getErrorMessage(err, 'No se pudieron obtener las sugerencias'),
      });
    }
  }

  async evaluateReplenishment(): Promise<void> {
    this.isEvaluating.set(true);
    try {
      const res = await firstValueFrom(this.replenishmentApi.evaluate());
      this.suggestions.set(res.data ?? []);
      this.selectedSuggestionIds.set(new Set());
      this.statusFilter.set('pending');
      toast.success(res.message || 'Evaluación del sistema experto finalizada');
    } catch (err) {
      toast.error('Error en la evaluación', {
        description: getErrorMessage(err, 'Ocurrió un error al ejecutar el motor de inferencia'),
      });
    } finally {
      this.isEvaluating.set(false);
    }
  }

  toggleSelectAll(): void {
    const pending = this.filteredSuggestions().filter((s) => s.status === 'pending');
    const selected = new Set(this.selectedSuggestionIds());

    if (this.allPendingSelected()) {
      for (const s of pending) {
        selected.delete(s.id);
      }
    } else {
      for (const s of pending) {
        selected.add(s.id);
      }
    }
    this.selectedSuggestionIds.set(selected);
  }

  toggleSelectRow(suggestion: ExpertSuggestion): void {
    if (suggestion.status !== 'pending') return;
    const selected = new Set(this.selectedSuggestionIds());
    if (selected.has(suggestion.id)) {
      selected.delete(suggestion.id);
    } else {
      selected.add(suggestion.id);
    }
    this.selectedSuggestionIds.set(selected);
  }

  async applySelectedTransfers(): Promise<void> {
    const ids = Array.from(this.selectedSuggestionIds());
    if (ids.length === 0) return;

    this.isApplying.set(true);
    try {
      const res = await firstValueFrom(
        this.replenishmentApi.applyTransfers({ transfer_ids: ids })
      );
      toast.success(res.message || 'Órdenes de traspaso automático aplicadas al inventario');
      this.selectedSuggestionIds.set(new Set());
      await this.loadSuggestions();
    } catch (err) {
      toast.error('Error al aplicar traspasos', {
        description: getErrorMessage(err, 'No se pudieron aplicar las transferencias automáticas'),
      });
    } finally {
      this.isApplying.set(false);
    }
  }

  setStatusFilter(filter: string): void {
    this.statusFilter.set(filter);
    this.selectedSuggestionIds.set(new Set());
  }

  getStatusBadgeClass(status: SuggestionStatus): string {
    switch (status) {
      case 'pending':
        return 'bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800';
      case 'applied':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800';
      case 'discarded':
        return 'bg-muted text-muted-foreground border-border';
      default:
        return 'bg-muted text-muted-foreground';
    }
  }

  getStatusLabel(status: SuggestionStatus): string {
    switch (status) {
      case 'pending':
        return 'Pendiente';
      case 'applied':
        return 'Aplicado';
      case 'discarded':
        return 'Descartado';
      default:
        return status;
    }
  }
}
