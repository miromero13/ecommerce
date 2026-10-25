import { Component, ElementRef, OnDestroy, inject, input, signal, viewChild } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { HlmButton } from '../../../components/button/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { CatalogApiService } from '../services/catalog-api.service';

export interface TryOnVariantOption {
  id: string;
  label: string;
  imageUrl: string | null;
}

const MAX_SIDE = 1536;

/** Shrinks and re-encodes as JPEG: phone photos often exceed the 8 MB API limit. */
async function toJpeg(source: CanvasImageSource, width: number, height: number): Promise<Blob> {
  const scale = Math.min(1, MAX_SIDE / Math.max(width, height));
  const canvas = document.createElement('canvas');
  canvas.width = Math.round(width * scale);
  canvas.height = Math.round(height * scale);
  canvas.getContext('2d')!.drawImage(source, 0, 0, canvas.width, canvas.height);
  return new Promise((resolve, reject) =>
    canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error('No se pudo procesar la foto.'))), 'image/jpeg', 0.9),
  );
}

@Component({
  selector: 'app-photo-try-on',
  standalone: true,
  imports: [HlmButton],
  templateUrl: './photo-try-on.component.html',
})
export class PhotoTryOnComponent implements OnDestroy {
  private readonly catalogApi = inject(CatalogApiService);

  readonly productName = input('Producto');
  readonly variants = input<TryOnVariantOption[]>([]);
  readonly initialVariantId = input<string | null>(null);

  protected readonly video = viewChild<ElementRef<HTMLVideoElement>>('video');
  protected readonly open = signal(false);
  protected readonly cameraOn = signal(false);
  protected readonly photoUrl = signal<string | null>(null);
  protected readonly variantId = signal<string | null>(null);
  protected readonly generating = signal(false);
  protected readonly resultUrl = signal<string | null>(null);
  protected readonly error = signal<string | null>(null);

  private photo: Blob | null = null;
  private stream: MediaStream | null = null;

  protected openModal(): void {
    this.variantId.set(this.initialVariantId() ?? this.variants()[0]?.id ?? null);
    this.error.set(null);
    this.open.set(true);
  }

  protected closeModal(): void {
    this.stopCamera();
    this.setPhoto(null);
    this.resultUrl.set(null);
    this.open.set(false);
  }

  ngOnDestroy(): void {
    this.closeModal();
  }

  protected async onFile(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      this.error.set('Elegí un archivo de imagen (JPG, PNG o WEBP).');
      return;
    }
    try {
      const bitmap = await createImageBitmap(file);
      this.setPhoto(await toJpeg(bitmap, bitmap.width, bitmap.height));
      bitmap.close();
    } catch {
      this.error.set('No se pudo leer la foto. Probá con otra imagen.');
    }
  }

  protected async startCamera(): Promise<void> {
    this.error.set(null);
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
      this.cameraOn.set(true);
      // The <video> exists only after cameraOn renders it.
      setTimeout(() => {
        const video = this.video()?.nativeElement;
        if (video && this.stream) {
          video.srcObject = this.stream;
          void video.play();
        }
      });
    } catch {
      this.error.set('No se pudo acceder a la cámara. Revisá los permisos del navegador o subí una foto.');
    }
  }

  protected async capture(): Promise<void> {
    const video = this.video()?.nativeElement;
    if (!video || !video.videoWidth) return;
    this.setPhoto(await toJpeg(video, video.videoWidth, video.videoHeight));
    this.stopCamera();
  }

  protected stopCamera(): void {
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;
    this.cameraOn.set(false);
  }

  protected retake(): void {
    this.setPhoto(null);
    this.resultUrl.set(null);
  }

  protected async generate(): Promise<void> {
    const variantId = this.variantId();
    if (!this.photo || !variantId || this.generating()) return;
    this.generating.set(true);
    this.error.set(null);
    this.resultUrl.set(null);
    try {
      const res = await firstValueFrom(this.catalogApi.tryOn(variantId, this.photo));
      this.resultUrl.set(res.data?.image_data_url ?? null);
    } catch (err) {
      this.error.set(getErrorMessage(err, 'No se pudo generar la prueba virtual.'));
    } finally {
      this.generating.set(false);
    }
  }

  protected selectedLabel(): string {
    return this.variants().find((option) => option.id === this.variantId())?.label ?? '';
  }

  private setPhoto(photo: Blob | null): void {
    const previous = this.photoUrl();
    if (previous) URL.revokeObjectURL(previous);
    this.photo = photo;
    this.photoUrl.set(photo ? URL.createObjectURL(photo) : null);
    if (photo) this.error.set(null);
  }
}
