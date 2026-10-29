import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { BankAccount, PayoutSummary, Settlement } from '../models/payout.model';

@Injectable({ providedIn: 'root' })
export class PayoutApiService {
  private readonly api = inject(ApiService);

  summary() {
    return this.api.get<ApiResponse<PayoutSummary>>('/payouts/summary');
  }

  updateBankAccount(payload: BankAccount) {
    return this.api.put<ApiResponse<BankAccount>>('/payouts/bank-account', payload);
  }

  settlements() {
    return this.api.get<ApiResponse<Settlement[]>>('/payouts/settlements');
  }

  runSettlements() {
    return this.api.post<ApiResponse<Settlement[]>>('/payouts/settlements/run', {});
  }

  markPaid(settlementId: string, transferReference: string) {
    return this.api.patch<ApiResponse<Settlement>>(`/payouts/settlements/${settlementId}/paid`, {
      transfer_reference: transferReference,
    });
  }
}
