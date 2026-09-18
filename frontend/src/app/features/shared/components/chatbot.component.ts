import { CommonModule } from '@angular/common';
import { Component, DestroyRef, ElementRef, ViewChild, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideEye, lucideMessageCircle, lucideRefreshCw, lucideSend, lucideTrash2, lucideX } from '@ng-icons/lucide';

import { ChatbotMessage, ChatbotApiService } from '../services/chatbot-api.service';
import { ChatbotUiService } from '../services/chatbot-ui.service';

type UiMessage = ChatbotMessage & { state?: 'sending' | 'error' };

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [CommonModule, NgIcon],
  providers: [provideIcons({ lucideEye, lucideMessageCircle, lucideRefreshCw, lucideSend, lucideTrash2, lucideX })],
  templateUrl: './chatbot.component.html',
})
export class ChatbotComponent {
  private readonly chatbotApi = inject(ChatbotApiService);
  private readonly chatbotUi = inject(ChatbotUiService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly router = inject(Router);

  @ViewChild('messagesViewport') private messagesViewport?: ElementRef<HTMLElement>;
  @ViewChild('messageInput') private messageInput?: ElementRef<HTMLTextAreaElement>;

  protected readonly open = signal(false);
  protected readonly loading = signal(false);
  protected readonly sending = signal(false);
  protected readonly resetting = signal(false);
  protected readonly deleteConfirmOpen = signal(false);
  protected readonly messages = signal<UiMessage[]>([]);
  protected readonly error = signal<string | null>(null);
  protected readonly draft = signal('');

  constructor() {
    this.chatbotUi.closeRequested$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        this.open.set(false);
        this.deleteConfirmOpen.set(false);
      });
  }

  protected openChat(): void {
    this.open.set(true);
    this.error.set(null);
    void this.loadMessages();
    setTimeout(() => this.messageInput?.nativeElement.focus());
  }

  protected closeChat(): void {
    if (!this.sending() && !this.resetting()) this.open.set(false);
  }

  protected onDraftInput(event: Event): void {
    this.draft.set((event.target as HTMLTextAreaElement).value);
  }

  protected onInputKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void this.sendMessage();
    }
  }

  protected async sendMessage(content = this.draft().trim()): Promise<void> {
    if (!content || this.sending() || this.resetting()) return;

    const optimistic: UiMessage = {
      id: `pending-${Date.now()}`,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
      metadata: null,
      state: 'sending',
    };
    this.messages.update((messages) => [...messages, optimistic]);
    this.draft.set('');
    this.error.set(null);
    this.sending.set(true);
    this.scrollToLatest();

    try {
      await firstValueFrom(this.chatbotApi.sendMessage(content));
      const refreshed = await this.loadMessages();
      if (!refreshed) this.markMessageFailed(optimistic.id);
    } catch {
      this.markMessageFailed(optimistic.id);
      this.error.set('No se pudo enviar el mensaje. Revisá tu conexión e intentá de nuevo.');
    } finally {
      this.sending.set(false);
      this.scrollToLatest();
    }
  }

  protected retry(message: UiMessage): void {
    this.messages.update((messages) => messages.filter((item) => item.id !== message.id));
    void this.sendMessage(message.content);
  }

  protected openRecommendation(productId: string): void {
    this.chatbotUi.requestClose();
    void this.router.navigate(['/app/cliente/products', productId], { queryParams: { from: 'catalog' } });
  }

  protected async resetConversation(): Promise<void> {
    if (this.resetting() || this.sending()) return;
    this.deleteConfirmOpen.set(true);
  }

  protected cancelDelete(): void {
    if (!this.resetting()) this.deleteConfirmOpen.set(false);
  }

  protected async confirmDelete(): Promise<void> {
    if (this.resetting() || this.sending()) return;

    this.resetting.set(true);
    this.error.set(null);
    try {
      await firstValueFrom(this.chatbotApi.resetConversation());
      this.messages.set([]);
      this.deleteConfirmOpen.set(false);
    } catch {
      this.error.set('No se pudo borrar la conversación. Intentá de nuevo.');
    } finally {
      this.resetting.set(false);
      this.scrollToLatest();
    }
  }

  private async loadMessages(): Promise<boolean> {
    this.loading.set(true);
    try {
      const response = await firstValueFrom(this.chatbotApi.getMessages());
      this.messages.set([...(response.data ?? [])].sort((a, b) => a.created_at.localeCompare(b.created_at)));
      this.error.set(null);
      this.scrollToLatest();
      return true;
    } catch {
      this.error.set('No se pudo cargar la conversación. Intentá de nuevo.');
      this.scrollToLatest();
      return false;
    } finally {
      this.loading.set(false);
    }
  }

  private markMessageFailed(id: string): void {
    this.messages.update((messages) => messages.map((message) => message.id === id ? { ...message, state: 'error' } : message));
  }

  private scrollToLatest(): void {
    setTimeout(() => {
      const viewport = this.messagesViewport?.nativeElement;
      if (viewport) viewport.scrollTop = viewport.scrollHeight;
    });
  }
}
