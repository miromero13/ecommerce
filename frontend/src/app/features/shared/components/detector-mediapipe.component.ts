import { CommonModule } from '@angular/common';
import { Component, computed, ElementRef, inject, Input, NgZone, OnChanges, OnDestroy, signal, SimpleChanges, viewChild } from '@angular/core';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { CatalogoPrendaService } from '../services/catalogo-prenda.service';
import {
  DEFAULT_FIT, DEFAULT_PROFILE, GARMENT_CATEGORIES, SLEEVE_KINDS, calibrationHandles, defaultFit, loadGarmentProfile, saveGarmentProfile, GarmentCalibrationEditor, GarmentTryOnEngine,
  prepareGarmentTexture, type FitKey, type GarmentFit, type GarmentProfile,
} from './garment-overlay.renderer';

@Component({
  selector: 'app-detector-mediapipe',
  standalone: true,
  imports: [CommonModule, HlmButton, ...HlmCardImports],
  template: `
    <button hlmBtn type="button" variant="outline" (click)="openDetector()">Probar en vestidor virtual 3</button>
    @if (open()) {
      <section hlmCard class="mt-4 bg-white shadow-sm">
        <div hlmCardHeader class="flex flex-row items-start justify-between gap-4">
          <div>
            <h2 hlmCardTitle>Vestidor virtual 3</h2>
            <p hlmCardDescription>Vista frontal para poleras, blusas y vestidos.</p>
          </div>
          <button hlmBtn type="button" variant="ghost" (click)="closeDetector()">Cerrar</button>
        </div>
        <div hlmCardContent class="space-y-4">
          <div class="grid gap-3 sm:grid-cols-2">
            <label class="block text-sm">Tipo de prenda
              <select class="mt-1 block w-full rounded-md border bg-white p-2" [value]="profile().category" (change)="changeProfile('category',$event)">
                @for (kind of categories; track kind.value) { <option [value]="kind.value">{{ kind.label }}</option> }
              </select>
            </label>
            <label class="block text-sm">Mangas
              <select class="mt-1 block w-full rounded-md border bg-white p-2" [value]="profile().sleeves" (change)="changeProfile('sleeves',$event)">
                @for (kind of sleeveKinds; track kind.value) { <option [value]="kind.value">{{ kind.label }}</option> }
              </select>
            </label>
          </div>
          @if (profile().category === 'dress') {
            <p class="text-sm text-slate-600">Muestra al menos hasta las rodillas. Para vestidos largos, muestra también los tobillos. Ajusta el largo y el ancho de la falda.</p>
          }
          @if (profile().sleeves !== 'long') {
            <p class="text-xs text-slate-600">Para probar manga corta o tirantes, usa ropa que deje los brazos descubiertos: esta vista no elimina las mangas de tu ropa actual.</p>
          }
          <!-- The video is an input only. Camera and garment share one visible canvas. -->
          <video #video autoplay muted playsinline aria-hidden="true"
            style="position:absolute;width:1px;height:1px;opacity:0;pointer-events:none"></video>
          <canvas #canvas width="640" height="480" role="img" aria-label="Vista de cámara con la prenda"
            class="block w-full rounded-xl bg-slate-950" style="height:auto"></canvas>
          <p class="text-sm text-slate-600" role="status" aria-live="polite">{{ status() }}</p>
          @if (error(); as message) { <p class="text-sm text-red-600" role="alert">{{ message }}</p> }
          @if (garmentError(); as message) { <p class="text-sm text-red-600" role="alert">{{ message }}</p> }
          @if (warning(); as message) { <p class="text-sm text-amber-700">{{ message }}</p> }

          <details [open]="!calibrated()" class="rounded-lg border p-3" [hidden]="!assetReady()">
            <summary class="cursor-pointer font-medium">Calibrar la foto de esta prenda</summary>
            <div class="mt-3 space-y-3">
              <p class="text-sm text-slate-600">
                Marca los {{ points().length }} puntos en la foto. Izquierda y derecha se refieren a la imagen.
                Selecciona un punto y toca su posición; también puedes arrastrar los círculos.
                La malla debe seguir las costuras y cubrir la prenda sin cruzarse.
              </p>
              <label class="block text-sm">
                Punto que vas a colocar
                <select class="mt-1 block w-full rounded-md border bg-white p-2"
                  [value]="selectedPoint()" (change)="selectPoint($event)">
                  @for (point of points(); track point.id) { <option [value]="point.id">{{ point.label }}</option> }
                </select>
              </label>
              <canvas #calibration role="img" aria-label="Foto de la prenda con puntos de calibración"
                class="block w-full rounded-lg border" style="height:auto;max-width:520px;touch-action:none"></canvas>
              <div class="flex flex-wrap gap-2">
                <button hlmBtn type="button" variant="outline" (click)="nextPoint()">Siguiente punto</button>
                <button hlmBtn type="button" (click)="saveCalibration()">Guardar calibración</button>
                <button hlmBtn type="button" variant="ghost" (click)="resetCalibration()">Restablecer puntos</button>
              </div>
              @if (calibrationMessage()) { <p class="text-sm" role="status">{{ calibrationMessage() }}</p> }
            </div>
          </details>

          <label class="flex items-center gap-2 text-sm font-medium">
            <input type="checkbox" [checked]="coverage()" (change)="toggleCoverage($event)" />
            Ajustar y cubrir la ropa detectada
          </label>
          <p class="text-xs text-slate-600">
            La cobertura extiende la textura de la prenda sobre los huecos. Si alcanza tu pantalón,
            baja el valor de «Límite inferior del relleno». La línea naranja muestra ese límite
            al activar «Mostrar malla».
          </p>
          <div class="grid gap-3 sm:grid-cols-2">
            @for (control of controls(); track control.key) {
              <label class="block text-sm">
                {{ control.label }}: {{ fit()[control.key] | number:'1.2-2' }}
                <input type="range" class="mt-1 block w-full" [min]="control.min" [max]="control.max"
                  step="0.01" [value]="fit()[control.key]" (input)="setFit(control.key, $event)" />
              </label>
            }
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <button hlmBtn type="button" variant="outline" (click)="recenter()">Reiniciar seguimiento</button>
            <button hlmBtn type="button" variant="ghost" (click)="resetFit()">Restablecer ajuste</button>
            <label class="flex items-center gap-2 text-sm">
              <input type="checkbox" [checked]="debug()" (change)="toggleDebug($event)" /> Mostrar malla
            </label>
          </div>
          <p class="text-xs text-slate-500">
            Mantén visible la zona del cuerpo que cubre la prenda. El relleno puede estirar el estampado
            y depende de detectar bien la ropa. No calcula la talla real.
          </p>
        </div>
      </section>
    }
  `,
})
export class DetectorMediapipeComponent implements OnChanges, OnDestroy {
  @Input() garmentImageUrl: string | null = null;
  private readonly video = viewChild<ElementRef<HTMLVideoElement>>('video');
  private readonly canvas = viewChild<ElementRef<HTMLCanvasElement>>('canvas');
  private readonly calibration = viewChild<ElementRef<HTMLCanvasElement>>('calibration');
  private readonly catalogoPrenda = inject(CatalogoPrendaService);
  private readonly zone = inject(NgZone);
  protected readonly open = signal(false);
  protected readonly status = signal('Listo para iniciar.');
  protected readonly error = signal<string | null>(null);
  protected readonly garmentError = signal<string | null>(null);
  protected readonly warning = signal<string | null>(null);
  protected readonly calibrated = signal(false);
  protected readonly assetReady = signal(false);
  protected readonly selectedPoint = signal(0);
  protected readonly calibrationMessage = signal('');
  protected readonly debug = signal(false);
  protected readonly coverage = signal(true);
  protected readonly fit = signal<GarmentFit>({ ...DEFAULT_FIT });
  protected readonly profile = signal<GarmentProfile>({ ...DEFAULT_PROFILE });
  protected readonly categories = GARMENT_CATEGORIES;
  protected readonly sleeveKinds = SLEEVE_KINDS;
  protected readonly points = computed(() => calibrationHandles(this.profile()));
  protected readonly controls = computed<Array<{ key: FitKey; label: string; min: number; max: number }>>(() => {
    const profile = this.profile(), dress = profile.category === 'dress';
    const items: Array<{ key: FitKey; label: string; min: number; max: number }> = [
      { key: 'width', label: 'Ancho del torso', min: .85, max: 1.7 },
      { key: 'length', label: dress ? 'Altura de cintura' : 'Largo del torso', min: .75, max: dress ? 1.15 : 1.4 },
    ];
    if (profile.sleeves !== 'none') items.push(
      { key: 'sleeveWidth', label: 'Ancho de mangas', min: .8, max: 2.5 },
      { key: 'sleeve', label: 'Largo de mangas', min: profile.sleeves === 'short' ? .5 : .7, max: profile.sleeves === 'short' ? 1.45 : 1.2 },
    );
    if (profile.sleeves === 'long') items.push({ key: 'cuffWidth', label: 'Ancho de puños', min: .8, max: 2.3 });
    if (dress) items.push({ key: 'skirtLength', label: 'Largo de falda (1 = rodilla)', min: .6, max: 1.65 }, { key: 'skirtWidth', label: 'Ancho de falda', min: .65, max: 2.6 });
    items.push({ key: 'offsetY', label: 'Posición vertical', min: -.15, max: .15 },
      { key: 'coverageHem', label: 'Límite inferior del relleno', min: .6, max: dress ? 3.8 : 1.3 },
      { key: 'coverageMargin', label: 'Margen de cobertura', min: 0, max: .12 });
    return items;
  });
  private engine: GarmentTryOnEngine | null = null;
  private editor: GarmentCalibrationEditor | null = null;
  private texture: HTMLCanvasElement | null = null;
  private timer: ReturnType<typeof setTimeout> | null = null;
  private garmentRequest = 0;
  private destroyed = false;

