import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { RpaCommitResult, RpaItem, RpaJob } from '../models/rpa-ingest.model';

@Injectable({ providedIn: 'root' })
export class RpaIngestApiService {
  private readonly api = inject(ApiService);

  upload(file: File) {
    const body = new FormData();
    body.append('file', file);
    return this.api.post<ApiResponse<{ job_id: string; filename: string; status: string }>>('/rpa/ingest/upload-document', body);
  }

  jobs() {
    return this.api.get<ApiResponse<RpaJob[]>>('/rpa/ingest/jobs');
  }

  job(jobId: string) {
    return this.api.get<ApiResponse<RpaJob>>(`/rpa/ingest/jobs/${jobId}`);
  }

  correct(jobId: string, items: RpaItem[]) {
    const clean = items.map(({ sku, name, size, color, quantity, unit_cost }) => ({ sku, name, size, color, quantity, unit_cost }));
    return this.api.patch<ApiResponse<RpaJob>>(`/rpa/ingest/jobs/${jobId}/items`, { items: clean });
  }

  commit(jobId: string, branchId: string) {
    return this.api.post<ApiResponse<RpaCommitResult>>(`/rpa/ingest/jobs/${jobId}/commit`, { branch_id: branchId });
  }
}
