import { Component, ElementRef, HostListener, input, signal, viewChild } from '@angular/core';

import { HlmButton } from '../../../components/button/src';
import { environment } from '../../../../environments/environment';

@Component({
  selector: 'app-virtual-try-on',
  standalone: true,
  imports: [HlmButton],
  templateUrl: './virtual-try-on.component.html',
})
export class VirtualTryOnComponent {
  readonly productName = input('Producto');
  readonly garmentImageUrl = input<string | null>(null);
  protected readonly tryOnFrame = viewChild<ElementRef<HTMLIFrameElement>>('tryOnFrame');
  protected readonly open = signal(false);

  protected openModal(): void {
    this.open.set(true);
  }

  protected closeModal(): void {
    this.open.set(false);
  }

  @HostListener('window:message', ['$event'])
  protected handleMessage(event: MessageEvent): void {
    const frame = this.tryOnFrame()?.nativeElement;

    if (
      event.origin !== window.location.origin ||
      event.source !== frame?.contentWindow ||
      event.data?.type !== 'decart-try-on-expired'
    ) {
      return;
    }

    this.closeModal();
  }

  protected sendConfiguration(): void {
    this.tryOnFrame()?.nativeElement.contentWindow?.postMessage(
      {
        type: 'decart-try-on-config',
        apiKey: environment.decartApiKey,
        garmentImageUrl: this.garmentImageUrl(),
        productName: this.productName(),
      },
      window.location.origin,
    );
  }
}
