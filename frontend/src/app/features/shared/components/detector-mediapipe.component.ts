import { CommonModule } from '@angular/common';
import { Component, ElementRef, OnDestroy, signal, viewChild } from '@angular/core';
import { FilesetResolver, ImageSegmenter } from '@mediapipe/tasks-vision';

import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';

const MODEL_URL =
  'https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite';
const WASM_URL = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm';
const CLOTHING_CATEGORY_INDEX = 4;

@Component({
  selector: 'app-detector-mediapipe',
  standalone: true,
  imports: [CommonModule, HlmButton, ...HlmCardImports],
  template: `
    <button hlmBtn type="button" variant="outline" (click)="openDetector()">
      Probar en vestidor virtual 3
    </button>

    @if (open()) {
      <section hlmCard class="mt-4 bg-white shadow-sm" aria-labelledby="detector-mediapipe-title">
        <div hlmCardHeader class="flex flex-row items-start justify-between gap-4">
          <div>
            <h2 hlmCardTitle id="detector-mediapipe-title">Vestidor virtual 3</h2>
            <p hlmCardDescription>Escanea tu polera cuando estés frente a la cámara.</p>
          </div>
          <button hlmBtn type="button" variant="ghost" (click)="closeDetector()" aria-label="Cerrar detector">Cerrar</button>
        </div>

        <div hlmCardContent class="space-y-3">
          <div class="relative aspect-[4/3] overflow-hidden rounded-xl bg-slate-950">
            <video #video class="h-full w-full object-cover [transform:scaleX(-1)]" autoplay muted playsinline></video>
            <canvas #canvas class="pointer-events-none absolute inset-0 h-full w-full [transform:scaleX(-1)]"></canvas>
          </div>
          <p class="text-sm text-slate-600" role="status" aria-live="polite">{{ status() }}</p>
          <button
            hlmBtn
            type="button"
            (click)="scanCurrentFrame()"
            [disabled]="!modelReady() || scanning()"
          >
            {{ scanning() ? 'Escaneando...' : 'Escanear ahora' }}
          </button>
          @if (error(); as message) {
            <p class="text-sm text-red-600" role="alert">{{ message }}</p>
          }
        </div>
      </section>
    }
  `,
})
export class DetectorMediapipeComponent implements OnDestroy {
  private readonly video = viewChild<ElementRef<HTMLVideoElement>>('video');
  private readonly canvas = viewChild<ElementRef<HTMLCanvasElement>>('canvas');
  protected readonly open = signal(false);
  protected readonly modelReady = signal(false);
  protected readonly scanning = signal(false);
  protected readonly status = signal('Listo para iniciar.');
  protected readonly error = signal<string | null>(null);

  private stream: MediaStream | null = null;
  private imageSegmenter: ImageSegmenter | null = null;
  private imageSegmenterPromise: Promise<ImageSegmenter> | null = null;
  private modelOwnerRunId = 0;
  private openTimer: number | null = null;
  private autoScanTimer: number | null = null;
  private runId = 0;
  private destroyed = false;

  protected openDetector(): void {
    if (this.open()) return;
    this.open.set(true);
    this.modelReady.set(false);
    this.error.set(null);
    this.status.set('Solicitando permiso de cámara...');
    this.openTimer = window.setTimeout(() => {
      this.openTimer = null;
      void this.start(this.runId);
    }, 0);
  }

  protected closeDetector(): void {
    this.open.set(false);
    this.cleanup();
    this.modelReady.set(false);
    this.error.set(null);
    this.status.set('Listo para iniciar.');
  }

  protected async scanCurrentFrame(): Promise<void> {
    const video = this.video()?.nativeElement;
    const segmenter = this.imageSegmenter;
    if (!segmenter || !video || this.scanning()) return;
    if (video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA || !video.videoWidth || !video.videoHeight) {
      this.error.set('La cámara todavía no está lista.');
      this.status.set('No se pudo escanear el frame actual.');
      return;
    }

    this.error.set(null);
    this.scanning.set(true);
    this.status.set('Escaneando...');

    try {
      await new Promise<void>((resolve, reject) => {
        segmenter.segment(video, (result) => {
          try {
            const categoryMask = result.categoryMask;
            if (!categoryMask) throw new Error('MediaPipe no devolvió una máscara de categorías.');

            this.drawClothingMask({
              data: new Uint8Array(categoryMask.getAsUint8Array()),
              width: categoryMask.width,
              height: categoryMask.height,
            });
            resolve();
          } catch (cause) {
            reject(cause);
          }
        });
      });
      this.status.set('Máscara guardada.');
    } catch (cause) {
      this.error.set(this.messageFor(cause));
      this.status.set('Error al escanear.');
    } finally {
      this.scanning.set(false);
    }
  }

