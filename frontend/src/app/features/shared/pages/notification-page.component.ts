import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { toast } from '@spartan-ng/brain/sonner';

import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { NotificationItem, notificationRoute } from '../models/notification.model';
import { NotificationPushService } from '../services/notification-push.service';
import { SessionService } from '../services/session.service';
import { ExpertReplenishmentApiService } from '../services/expert-replenishment-api.service';

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
  private readonly replenishmentApi = inject(ExpertReplenishmentApiService);

  protected readonly processingId = signal<string | null>(null);

  constructor() {
    void this.push.refresh();
  }

  // [CU12 - Secuencia: Paso 1] El Cliente ejecuta enablePush() en NotificationPageComponent
  protected async enablePush(): Promise<void> {
    try {
      await this.push.enable();
    } catch {
      // The service exposes a safe generic error state for the page.
    }
  }

  // [CU12 - Secuencia: Paso 3] El Cliente ejecuta markAllRead() en NotificationPageComponent
  protected async markAllRead(): Promise<void> {
    try {
      await this.push.markAllRead();
    } catch {
      // Keep the list unchanged when the API is unavailable.
    }
  }

  // [CU12 - Secuencia: Paso 2] El Cliente ejecuta open(item) en NotificationPageComponent
  protected async open(item: NotificationItem): Promise<void> {
    if (this.isReplenishment(item)) {
      // Handled directly inside the interactive card actions
      return;
    }
    try {
      await this.push.markRead(item);
    } catch {
      // Navigation remains safe even if marking read fails.
    }
    await this.router.navigateByUrl(notificationRoute(item.data, this.session.user()?.rol));
  }

  protected isReplenishment(item: NotificationItem): boolean {
    return item.data?.['destination'] === 'expert_replenishment' && !!item.data?.['suggestion_id'];
  }

  // [CU09 - Secuencia: Paso 6] El Administrador del tenant ejecuta applyReplenishment(item, event) en NotificationPageComponent
  protected async applyReplenishment(item: NotificationItem, event?: Event): Promise<void> {
    if (event) {
      event.stopPropagation();
    }
    const suggestionId = item.data?.['suggestion_id'] as string;
    if (!suggestionId) return;

    this.processingId.set(item.id);
    try {
      const res = await firstValueFrom(
        this.replenishmentApi.applyTransfers({ transfer_ids: [suggestionId] })
      );
      toast.success(res.message || 'Órdenes de traspaso automático aplicadas al inventario');
      await this.push.markRead(item);
      void this.push.refresh();
    } catch (err) {
      toast.error('Error al aplicar traspaso', {
        description: getErrorMessage(err, 'No se pudo aplicar el traspaso sugerido'),
      });
    } finally {
      this.processingId.set(null);
    }
  }

  // [CU09 - Secuencia: Paso 7] El Administrador del tenant ejecuta discardReplenishment(item, event) en NotificationPageComponent
  protected async discardReplenishment(item: NotificationItem, event?: Event): Promise<void> {
    if (event) {
      event.stopPropagation();
    }
    const suggestionId = item.data?.['suggestion_id'] as string;
    if (!suggestionId) return;

    this.processingId.set(item.id);
    try {
      const res = await firstValueFrom(
        this.replenishmentApi.discardTransfers({ transfer_ids: [suggestionId] })
      );
      toast.success(res.message || 'Sugerencia de traspaso descartada');
      await this.push.markRead(item);
      void this.push.refresh();
    } catch (err) {
      toast.error('Error al descartar', {
        description: getErrorMessage(err, 'No se pudo descartar la sugerencia'),
      });
    } finally {
      this.processingId.set(null);
    }
  }
}
