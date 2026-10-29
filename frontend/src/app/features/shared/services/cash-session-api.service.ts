import { Injectable, inject, signal } from '@angular/core';
import { HttpParams } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { CashSession } from '../models/cash-session.model';

/** 1P-CU18 cash drawer. `current` is the cashier's open drawer, shared by the till and its panel. */
@Injectable({ providedIn: 'root' })
export class CashSessionApiService {
  private readonly api = inject(ApiService);
  readonly current = signal<CashSession | null>(null);

  async loadCurrent(): Promise<CashSession | null> {
    const res = await firstValueFrom(this.api.get<ApiResponse<CashSession | null>>('/cash-sessions/current'));
    this.current.set(res.data ?? null);
    return this.current();
  }

  async open(openingAmount: number): Promise<string> {
    const res = await firstValueFrom(this.api.post<ApiResponse<CashSession>>('/cash-sessions/open', { opening_amount: openingAmount }));
    this.current.set(res.data ?? null);
    return res.message;
  }

  async addMovement(type: 'deposit' | 'withdrawal', amount: number, reason: string): Promise<string> {
    const res = await firstValueFrom(
      this.api.post<ApiResponse<CashSession>>('/cash-sessions/current/movements', { type, amount, reason }),
    );
    this.current.set(res.data ?? null);
    return res.message;
  }

  async close(countedAmount: number, note: string): Promise<{ message: string; session: CashSession | null }> {
    const res = await firstValueFrom(
      this.api.post<ApiResponse<CashSession>>('/cash-sessions/current/close', { counted_amount: countedAmount, note: note || null }),
    );
    this.current.set(null);
    return { message: res.message, session: res.data ?? null };
  }

  /** Administrator: any branch of the company; manager: their branch; cashier: their own drawers. */
  list(filters: { branch_id?: string; day?: string } = {}) {
    let params = new HttpParams();
    if (filters.branch_id) params = params.set('branch_id', filters.branch_id);
    if (filters.day) params = params.set('day', filters.day);
    return this.api.get<ApiResponse<CashSession[]>>('/cash-sessions', { params });
  }

  get(sessionId: string) {
    return this.api.get<ApiResponse<CashSession>>(`/cash-sessions/${sessionId}`);
  }
}
