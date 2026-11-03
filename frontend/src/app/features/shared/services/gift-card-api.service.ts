import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { GiftCard, GiftCardPurchasePayload, GiftCardVerify } from '../models/gift-card.model';

/** CU18 Gift Cards API service */
@Injectable({ providedIn: 'root' })
export class GiftCardApiService {
  private readonly api = inject(ApiService);

  purchase(payload: GiftCardPurchasePayload) {
    return this.api.post<ApiResponse<GiftCard>>('/gift-cards/purchase', payload);
  }

  myPurchases() {
    return this.api.get<ApiResponse<GiftCard[]>>('/gift-cards/my-purchases');
  }

  verify(code: string) {
    return this.api.get<ApiResponse<GiftCardVerify>>(`/gift-cards/verify/${encodeURIComponent(code)}`);
  }
}
