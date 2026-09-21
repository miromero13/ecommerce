import { Injectable, signal } from '@angular/core';
import { getApp, getApps, initializeApp } from 'firebase/app';
import { getMessaging, getToken, isSupported, onMessage, type Messaging } from 'firebase/messaging';
import { firstValueFrom } from 'rxjs';

import { environment } from '../../../../environments/environment';
import { NotificationItem } from '../models/notification.model';
import { NotificationApiService } from './notification-api.service';

export type PushPermission = NotificationPermission | 'unsupported';

@Injectable({ providedIn: 'root' })
export class NotificationPushService {
  private readonly notificationsSignal = signal<NotificationItem[]>([]);
  private readonly unreadCountSignal = signal(0);
  private readonly loadingSignal = signal(false);
  private readonly errorSignal = signal<string | null>(null);
  private readonly permissionSignal = signal<PushPermission>(this.readPermission());
  private messageUnsubscribe: (() => void) | undefined;
  private messaging: Messaging | undefined;
  private serviceWorkerRegistration: ServiceWorkerRegistration | undefined;
  private token: string | undefined;
  private started = false;
  private readonly handleFocus = (): void => {
    void this.syncToken().catch(() => {
      this.errorSignal.set('No se pudo actualizar el token de notificaciones.');
    });
  };

  readonly notifications = this.notificationsSignal.asReadonly();
  readonly unreadCount = this.unreadCountSignal.asReadonly();
  readonly loading = this.loadingSignal.asReadonly();
  readonly error = this.errorSignal.asReadonly();
  readonly permission = this.permissionSignal.asReadonly();

  constructor(private readonly api: NotificationApiService) {}

  async start(): Promise<void> {
    await this.refresh();
    if (this.permissionSignal() !== 'granted') return;
    try {
      await this.activate();
    } catch {
      this.errorSignal.set('No se pudo activar la recepción de notificaciones en este navegador.');
    }
  }

  async enable(): Promise<void> {
    if (!(await this.isSupported())) {
      this.permissionSignal.set('unsupported');
      return;
    }

    const permission = await Notification.requestPermission();
    this.permissionSignal.set(permission);
    if (permission !== 'granted') return;
    try {
      await this.activate();
    } catch {
      this.errorSignal.set('No se pudo activar la recepción de notificaciones en este navegador.');
    }
  }

  async refresh(): Promise<void> {
    this.loadingSignal.set(true);
    try {
      const [listResponse, countResponse] = await Promise.all([
        firstValueFrom(this.api.list()),
        firstValueFrom(this.api.unreadCount()),
      ]);
      const existing = new Map(this.notificationsSignal().map((item) => [item.id, item]));
      for (const item of listResponse.data ?? []) existing.set(item.id, item);
      this.notificationsSignal.set([...existing.values()].sort((a, b) => b.created_at.localeCompare(a.created_at)));
      this.unreadCountSignal.set(countResponse.data?.count ?? 0);
      this.errorSignal.set(null);
    } catch {
      this.errorSignal.set('No se pudieron cargar las notificaciones.');
    } finally {
      this.loadingSignal.set(false);
    }
  }

  async markRead(item: NotificationItem): Promise<void> {
    if (item.read_at) return;
    const response = await firstValueFrom(this.api.markRead(item.id));
    const updated = response.data ?? { ...item, read_at: new Date().toISOString() };
    this.notificationsSignal.update((items) => items.map((current) => current.id === item.id ? updated : current));
    this.unreadCountSignal.update((count) => Math.max(0, count - 1));
  }

  async markAllRead(): Promise<void> {
    await firstValueFrom(this.api.markAllRead());
    const readAt = new Date().toISOString();
    this.notificationsSignal.update((items) => items.map((item) => ({ ...item, read_at: item.read_at ?? readAt })));
    this.unreadCountSignal.set(0);
  }

  async logout(): Promise<void> {
    if (this.token) {
      try {
        await firstValueFrom(this.api.unregisterToken(this.token));
      } catch {
        // The session is still cleared when token removal is unavailable.
      }
    }
    this.token = undefined;
    this.stop();
  }

  stop(): void {
    this.messageUnsubscribe?.();
    this.messageUnsubscribe = undefined;
    window.removeEventListener('focus', this.handleFocus);
    this.messaging = undefined;
    this.serviceWorkerRegistration = undefined;
    this.started = false;
    this.notificationsSignal.set([]);
    this.unreadCountSignal.set(0);
  }

  private async activate(): Promise<void> {
    if (this.started) return;
    this.started = true;
    try {
      const supported = await this.isSupported();
      if (!supported || !('serviceWorker' in navigator)) throw new Error('unsupported');

      const registration = await navigator.serviceWorker.register(this.serviceWorkerUrl(), { scope: '/' });
      this.serviceWorkerRegistration = registration;
      const app = getApps().length ? getApp() : initializeApp(environment.firebase);
      this.messaging = getMessaging(app);
      await this.syncToken();
      this.messageUnsubscribe = onMessage(this.messaging, () => {
        void this.refresh();
      });
      window.addEventListener('focus', this.handleFocus);
    } catch (error) {
      this.started = false;
      throw error;
    }
  }

  private async syncToken(): Promise<void> {
    if (!this.messaging || !this.serviceWorkerRegistration) return;
    const token = await getToken(this.messaging, {
      vapidKey: environment.firebaseVapidKey,
      serviceWorkerRegistration: this.serviceWorkerRegistration,
    });
    if (!token) throw new Error('missing token');
    if (token !== this.token) {
      await firstValueFrom(this.api.registerToken(token));
      this.token = token;
    }
  }

  private async isSupported(): Promise<boolean> {
    try {
      return await isSupported();
    } catch {
      return false;
    }
  }

  private serviceWorkerUrl(): string {
    const params = new URLSearchParams(environment.firebase);
    return `/firebase-messaging-sw.js?${params.toString()}`;
  }

  private readPermission(): PushPermission {
    return typeof Notification === 'undefined' ? 'unsupported' : Notification.permission;
  }
}
