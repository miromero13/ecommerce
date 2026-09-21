import { Component, effect, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { HlmToaster } from '@spartan-ng/helm/sonner';
import { SessionService } from './features/shared/services/session.service';
import { NotificationPushService } from './features/shared/services/notification-push.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, HlmToaster],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  private readonly session = inject(SessionService);
  private readonly notifications = inject(NotificationPushService);

  constructor() {
    effect(() => {
      if (this.session.isAuthenticated()) {
        void this.notifications.start();
      } else {
        this.notifications.stop();
      }
    });
    void this.session.bootstrap();
  }
}
