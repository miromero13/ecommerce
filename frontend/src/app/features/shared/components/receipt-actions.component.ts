import { CommonModule } from '@angular/common';
import { Component, ElementRef, HostListener, Input, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { toast } from '@spartan-ng/brain/sonner';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideDownload, lucideMail, lucideMoreVertical } from '@ng-icons/lucide';

import { HlmButton } from '../../../components/button/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { ReceiptKind } from '../models/receipt.model';
import { ReceiptApiService } from '../services/receipt-api.service';

/** Dropdown menu with 3 dots for receipt actions: "Descargar" and "Enviar por correo". */
@Component({
  selector: 'app-receipt-actions',
  standalone: true,
  imports: [CommonModule, HlmButton, NgIcon],
  providers: [provideIcons({ lucideMoreVertical, lucideDownload, lucideMail })],
  template: `
    <div class="relative inline-block text-left">
      <button
        hlmBtn
        variant="ghost"
        size="sm"
        type="button"
        [disabled]="busy()"
        class="size-8 p-0 cursor-pointer text-muted-foreground hover:text-foreground hover:bg-muted rounded-md"
        (click)="toggleMenu($event)"
        aria-label="Acciones de comprobante"
      >
        <ng-icon name="lucideMoreVertical" class="size-4" />
      </button>

      @if (isOpen()) {
        <div
          class="absolute right-0 z-50 mt-1 min-w-44 origin-top-right rounded-xl border border-border bg-popover p-1 text-popover-foreground shadow-lg animate-in fade-in zoom-in-95 duration-150"
          (click)="$event.stopPropagation()"
        >
          <button
            type="button"
            class="flex w-full cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-left text-xs font-medium hover:bg-muted transition-colors text-foreground disabled:opacity-50"
            [disabled]="busy()"
            (click)="handleDownload()"
          >
            <ng-icon name="lucideDownload" class="size-3.5 text-muted-foreground" />
            <span>Descargar comprobante</span>
          </button>

          @if (showResend) {
            <button
              type="button"
              class="flex w-full cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-left text-xs font-medium hover:bg-muted transition-colors text-foreground disabled:opacity-50"
              [disabled]="busy()"
              (click)="handleResend()"
            >
              <ng-icon name="lucideMail" class="size-3.5 text-muted-foreground" />
              <span>Enviar por correo</span>
            </button>
          }
        </div>
      }
    </div>
  `,
})
export class ReceiptActionsComponent {
  private readonly receipts = inject(ReceiptApiService);
  private readonly elementRef = inject(ElementRef);

  @Input({ required: true }) kind!: ReceiptKind;
  @Input({ required: true }) sourceId!: string;
  @Input() showResend = true;

  protected readonly busy = signal(false);
  protected readonly isOpen = signal(false);

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.isOpen.set(false);
    }
  }

  protected toggleMenu(event: MouseEvent): void {
    event.stopPropagation();
    this.isOpen.update((v) => !v);
  }

  protected async handleDownload(): Promise<void> {
    this.isOpen.set(false);
    await this.download();
  }

  protected async handleResend(): Promise<void> {
    this.isOpen.set(false);
    await this.resend();
  }

  protected download(): Promise<void> {
    return this.run(() => this.receipts.downloadPdf(this.kind, this.sourceId), 'No se pudo descargar el comprobante.');
  }

  protected resend(): Promise<void> {
    return this.run(async () => {
      toast.success((await firstValueFrom(this.receipts.resend(this.kind, this.sourceId))).message);
    }, 'No se pudo enviar el comprobante.');
  }

  private async run(action: () => Promise<void>, fallback: string): Promise<void> {
    this.busy.set(true);
    try {
      await action();
    } catch (error) {
      toast.error(getErrorMessage(error, fallback));
    } finally {
      this.busy.set(false);
    }
  }
}
