import { Component, effect, inject, untracked } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { HlmToaster } from '@spartan-ng/helm/sonner';
import { SessionService } from './features/shared/services/session.service';
import { NotificationPushService } from './features/shared/services/notification-push.service';
import { OfflineSyncService } from './core/services/offline-sync.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, HlmToaster],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  private readonly session = inject(SessionService);
  private readonly notifications = inject(NotificationPushService);
  // CU30: pending offline sales are sent at boot/login and whenever the connection returns.
  private readonly offlineSync = inject(OfflineSyncService);

  constructor() {
    effect(() => {
      if (this.session.isAuthenticated()) {
        void this.notifications.start();
        untracked(() => void this.offlineSync.triggerAutoSync());
      } else {
        this.notifications.stop();
      }
    });
    void this.session.bootstrap();
  }
}