  ngOnChanges(changes: SimpleChanges): void {
    if (!('garmentImageUrl' in changes)) return;
    const request = ++this.garmentRequest;
    this.texture = null; this.assetReady.set(false); this.calibrated.set(false);
    this.garmentError.set(null); this.calibrationMessage.set('');
    this.editor?.destroy(); this.editor = null; this.engine?.setGarment(null);
    const url = this.garmentImageUrl?.trim();
    this.profile.set(loadGarmentProfile(url ?? '')); this.fit.set(defaultFit(this.profile()));
    if (this.engine) { this.engine.profile = { ...this.profile() }; this.engine.fit = { ...this.fit() }; }
    if (url) void this.prepareGarment(url, request);
  }

  private async prepareGarment(url: string, request: number): Promise<void> {
    try {
      const dataUrl = await this.catalogoPrenda.prepare(url);
      if (request !== this.garmentRequest || this.destroyed) return;
      const image = await new Promise<HTMLImageElement>((resolve, reject) => {
        const img = new Image(); img.crossOrigin = 'anonymous';
        img.onload = () => resolve(img); img.onerror = () => reject(new Error('No se pudo cargar la imagen preparada de la prenda.'));
        img.src = dataUrl;
      });
      if (request !== this.garmentRequest || this.destroyed) return;
      this.texture = prepareGarmentTexture(image); this.assetReady.set(true); this.bindGarment();
    } catch (error) {
      if (request === this.garmentRequest && !this.destroyed) this.garmentError.set(this.messageFor(error));
    }
  }

