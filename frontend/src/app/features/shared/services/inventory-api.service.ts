import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import {
  InventoryBranchStock,
  InventoryConsolidatedStock,
  InventoryMovement,
} from '../models/inventory.model';

@Injectable({ providedIn: 'root' })
export class InventoryApiService {
  private readonly api = inject(ApiService);

  getConsolidatedStock() {
    return this.api.get<ApiResponse<InventoryConsolidatedStock[]>>('/inventory/consolidated');
  }

  getBranchStock(branchId: string) {
    return this.api.get<ApiResponse<InventoryBranchStock[]>>(`/inventory/branches/${branchId}`);
  }

  getMovements(params?: { branch_id?: string; variant_id?: string; movement_type?: string; limit?: number }) {
    const query = params
      ? '?' + Object.entries(params).filter(([, value]) => value !== undefined && value !== '').map(([key, value]) => `${key}=${encodeURIComponent(String(value))}`).join('&')
      : '';
    return this.api.get<ApiResponse<InventoryMovement[]>>(`/inventory/movements${query}`);
  }
}
