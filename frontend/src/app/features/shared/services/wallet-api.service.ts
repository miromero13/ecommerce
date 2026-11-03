import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import {
  WalletBalance,
  WalletCheckoutPayload,
  WalletPayPayload,
  WalletRedeemResult,
  WalletTransaction,
} from '../models/wallet.model';

/** CU19 Store Wallet API service */
@Injectable({ providedIn: 'root' })
export class WalletApiService {
  private readonly api = inject(ApiService);

  balance() {
    return this.api.get<ApiResponse<WalletBalance>>('/wallet/balance');
  }

  redeem(cardCode: string) {
    return this.api.post<ApiResponse<WalletRedeemResult>>('/wallet/redeem-gift-card', { card_code: cardCode });
  }

  convertPoints(payload: { tenant_id: string; points: number }) {
    return this.api.post<ApiResponse<{ converted_points: number; credited_amount: number; new_balance: number; tenant_name: string }>>(
      '/wallet/convert-points',
      payload,
    );
  }

  pay(payload: WalletPayPayload) {
    return this.api.post<ApiResponse<{ order_id: string }>>('/wallet/pay', payload);
  }

  checkout(payload: WalletCheckoutPayload) {
    return this.api.post<ApiResponse<any>>('/wallet/checkout', payload);
  }

  transactions() {
    return this.api.get<ApiResponse<WalletTransaction[]>>('/wallet/transactions');
  }
}
