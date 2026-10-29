import { Injectable, inject } from '@angular/core';
import { HttpParams } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { PaymentReceipt, ReceiptKind } from '../models/receipt.model';

/** Payment receipts (comprobantes): every payment issues one, downloadable as PDF and emailed to the payer. */
@Injectable({ providedIn: 'root' })
export class ReceiptApiService {
  private readonly api = inject(ApiService);

  list(kind?: ReceiptKind) {
    const params = kind ? new HttpParams().set('kind', kind) : new HttpParams();
    return this.api.get<ApiResponse<PaymentReceipt[]>>('/receipts', { params });
  }

  async downloadPdf(kind: ReceiptKind, sourceId: string): Promise<void> {
    const blob = await firstValueFrom(
      this.api.get<Blob>(`/receipts/${kind}/${sourceId}/pdf`, { responseType: 'blob' as const }),
    );
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `comprobante-${kind}-${sourceId.slice(0, 8)}.pdf`;
    link.click();
    URL.revokeObjectURL(url);
  }

  resend(kind: ReceiptKind, sourceId: string) {
    return this.api.post<ApiResponse<PaymentReceipt>>(`/receipts/${kind}/${sourceId}/resend`, {});
  }
}
