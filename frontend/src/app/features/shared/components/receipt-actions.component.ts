import { Component, Input, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { toast } from '@spartan-ng/brain/sonner';

import { HlmButton } from '../../../components/button/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { ReceiptKind } from '../models/receipt.model';
import { ReceiptApiService } from '../services/receipt-api.service';

/** "Comprobante PDF" and "Enviar por correo" for one paid transaction. */
@Component({
  selector: 'app-receipt-actions',
  standalone: true,
  imports: [HlmButton],
  template: `
    <div class="flex flex-wrap gap-2">
      <button hlmBtn type="button" size="sm" variant="outline" [disabled]="busy()" (click)="download()">Comprobante PDF</button>
      @if (showResend) {
        <button hlmBtn type="button" size="sm" variant="ghost" [disabled]="busy()" (click)="resend()">Enviar por correo</button>
      }
    </div>
  `,
})
export class ReceiptActionsComponent {
  private readonly receipts = inject(ReceiptApiService);
  @Input({ required: true }) kind!: ReceiptKind;
  @Input({ required: true }) sourceId!: string;
  @Input() showResend = true;
  protected readonly busy = signal(false);

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
