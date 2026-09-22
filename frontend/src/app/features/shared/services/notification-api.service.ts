import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';
import { NotificationItem } from '../models/notification.model';

@Injectable({ providedIn: 'root' })
export class NotificationApiService {
  private readonly api = inject(ApiService);

  list() {
    return this.api.get<ApiResponse<NotificationItem[]>>('/notifications');
  }

  unreadCount() {
    return this.api.get<ApiResponse<{ count: number }>>('/notifications/unread-count');
  }

  markRead(id: string) {
    return this.api.patch<ApiResponse<NotificationItem>>(`/notifications/${id}/read`, {});
  }

  markAllRead() {
    return this.api.patch<ApiResponse<{ updated: number }>>('/notifications/read-all', {});
  }

  registerToken(token: string) {
    return this.api.post<ApiResponse<{ id: string; token: string; platform: string }>>('/notifications/tokens', {
      token,
      platform: 'web',
    });
  }

  unregisterToken(token: string) {
    return this.api.delete<ApiResponse<{ removed: boolean }>>('/notifications/tokens', {
      body: { token, platform: 'web' },
    });
  }
}
