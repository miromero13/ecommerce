import { Injectable, inject } from '@angular/core';

import { ApiService } from '../../../core/services/api.service';
import { ApiResponse } from '../../../core/models/api.model';
import { CreatePromotionCodeRequest, PromotionCode } from '../models/promotion.model';

@Injectable({ providedIn: 'root' })
export class PromotionApiService {
  private readonly api = inject(ApiService);

  list() {
    return this.api.get<ApiResponse<PromotionCode[]>>('/promotions');
  }

  create(payload: CreatePromotionCodeRequest) {
    return this.api.post<ApiResponse<PromotionCode>>('/promotions', payload);
  }
}
