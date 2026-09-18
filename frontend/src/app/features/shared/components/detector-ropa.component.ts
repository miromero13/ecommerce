import { CommonModule } from '@angular/common';
import { Component, ElementRef, OnDestroy, signal, viewChild } from '@angular/core';
import type { RawImage as RawImageType } from '@xenova/transformers';

import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';

type Segmentation = { label?: string; mask: RawImageType };
type Segmenter = (image: RawImageType) => Promise<Segmentation[]>;

@Component({
  selector: 'app-detector-ropa',
  standalone: true,
  imports: [CommonModule, HlmButton, ...HlmCardImports],
  template: `
    <button hlmBtn type="button" variant="outline" (click)="openDetector()">
      Probar en vestidor virtual 2
    </button>

    @if (open()) {
      <section hlmCard class="mt-4 bg-white shadow-sm" aria-labelledby="detector-ropa-title">
        <div hlmCardHeader class="flex flex-row items-start justify-between gap-4">
          <div>
            <h2 hlmCardTitle id="detector-ropa-title">Vestidor virtual 2</h2>
            <p hlmCardDescription>La cámara detectará la prenda en tiempo real.</p>
          </div>
          <button hlmBtn type="button" variant="ghost" (click)="closeDetector()" aria-label="Cerrar detector">Cerrar</button>
        </div>

        <div hlmCardContent class="space-y-3">
          <div class="relative aspect-video overflow-hidden rounded-xl bg-slate-950">
            <video #video class="h-full w-full object-cover [transform:scaleX(-1)]" autoplay muted playsinline></video>
            <canvas #canvas class="pointer-events-none absolute inset-0 h-full w-full [transform:scaleX(-1)]"></canvas>
          </div>
          <p class="text-sm text-slate-600" role="status">{{ status() }}</p>
          @if (error(); as message) {
            <p class="text-sm text-red-600">{{ message }}</p>
          }
        </div>
      </section>
    }
  `,
})
export class DetectorRopaComponent implements OnDestroy {
  private readonly video = viewChild<ElementRef<HTMLVideoElement>>('video');
  private readonly canvas = viewChild<ElementRef<HTMLCanvasElement>>('canvas');
  protected readonly open = signal(false);
  protected readonly status = signal('Listo para iniciar.');
  protected readonly error = signal<string | null>(null);
  private stream: MediaStream | null = null;
  private segmenter: Segmenter | null = null;
  private animationFrame: number | null = null;
  private lastInference = 0;
  private lastMaskAt = 0;
  private runId = 0;
  private destroyed = false;

  protected openDetector(): void {
    if (this.open()) return;
    this.open.set(true);
    this.error.set(null);
    this.status.set('Solicitando permiso para usar la cámara...');
    window.setTimeout(() => void this.start(this.runId), 0);
  }

  protected closeDetector(): void {
    this.open.set(false);
    this.cleanup();
    this.status.set('Listo para iniciar.');
  }

  private async start(runId: number): Promise<void> {
    try {
      if (!navigator.mediaDevices?.getUserMedia) throw new Error('Este navegador no permite usar la cámara.');

      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      });
      if (runId !== this.runId || this.destroyed) {
        this.stream.getTracks().forEach((track) => track.stop());
        this.stream = null;
        return;
      }

      const video = this.video()?.nativeElement;
      if (!video) throw new Error('No se pudo preparar la vista de cámara.');
      video.srcObject = this.stream;
      await video.play();
      this.status.set('Cargando detector de prendas...');
      await this.loadSegmenter();
      if (runId !== this.runId || this.destroyed) {
        this.cleanup();
        return;
      }

