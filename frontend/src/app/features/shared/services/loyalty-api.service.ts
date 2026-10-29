import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { LoyaltyBalance, LoyaltyMovement } from '../models/loyalty.model';

/** CU17 loyalty program. */
@Injectable({ providedIn: 'root' })
export class LoyaltyApiService {
  private readonly api = inject(ApiService);

  balances() {
    return this.api.get<ApiResponse<LoyaltyBalance[]>>('/loyalty/balance');
  }

  transactions() {
    return this.api.get<ApiResponse<LoyaltyMovement[]>>('/loyalty/transactions');
  }

  /** Till: balance of a registered customer in the cashier's company. */
  customer(email: string) {
    return this.api.get<ApiResponse<LoyaltyBalance>>(`/loyalty/customer?email=${encodeURIComponent(email)}`);
  }
}