  protected openDetector(): void {
    if (this.open() || this.destroyed) return;
    this.open.set(true); this.error.set(null); this.warning.set(null); this.status.set('Preparando cámara...');
    this.timer = setTimeout(() => { this.timer = null; void this.start(); }, 0);
  }

  private async start(): Promise<void> {
    const video = this.video()?.nativeElement, canvas = this.canvas()?.nativeElement;
    if (!this.open() || this.destroyed || !video || !canvas) return;
    const engine = new GarmentTryOnEngine({
      status: text => this.zone.run(() => { if (this.engine === engine) this.status.set(text); }),
      warning: text => this.zone.run(() => { if (this.engine === engine) this.warning.set(text); }),
      stopped: () => this.zone.run(() => { if (this.engine === engine) this.closeDetector(); }),
    });
    this.engine = engine; engine.fit = { ...this.fit() }; engine.debug = this.debug(); engine.coverage = this.coverage(); engine.profile = { ...this.profile() };
    this.bindGarment();
    try { await this.zone.runOutsideAngular(() => engine.start(video, canvas)); }
    catch (error) { if (this.engine === engine && !this.destroyed) { this.error.set(this.messageFor(error)); this.status.set('No se pudo iniciar. Cierra y vuelve a abrir el vestidor.'); } }
  }

