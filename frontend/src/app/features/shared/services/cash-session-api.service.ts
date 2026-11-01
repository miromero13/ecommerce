import { Injectable, inject, signal } from '@angular/core';
import { HttpParams } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { CashSession } from '../models/cash-session.model';
import { SessionService } from './session.service';

/** 1P-CU18 cash drawer. `current` is the cashier's open drawer, shared by the till and its panel. */
@Injectable({ providedIn: 'root' })
export class CashSessionApiService {
  private readonly api = inject(ApiService);
  private readonly session = inject(SessionService);
  readonly current = signal<CashSession | null>(null);

  /** Last open drawer seen online by this cashier: offline cash sales are attributed to it. */
  offlineSessionId(): string | null {
    return localStorage.getItem(this.offlineKey());
  }

  private offlineKey(): string {
    return `aci_offline_cash_session:${this.session.user()?.id ?? ''}`;
  }

  private setCurrent(session: CashSession | null): void {
    this.current.set(session);
    if (session) localStorage.setItem(this.offlineKey(), session.id);
    else localStorage.removeItem(this.offlineKey());
  }

  async loadCurrent(): Promise<CashSession | null> {
    const res = await firstValueFrom(this.api.get<ApiResponse<CashSession | null>>('/cash-sessions/current'));
    this.setCurrent(res.data ?? null);
    return this.current();
  }

  async open(openingAmount: number): Promise<string> {
    const res = await firstValueFrom(this.api.post<ApiResponse<CashSession>>('/cash-sessions/open', { opening_amount: openingAmount }));
    this.setCurrent(res.data ?? null);
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
    this.setCurrent(null);
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