      this.status.set('Analizando tu cuerpo y tu ropa...');
      this.animationFrame = requestAnimationFrame((time) => this.detect(time, runId));
    } catch (cause) {
      if (runId !== this.runId || this.destroyed) return;
      this.error.set(this.messageFor(cause));
      this.status.set('El detector no está disponible.');
      this.cleanup();
    }
  }

  private async loadSegmenter(): Promise<void> {
    if (this.segmenter) return;
    const transformers = await this.loadTransformers();
    transformers.env.allowLocalModels = false;
    const webGpuAvailable = 'gpu' in navigator;
    if (webGpuAvailable) {
      const providers = (transformers.env as { backends?: { onnx?: { executionProviders?: string[] } } }).backends?.onnx?.executionProviders;
      if (providers && !providers.includes('webgpu')) providers.unshift('webgpu');
    }
    const device = webGpuAvailable ? 'webgpu' : 'wasm';
    const { pipeline } = transformers;
    this.segmenter = (await pipeline(
      'image-segmentation',
      'Xenova/segformer_b0_clothes',
      { device } as never,
    )) as unknown as Segmenter;
  }

  private async detect(time: number, runId: number): Promise<void> {
    if (runId !== this.runId || this.destroyed || !this.open()) return;
    const video = this.video()?.nativeElement;
    const canvas = this.canvas()?.nativeElement;
    if (!video || !canvas || video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
      this.animationFrame = requestAnimationFrame((next) => this.detect(next, runId));
      return;
    }

    if (time - this.lastInference >= 300 && this.segmenter) {
      this.lastInference = time;
      try {
        const width = video.videoWidth;
        const height = video.videoHeight;
        if (canvas.width !== width || canvas.height !== height) {
          canvas.width = width;
          canvas.height = height;
        }
        const frame = document.createElement('canvas');
        const scale = Math.min(1, 256 / width);
        const frameWidth = Math.max(1, Math.round(width * scale));
        const frameHeight = Math.max(1, Math.round(height * scale));
        frame.width = frameWidth;
        frame.height = frameHeight;
        frame.getContext('2d')?.drawImage(video, 0, 0, frameWidth, frameHeight);
        const frameData = frame.getContext('2d')?.getImageData(0, 0, frameWidth, frameHeight);
        if (frameData) {
          const { RawImage } = await this.loadTransformers();
          const results = await this.segmenter(new RawImage(frameData.data, frameWidth, frameHeight, 4));
          this.drawMasks(canvas, results, time);
        }
      } catch (cause) {
        this.error.set(this.messageFor(cause));
      }
    }

    this.animationFrame = requestAnimationFrame((next) => this.detect(next, runId));
  }

  private loadTransformers(): Promise<typeof import('@xenova/transformers')> {
    // @xenova/transformers 2.17 ships Node-only optional imports that Angular's browser bundler cannot resolve.
    // Load the same package through an ESM browser bundle while keeping the npm dependency pinned locally.
    const load = new Function('specifier', 'return import(specifier)') as (specifier: string) => Promise<typeof import('@xenova/transformers')>;
    return load('https://esm.sh/@xenova/transformers@2.17.2?bundle');
  }

  private drawMasks(canvas: HTMLCanvasElement, results: Segmentation[], time: number): void {
    const context = canvas.getContext('2d');
    if (!context) return;
    const clothing = results.filter(({ label }) => /upper-clothes|lower-clothes|clothes|shirt|top|jacket|coat|dress|skirt|pants|shorts|jeans/i.test(label ?? ''));
    if (!clothing.length) {
      if (time - this.lastMaskAt > 800) context.clearRect(0, 0, canvas.width, canvas.height);
      return;
    }

    context.clearRect(0, 0, canvas.width, canvas.height);
    this.lastMaskAt = time;
    for (const { mask } of clothing) {
      const image = new ImageData(mask.width, mask.height);
      for (let index = 0; index < mask.data.length; index++) {
        if (mask.data[index] > 0) {
          const pixel = index * 4;
          image.data[pixel] = 255;
          image.data[pixel + 1] = 0;
          image.data[pixel + 2] = 0;
          image.data[pixel + 3] = 220;
        }
      }
      const maskCanvas = document.createElement('canvas');
      maskCanvas.width = mask.width;
      maskCanvas.height = mask.height;
      maskCanvas.getContext('2d')?.putImageData(image, 0, 0);
      context.drawImage(maskCanvas, 0, 0, canvas.width, canvas.height);
    }
  }

  private cleanup(): void {
    this.runId += 1;
    if (this.animationFrame !== null) cancelAnimationFrame(this.animationFrame);
    this.animationFrame = null;
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;
    const video = this.video()?.nativeElement;
    if (video) video.srcObject = null;
    const canvas = this.canvas()?.nativeElement;
    canvas?.getContext('2d')?.clearRect(0, 0, canvas.width, canvas.height);
    this.lastMaskAt = 0;
  }

  private messageFor(cause: unknown): string {
    if (cause instanceof DOMException && cause.name === 'NotAllowedError') return 'Se denegó el permiso de cámara. Puedes habilitarlo desde la configuración del navegador.';
    if (cause instanceof DOMException && cause.name === 'NotFoundError') return 'No se encontró una cámara disponible.';
    return cause instanceof Error ? cause.message : 'No se pudo iniciar el detector.';
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    this.cleanup();
  }
}
