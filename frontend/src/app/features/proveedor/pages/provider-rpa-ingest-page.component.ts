import { CommonModule } from '@angular/common';
import { Component, OnDestroy, computed, inject, signal } from '@angular/core';
import { toast } from '@spartan-ng/brain/sonner';
import { firstValueFrom } from 'rxjs';

import { HlmButton } from '../../../components/button/src';
import { HlmInput } from '../../../components/input/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { AdminBranch } from '../../admin/models/admin-branch.model';
import { AdminBranchService } from '../../admin/services/admin-branch.service';
import { RpaItem, RpaJob } from '../../shared/models/rpa-ingest.model';
import { RpaIngestApiService } from '../../shared/services/rpa-ingest-api.service';
import { SessionService } from '../../shared/services/session.service';

const ACCEPTED = ['application/pdf', 'image/png', 'image/jpeg', 'image/webp'];
const MAX_BYTES = 10 * 1024 * 1024;
const POLL_MS = 2000;

/**
 * CU10 RPA ingestion. The supplier uploads a delivery note; Gemini extracts the garments;
 * the draft can be corrected; an administrator or branch manager commits it into a branch.
 */
@Component({
  selector: 'app-provider-rpa-ingest-page',
  standalone: true,
  imports: [CommonModule, HlmButton, HlmInput],
  templateUrl: './provider-rpa-ingest-page.component.html',
})
export class ProviderRpaIngestPageComponent implements OnDestroy {
  private readonly api = inject(RpaIngestApiService);
  private readonly session = inject(SessionService);
  private readonly branchApi = inject(AdminBranchService);
  private poll?: ReturnType<typeof setInterval>;

  protected readonly rol = this.session.user()?.rol;
  protected readonly canCommit = this.rol === 'administrador' || this.rol === 'encargado';
  protected readonly jobs = signal<RpaJob[]>([]);
  protected readonly selected = signal<RpaJob | null>(null);
  protected readonly items = signal<RpaItem[]>([]);
  protected readonly branches = signal<AdminBranch[]>([]);
  protected readonly branchId = signal(this.session.user()?.branch_id ?? '');
  protected readonly busy = signal(false);
  protected readonly dragging = signal(false);
  protected readonly unrecognized = computed(() => this.items().filter((item) => !item.recognized).length);

  constructor() {
    void this.loadJobs();
    // Administrators choose the receiving branch; a branch manager always receives into their own.
    if (this.rol === 'administrador') void this.loadBranches();
  }

  ngOnDestroy(): void {
    this.stopPolling();
  }

  protected onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragging.set(false);
    const file = event.dataTransfer?.files?.[0];
    if (file) void this.upload(file);
  }

  protected onPick(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (file) void this.upload(file);
  }

  private async upload(file: File): Promise<void> {
    // Same limits as the backend, checked first for immediate feedback.
    if (!ACCEPTED.includes(file.type)) {
      toast.error('El archivo proporcionado no es un documento PDF o imagen válido');
      return;
    }
    if (file.size > MAX_BYTES) {
      toast.error('El documento no puede superar los 10 MB');
      return;
    }
    this.busy.set(true);
    try {
      const response = await firstValueFrom(this.api.upload(file));
      toast.success(response.message);
      await this.loadJobs();
      if (response.data) this.watch(response.data.job_id);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo subir el documento.'));
    } finally {
      this.busy.set(false);
    }
  }

  protected async open(job: RpaJob): Promise<void> {
    this.stopPolling();
    if (job.status === 'processing') {
      this.watch(job.job_id);
      return;
    }
    await this.refresh(job.job_id, true);
  }

  /** Poll the background extraction until it finishes. */
  private watch(jobId: string): void {
    this.stopPolling();
    this.selected.set(this.jobs().find((job) => job.job_id === jobId) ?? null);
    this.poll = setInterval(() => void this.refresh(jobId, false), POLL_MS);
  }

  private async refresh(jobId: string, notify: boolean): Promise<void> {
    try {
      const response = await firstValueFrom(this.api.job(jobId));
      const job = response.data!;
      if (job.status === 'processing') return;
      this.stopPolling();
      this.show(job);
      if (notify || job.status === 'completed') toast.success(response.message);
      await this.loadJobs();
    } catch (error) {
      // 422: the AI could not read garment lines from the document.
      this.stopPolling();
      this.selected.set(null);
      toast.error(getErrorMessage(error, 'No se pudo leer el documento.'));
      await this.loadJobs();
    }
  }

  protected setItem(index: number, field: 'sku' | 'quantity', event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.items.update((items) => items.map((item, i) =>
      i === index ? { ...item, [field]: field === 'quantity' ? Number(value) : value } : item));
  }

  protected removeItem(index: number): void {
    this.items.update((items) => items.filter((_, i) => i !== index));
  }

  protected async saveCorrections(): Promise<void> {
    const job = this.selected();
    if (!job || !this.items().length) return;
    await this.run(async () => {
      const response = await firstValueFrom(this.api.correct(job.job_id, this.items()));
      this.show(response.data!);
      return response.message;
    }, 'No se pudieron guardar las correcciones.');
  }

  protected async commit(): Promise<void> {
    const job = this.selected();
    if (!job || !this.branchId()) {
      toast.warning('Selecciona la sucursal que recibe la mercadería.');
      return;
    }
    await this.run(async () => {
      const response = await firstValueFrom(this.api.commit(job.job_id, this.branchId()));
      const skipped = response.data?.unrecognized_items.length ?? 0;
      this.selected.set(null);
      await this.loadJobs();
      return skipped ? `${response.message}. ${skipped} ítem(s) no reconocido(s) quedaron fuera.` : response.message;
    }, 'No se pudo ingresar la mercadería.');
  }

  protected statusLabel(status: RpaJob['status']): string {
    return { processing: 'Procesando…', completed: 'Listo para revisar', failed: 'No se pudo leer', committed: 'Ingresado' }[status];
  }

  private show(job: RpaJob): void {
    this.selected.set(job);
    this.items.set(job.extracted_items.map((item) => ({ ...item })));
  }

  private async run(action: () => Promise<string>, fallback: string): Promise<void> {
    this.busy.set(true);
    try {
      toast.success(await action());
    } catch (error) {
      toast.error(getErrorMessage(error, fallback));
    } finally {
      this.busy.set(false);
    }
  }

  private async loadJobs(): Promise<void> {
    try {
      this.jobs.set((await firstValueFrom(this.api.jobs())).data ?? []);
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar los documentos.'));
    }
  }

  private async loadBranches(): Promise<void> {
    try {
      this.branches.set(((await firstValueFrom(this.branchApi.listBranches())).data ?? []).filter((b) => b.is_active));
    } catch {
      this.branches.set([]);
    }
  }

  private stopPolling(): void {
    if (this.poll) clearInterval(this.poll);
    this.poll = undefined;
  }
}
