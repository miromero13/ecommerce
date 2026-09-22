import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';

import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { NotificationItem, notificationRoute } from '../models/notification.model';
import { NotificationPushService } from '../services/notification-push.service';
import { SessionService } from '../services/session.service';

@Component({
  selector: 'app-notification-page',
  standalone: true,
  imports: [CommonModule, HlmButton, ...HlmCardImports],
  templateUrl: './notification-page.component.html',
})
export class NotificationPageComponent {
  protected readonly push = inject(NotificationPushService);
  private readonly session = inject(SessionService);
  private readonly router = inject(Router);

  constructor() {
    void this.push.refresh();
  }

  protected async enablePush(): Promise<void> {
    try {
      await this.push.enable();
    } catch {
      // The service exposes a safe generic error state for the page.
    }
  }

  protected async markAllRead(): Promise<void> {
    try {
      await this.push.markAllRead();
    } catch {
      // Keep the list unchanged when the API is unavailable.
    }
  }

  protected async open(item: NotificationItem): Promise<void> {
    try {
      await this.push.markRead(item);
    } catch {
      // Navigation remains safe even if marking read fails.
    }
    await this.router.navigateByUrl(notificationRoute(item.data, this.session.user()?.rol));
  }
}