  private async start(runId: number): Promise<void> {
    try {
      if (!navigator.mediaDevices?.getUserMedia) throw new Error('Este navegador no permite usar la cámara.');

      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      });
      if (runId !== this.runId || this.destroyed || !this.open()) {
        this.stream.getTracks().forEach((track) => track.stop());
        this.stream = null;
        return;
      }

      const video = this.video()?.nativeElement;
      if (!video) throw new Error('No se pudo preparar la vista de cámara.');
      video.srcObject = this.stream;
      await video.play();
      if (runId !== this.runId || this.destroyed || !this.open()) return;

      this.status.set('Cargando modelo...');
      const imageSegmenter = await this.loadSegmenter(runId);
      if (runId !== this.runId || this.destroyed || !this.open()) {
        if (this.modelOwnerRunId === runId) {
          imageSegmenter.close();
          this.imageSegmenterPromise = null;
        }
        return;
      }

      this.imageSegmenter = imageSegmenter;
      this.modelReady.set(true);
      this.status.set('Escaneo automático activo.');
      this.startAutoScan();
    } catch (cause) {
      if (runId !== this.runId || this.destroyed) return;
      this.error.set(this.messageFor(cause));
      this.status.set('Error de cámara o modelo.');
      this.cleanup();
    }
  }

  private loadSegmenter(runId: number): Promise<ImageSegmenter> {
    this.modelOwnerRunId = runId;
    if (this.imageSegmenter) return Promise.resolve(this.imageSegmenter);
    if (!this.imageSegmenterPromise) {
      this.imageSegmenterPromise = (async () => {
        const vision = await FilesetResolver.forVisionTasks(WASM_URL);
        return ImageSegmenter.createFromOptions(vision, {
          baseOptions: { modelAssetPath: MODEL_URL },
          runningMode: 'IMAGE',
          outputCategoryMask: true,
          outputConfidenceMasks: false,
        });
      })().catch((cause) => {
        this.imageSegmenterPromise = null;
        throw cause;
      });
    }
    return this.imageSegmenterPromise;
  }

  private startAutoScan(): void {
    this.stopAutoScan();
    void this.scanCurrentFrame();
    this.autoScanTimer = window.setInterval(() => void this.scanCurrentFrame(), 1500);
  }

  private stopAutoScan(): void {
    if (this.autoScanTimer !== null) window.clearInterval(this.autoScanTimer);
    this.autoScanTimer = null;
  }

  private drawClothingMask(mask: { data: Uint8Array; width: number; height: number }): void {
    const canvas = this.canvas()?.nativeElement;
    const video = this.video()?.nativeElement;
    const context = canvas?.getContext('2d');
    if (!canvas || !video || !context) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.clearRect(0, 0, canvas.width, canvas.height);

    const maskCanvas = document.createElement('canvas');
    maskCanvas.width = mask.width;
    maskCanvas.height = mask.height;
    const maskContext = maskCanvas.getContext('2d');
    if (!maskContext) return;

    const imageData = new ImageData(mask.width, mask.height);
    const pixelCount = Math.min(mask.data.length, mask.width * mask.height);
    for (let index = 0; index < pixelCount; index += 1) {
      if (mask.data[index] !== CLOTHING_CATEGORY_INDEX) continue;
      const pixel = index * 4;
      imageData.data[pixel] = 34;
      imageData.data[pixel + 1] = 197;
      imageData.data[pixel + 2] = 94;
      imageData.data[pixel + 3] = 190;
    }

    maskContext.putImageData(imageData, 0, 0);
    context.drawImage(maskCanvas, 0, 0, canvas.width, canvas.height);
  }

  private cleanup(): void {
    this.runId += 1;
    if (this.openTimer !== null) window.clearTimeout(this.openTimer);
    this.openTimer = null;
    this.stopAutoScan();
    this.scanning.set(false);
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;

    const video = this.video()?.nativeElement;
    if (video) video.srcObject = null;
    const canvas = this.canvas()?.nativeElement;
    canvas?.getContext('2d')?.clearRect(0, 0, canvas.width, canvas.height);

    if (this.imageSegmenter) {
      this.imageSegmenter.close();
      this.imageSegmenter = null;
      this.imageSegmenterPromise = null;
    }
  }

  private messageFor(cause: unknown): string {
    if (cause instanceof DOMException && cause.name === 'NotAllowedError') {
      return 'Se denegó el permiso de cámara. Habilítalo desde la configuración del navegador.';
    }
    if (cause instanceof DOMException && cause.name === 'NotFoundError') return 'No se encontró una cámara disponible.';
    return cause instanceof Error ? cause.message : 'No se pudo iniciar el vestidor virtual.';
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    this.cleanup();
  }
}