  private bindGarment(): void {
    const canvas = this.calibration()?.nativeElement, engine = this.engine, texture = this.texture;
    if (!canvas || !engine || !texture) return;
    this.editor?.destroy(); this.calibrated.set(false); this.selectedPoint.set(0);
    engine.profile = { ...this.profile() }; engine.setGarment(texture);
    this.editor = new GarmentCalibrationEditor(canvas, texture, this.garmentImageUrl ?? '',
      index => this.zone.run(() => this.selectedPoint.set(index)),
      points => this.zone.run(() => { engine.setCalibration(points); this.calibrated.set(true); }),
      this.profile(),
    );
  }
  protected selectPoint(event: Event): void { this.editor?.select(Number((event.target as HTMLSelectElement).value)); }
  protected nextPoint(): void {
    const points = this.points(), current = points.findIndex(p => p.id === this.selectedPoint());
    this.editor?.select(points[(current + 1) % points.length].id);
  }
  protected changeProfile(key: 'category' | 'sleeves', event: Event): void {
    const value = (event.target as HTMLSelectElement).value;
    if (!(key === 'category' ? this.categories : this.sleeveKinds).some(p => p.value === value)) return;
    this.profile.update(profile => ({ ...profile, [key]: value }));
    saveGarmentProfile(this.garmentImageUrl ?? '', this.profile());
    this.fit.set(defaultFit(this.profile())); this.calibrated.set(false); this.calibrationMessage.set('Ajusta y guarda los puntos correspondientes a este tipo de prenda.');
    if (this.engine) { this.engine.profile = { ...this.profile() }; this.engine.fit = { ...this.fit() }; this.engine.recalibrate(); }
    this.bindGarment();
  }
  protected saveCalibration(): void {
    try { this.calibrationMessage.set(this.editor?.save() ?? 'Espera a que se cargue la prenda.'); }
    catch (error) { this.calibrationMessage.set(this.messageFor(error)); }
  }
  protected resetCalibration(): void {
    this.editor?.reset(); this.engine?.recalibrate(); this.calibrated.set(false); this.calibrationMessage.set('Ajusta los puntos y vuelve a guardar.');
  }
  protected setFit(key: FitKey, event: Event): void {
    const control = this.controls().find(c => c.key === key)!;
    const value = Number((event.target as HTMLInputElement).value);
    if (!Number.isFinite(value)) return;
    this.fit.update(fit => ({ ...fit, [key]: Math.max(control.min, Math.min(control.max, value)) }));
    if (this.engine) this.engine.fit = { ...this.fit() };
  }
  protected resetFit(): void { this.fit.set(defaultFit(this.profile())); if (this.engine) this.engine.fit = { ...this.fit() }; }
  protected recenter(): void { this.engine?.recenter(); }
  protected toggleDebug(event: Event): void {
    this.debug.set((event.target as HTMLInputElement).checked); if (this.engine) this.engine.debug = this.debug();
  }
  protected toggleCoverage(event: Event): void {
    this.coverage.set((event.target as HTMLInputElement).checked);
    if (this.engine) this.engine.coverage = this.coverage();
  }
  protected closeDetector(): void {
    if (this.timer !== null) clearTimeout(this.timer); this.timer = null;
    const engine = this.engine; this.engine = null; engine?.stop(false);
    this.editor?.destroy(); this.editor = null; this.open.set(false); this.status.set('Listo para iniciar.');
  }
  private messageFor(error: unknown): string {
    if (error instanceof DOMException && error.name === 'NotAllowedError') return 'Permite el acceso a la cámara en la configuración del navegador.';
    if (error instanceof DOMException && error.name === 'NotFoundError') return 'No se encontró una cámara.';
    if (error instanceof DOMException && error.name === 'NotReadableError') return 'La cámara está ocupada. Cierra otras aplicaciones que la estén usando.';
    if (error instanceof DOMException && error.name === 'SecurityError') return 'No se pudo leer la imagen. Usa un PNG transparente servido con permisos CORS.';
    return error instanceof Error ? error.message : 'No se pudo iniciar el vestidor.';
  }
  ngOnDestroy(): void { this.destroyed = true; this.garmentRequest++; this.closeDetector(); }
}
