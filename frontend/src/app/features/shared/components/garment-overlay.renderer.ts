import { FilesetResolver, ImageSegmenter, PoseLandmarker } from '@mediapipe/tasks-vision';

// Keep the installed JS package and the WASM files on the SAME version.
// npm install --save-exact @mediapipe/tasks-vision@0.10.21
const WASM_URL = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.21/wasm';
const POSE_URL = 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task';
const MASK_URL = 'https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/1/selfie_multiclass_256x256.tflite';

export type Point = { x: number; y: number };
type Landmark = Point & { z?: number; visibility?: number; presence?: number };
type TrackedPoint = Point & { z: number; seenAt: number };
export type FitKey = 'width' | 'length' | 'sleeve' | 'offsetY' | 'sleeveWidth' | 'cuffWidth' | 'coverageMargin' | 'coverageHem' | 'skirtLength' | 'skirtWidth';
export type GarmentFit = Record<FitKey, number>;
export const DEFAULT_FIT: GarmentFit = { width: 1.12, length: 1, sleeve: 1, offsetY: 0, sleeveWidth: 1.3, cuffWidth: 1.25, coverageMargin: 0.025, coverageHem: 0.95, skirtLength: 1, skirtWidth: 1.35 };

// Left/right ALWAYS mean the left/right of the product photograph, not anatomy.
// These are initial handles for the editor, NOT automatically detected seams.
export const GARMENT_POINTS = [
  { label: '1. Hombro izquierdo: unión superior de manga y torso', x: 0.27, y: 0.10 },
  { label: '2. Hombro derecho: unión superior de manga y torso', x: 0.73, y: 0.10 },
  { label: '3. Axila izquierda: unión inferior de manga y torso', x: 0.30, y: 0.35 },
  { label: '4. Axila derecha: unión inferior de manga y torso', x: 0.70, y: 0.35 },
  { label: '5. Esquina inferior izquierda del torso', x: 0.30, y: 0.94 },
  { label: '6. Esquina inferior derecha del torso', x: 0.70, y: 0.94 },
  { label: '7. Codo izquierdo: borde exterior de la manga', x: 0.12, y: 0.52 },
  { label: '8. Codo izquierdo: borde interior de la manga', x: 0.27, y: 0.55 },
  { label: '9. Puño izquierdo: borde exterior', x: 0.03, y: 0.95 },
  { label: '10. Puño izquierdo: borde interior', x: 0.19, y: 0.98 },
  { label: '11. Codo derecho: borde exterior de la manga', x: 0.88, y: 0.52 },
  { label: '12. Codo derecho: borde interior de la manga', x: 0.73, y: 0.55 },
  { label: '13. Puño derecho: borde exterior', x: 0.97, y: 0.95 },
  { label: '14. Puño derecho: borde interior', x: 0.81, y: 0.98 },
  { label: '15. Borde superior del cuello: extremo izquierdo', x: 0.42, y: 0.01 },
  { label: '16. Borde superior del cuello: extremo derecho', x: 0.58, y: 0.01 },
  { label: '17. Profundidad del cuello: centro inferior', x: 0.50, y: 0.16 },
] as const;

type Triangle = readonly [number, number, number];
// El triángulo [14,16,15] es el hueco del cuello y nunca se pinta.
const TORSO: readonly Triangle[] = [[0, 14, 2], [14, 16, 2], [16, 3, 2], [16, 15, 3], [15, 1, 3], [2, 3, 4], [3, 5, 4]];
const LEFT_ARM: readonly Triangle[] = [[0, 2, 6], [2, 7, 6], [6, 7, 8], [7, 9, 8]];
const RIGHT_ARM: readonly Triangle[] = [[1, 10, 3], [3, 10, 11], [10, 12, 11], [11, 12, 13]];
const ALL_TRIANGLES = [...TORSO, ...LEFT_ARM, ...RIGHT_ARM];
export type GarmentCategory = 'top' | 'blouse' | 'dress';
export type SleeveKind = 'long' | 'short' | 'none';
export type GarmentProfile = { category: GarmentCategory; sleeves: SleeveKind };
export const DEFAULT_PROFILE: GarmentProfile = { category: 'top', sleeves: 'long' };
export const GARMENT_CATEGORIES = [{ value: 'top', label: 'Polera / suéter' }, { value: 'blouse', label: 'Blusa' }, { value: 'dress', label: 'Vestido' }] as const;
export const SLEEVE_KINDS = [{ value: 'long', label: 'Manga larga' }, { value: 'short', label: 'Manga corta' }, { value: 'none', label: 'Sin mangas / tirantes' }] as const;
export type CalibrationHandle = Point & { id: number; label: string };
export function defaultFit(profile: GarmentProfile): GarmentFit {
  return {
    ...DEFAULT_FIT, width: profile.category === 'blouse' ? 1.2 : DEFAULT_FIT.width,
    sleeveWidth: profile.sleeves === 'short' ? 1.05 : DEFAULT_FIT.sleeveWidth,
    coverageHem: profile.category === 'dress' ? 2.0 : DEFAULT_FIT.coverageHem
  };
}
export function profileTriangles(profile: GarmentProfile): { torso: readonly Triangle[]; skirt: readonly Triangle[]; left: readonly Triangle[]; right: readonly Triangle[] } {
  return {
    torso: profile.category === 'dress' ? [[0, 14, 2], [14, 16, 2], [16, 3, 2], [16, 15, 3], [15, 1, 3], [2, 3, 17], [3, 18, 17]] : TORSO,
    skirt: profile.category === 'dress' ? [[17, 18, 4], [18, 5, 4]] : [],
    left: profile.sleeves === 'none' ? [] : profile.sleeves === 'short' ? LEFT_ARM.slice(0, 2) : LEFT_ARM,
    right: profile.sleeves === 'none' ? [] : profile.sleeves === 'short' ? RIGHT_ARM.slice(0, 2) : RIGHT_ARM,
  };
}
export function defaultCalibration(profile: GarmentProfile): Point[] {
  const p = clonePoints(GARMENT_POINTS);
  if (profile.sleeves === 'short') {
    p[6] = { x: .04, y: .33 }; p[7] = { x: .20, y: .45 }; p[10] = { x: .96, y: .33 }; p[11] = { x: .80, y: .45 };
  }
  if (profile.category === 'dress') {
    p[0] = { x: .32, y: .06 }; p[1] = { x: .68, y: .06 }; p[2] = { x: .36, y: .22 }; p[3] = { x: .64, y: .22 };
    p[4] = { x: .12, y: .98 }; p[5] = { x: .88, y: .98 }; p[14] = { x: .44, y: .01 }; p[15] = { x: .56, y: .01 }; p[16] = { x: .50, y: .14 };
    p.push({ x: .38, y: .40 }, { x: .62, y: .40 });
    if (profile.sleeves === 'long') {
      p[6] = { x: .15, y: .30 }; p[7] = { x: .30, y: .32 }; p[8] = { x: .10, y: .52 }; p[9] = { x: .25, y: .54 };
      p[10] = { x: .85, y: .30 }; p[11] = { x: .70, y: .32 }; p[12] = { x: .90, y: .52 }; p[13] = { x: .75, y: .54 };
    } else if (profile.sleeves === 'short') {
      p[6] = { x: .10, y: .20 }; p[7] = { x: .26, y: .28 }; p[10] = { x: .90, y: .20 }; p[11] = { x: .74, y: .28 };
    }
  }
  return p;
}
export function calibrationHandles(profile: GarmentProfile): CalibrationHandle[] {
  const topology = profileTriangles(profile), used = new Set(Object.values(topology).flat().flat());
  const points = defaultCalibration(profile);
  return points.flatMap((p, id) => {
    if (!used.has(id)) return [];
    let label: string = id < 17 ? GARMENT_POINTS[id].label.replace(/^\d+\. /, '') : id === 17 ? 'Cintura izquierda' : 'Cintura derecha';
    if (id === 4 || id === 5) label = `${profile.category === 'dress' ? 'Borde inferior de la falda' : 'Borde inferior del torso'}: ${id === 4 ? 'izquierda' : 'derecha'}`;
    if (profile.sleeves === 'short' && [6, 7, 10, 11].includes(id)) label = `Final de manga ${id < 10 ? 'izquierda' : 'derecha'}: borde ${id % 2 === 0 ? 'exterior' : 'interior'}`;
    if (profile.sleeves === 'none' && id < 2) label = `Hombro / borde exterior del tirante ${id === 0 ? 'izquierdo' : 'derecho'}`;
    return [{ ...p, id, label }];
  }).map((p, index) => ({ ...p, label: `${index + 1}. ${p.label}` }));
}
function profileKey(source: string): string { let h = 2166136261; for (let i = 0; i < source.length; i++)h = Math.imul(h ^ source.charCodeAt(i), 16777619); return `aci-garment-profile-v1:${h >>> 0}`; }
export function loadGarmentProfile(source: string): GarmentProfile {
  try {
    const p = JSON.parse(localStorage.getItem(profileKey(source)) ?? 'null');
    if (p && GARMENT_CATEGORIES.some(v => v.value === p.category) && SLEEVE_KINDS.some(v => v.value === p.sleeves)) return { category: p.category, sleeves: p.sleeves };
  } catch { /* Profile selection remains available without storage. */ }
  return { ...DEFAULT_PROFILE };
}
export function saveGarmentProfile(source: string, profile: GarmentProfile): void {
  try { localStorage.setItem(profileKey(source), JSON.stringify(profile)); } catch { /* Session-only preference. */ }
}

const clonePoints = (points: readonly Point[]): Point[] => points.map(({ x, y }) => ({ x, y }));
const add = (a: Point, b: Point, scale = 1): Point => ({ x: a.x + b.x * scale, y: a.y + b.y * scale });
const sub = (a: Point, b: Point): Point => ({ x: a.x - b.x, y: a.y - b.y });
const length = (a: Point): number => Math.hypot(a.x, a.y);
const unit = (a: Point): Point => { const d = Math.max(0.00001, length(a)); return { x: a.x / d, y: a.y / d }; };
const mix = (a: Point, b: Point, t = 0.5): Point => add(a, sub(b, a), t);
const dot = (a: Point, b: Point): number => a.x * b.x + a.y * b.y;
const area = (a: Point, b: Point, c: Point): number => (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
const clamp = (n: number, lo: number, hi: number): number => Math.max(lo, Math.min(hi, n));

export function validateCalibration(points: readonly Point[], profile: GarmentProfile = DEFAULT_PROFILE): string | null {
  const handles = calibrationHandles(profile);
  if (points.length !== (profile.category === 'dress' ? 19 : 17) || handles.some(({ id }) => !points[id] || !Number.isFinite(points[id].x) || !Number.isFinite(points[id].y) || points[id].x < 0 || points[id].x > 1 || points[id].y < 0 || points[id].y > 1)) return `Los ${handles.length} puntos deben quedar dentro de la imagen.`;
  for (const [a, b, c] of Object.values(profileTriangles(profile)).flat()) {
    if (area(points[a], points[b], points[c]) < 0.00015) {
      return `Revisa los puntos ${handles.findIndex(p => p.id === a) + 1}, ${handles.findIndex(p => p.id === b) + 1} y ${handles.findIndex(p => p.id === c) + 1}: se cruzan o están demasiado juntos.`;
    }
  }
  return null;
}

/** Crop transparent padding once. A photograph with a background is not a garment texture. */
export function prepareGarmentTexture(image: HTMLImageElement): HTMLCanvasElement {
  const canvas = document.createElement('canvas');
  const scale = Math.min(1, 1600 / Math.max(image.naturalWidth, image.naturalHeight));
  canvas.width = Math.max(1, Math.round(image.naturalWidth * scale));
  canvas.height = Math.max(1, Math.round(image.naturalHeight * scale));
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  if (!ctx) throw new Error('No se pudo crear el lienzo de la prenda.');
  ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
  const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  let minX = canvas.width, minY = canvas.height, maxX = -1, maxY = -1, transparent = 0;
  for (let y = 0; y < canvas.height; y++) for (let x = 0; x < canvas.width; x++) {
    const alpha = data[(y * canvas.width + x) * 4 + 3];
    if (alpha < 8) { transparent++; continue; }
    minX = Math.min(minX, x); minY = Math.min(minY, y);
    maxX = Math.max(maxX, x); maxY = Math.max(maxY, y);
  }
  if (maxX < minX) throw new Error('La imagen de la prenda está vacía.');
  if (transparent < canvas.width * canvas.height * 0.005) throw new Error('La prenda necesita fondo transparente. Revisa la imagen que devuelve CatalogoPrendaService.');
  const cropped = document.createElement('canvas');
  cropped.width = maxX - minX + 1; cropped.height = maxY - minY + 1;
  cropped.getContext('2d')!.drawImage(canvas, minX, minY, cropped.width, cropped.height, 0, 0, cropped.width, cropped.height);
  return cropped;
}

function storageKey(key: string, texture: HTMLCanvasElement): string {
  let hash = 2166136261;
  for (let i = 0; i < key.length; i++) hash = Math.imul(hash ^ key.charCodeAt(i), 16777619);
  return `aci-garment-mesh-v1:${hash >>> 0}:${texture.width}x${texture.height}`;
}

/** Click a point in the list, then click its position in the product photo; handles also drag. */
export class GarmentCalibrationEditor {
  private points: Point[];
  private readonly handles: CalibrationHandle[];
  private selected = 0;
  private pointer: number | null = null;
  private readonly key: string;
  private readonly abort = new AbortController();

  constructor(
    private readonly canvas: HTMLCanvasElement,
    private readonly texture: HTMLCanvasElement,
    sourceKey: string,
    private readonly changed: (selected: number) => void,
    private readonly applied: (points: Point[]) => void,
    private readonly profile: GarmentProfile = DEFAULT_PROFILE,
    private readonly serverPoints: readonly Point[] | null = null,
  ) {
    this.points = defaultCalibration(profile); this.handles = calibrationHandles(profile);
    const legacy = storageKey(sourceKey, texture);
    this.key = profile.category === 'top' && profile.sleeves === 'long' ? legacy : `${legacy}:${profile.category}:${profile.sleeves}`;
    const scale = Math.min(1, 720 / texture.width);
    canvas.width = Math.round(texture.width * scale);
    canvas.height = Math.round(texture.height * scale);
    canvas.style.touchAction = 'none';
    const serverCandidate = this.serverPoints && !validateCalibration(this.serverPoints, this.profile)
      ? clonePoints(this.serverPoints)
      : null;
    if (serverCandidate) {
      this.points = serverCandidate; this.applied(clonePoints(this.points));
    } else {
      try {
        const saved: unknown = JSON.parse(localStorage.getItem(this.key) ?? 'null');
        if (Array.isArray(saved) && saved.every(p => p && typeof p.x === 'number' && typeof p.y === 'number')) {
          // Migra calibraciones anteriores: conserva tus 16 puntos y añade solo el nuevo punto 17.
          let candidate = clonePoints(saved as Point[]);
          if (this.profile.category === 'dress' && candidate.length === 18) {
            candidate = [...candidate.slice(0, 16), { ...this.points[16] }, ...candidate.slice(16)];
          } else if (this.profile.category !== 'dress' && candidate.length === 16) {
            candidate.push({ ...this.points[16] });
          }
          if (candidate.length === this.points.length && !validateCalibration(candidate, this.profile)) {
            this.points = candidate; this.applied(clonePoints(this.points));
            if (candidate.length !== (saved as Point[]).length) localStorage.setItem(this.key, JSON.stringify(candidate));
          }
        }
      } catch { /* Storage is optional; calibration still works in this session. */ }
    }
    const options = { signal: this.abort.signal };
    canvas.addEventListener('pointerdown', this.down, options);
    canvas.addEventListener('pointermove', this.move, options);
    canvas.addEventListener('pointerup', this.up, options);
    canvas.addEventListener('pointercancel', this.cancel, options);
    this.draw();
  }

  select(index: number): void {
    this.selected = this.handles.some(p => p.id === index) ? index : this.handles[0].id; this.changed(this.selected); this.draw();
  }
  reset(): void { this.points = defaultCalibration(this.profile); this.select(0); }
  save(): string {
    const error = validateCalibration(this.points, this.profile);
    if (error) throw new Error(error);
    this.applied(clonePoints(this.points));
    try { localStorage.setItem(this.key, JSON.stringify(this.points)); }
    catch { return 'Calibración aplicada para esta sesión. El navegador no permitió guardarla.'; }
    return 'Calibración guardada en este navegador para esta prenda.';
  }
  getPoints(): Point[] { return clonePoints(this.points); }
  destroy(): void { this.abort.abort(); this.pointer = null; }
  private position(event: PointerEvent): Point {
    const rect = this.canvas.getBoundingClientRect();
    return { x: clamp((event.clientX - rect.left) / rect.width, 0, 1), y: clamp((event.clientY - rect.top) / rect.height, 0, 1) };
  }
  private down = (event: PointerEvent): void => {
    if (this.pointer !== null || event.button !== 0) return;
    event.preventDefault(); this.pointer = event.pointerId;
    this.canvas.setPointerCapture(event.pointerId);
    const p = this.position(event), rect = this.canvas.getBoundingClientRect();
    const nearest = this.handles.map(({ id: i }) => ({ i, d: Math.hypot((p.x - this.points[i].x) * rect.width, (p.y - this.points[i].y) * rect.height) })).sort((a, b) => a.d - b.d)[0];
    if (nearest.d < 16) this.select(nearest.i);
    this.points[this.selected] = p; this.draw();
  };
  private move = (event: PointerEvent): void => {
    if (event.pointerId !== this.pointer) return;
    this.points[this.selected] = this.position(event); this.draw();
  };
  private up = (event: PointerEvent): void => {
    if (event.pointerId !== this.pointer) return;
    this.points[this.selected] = this.position(event); this.cancel(event); this.draw();
  };
  private cancel = (event: PointerEvent): void => {
    if (event.pointerId !== this.pointer) return;
    if (this.canvas.hasPointerCapture(event.pointerId)) this.canvas.releasePointerCapture(event.pointerId);
    this.pointer = null;
  };
  private draw(): void {
    const ctx = this.canvas.getContext('2d'); if (!ctx) return;
    const w = this.canvas.width, h = this.canvas.height;
    ctx.clearRect(0, 0, w, h);
    for (let y = 0; y < h; y += 20) for (let x = 0; x < w; x += 20) {
      ctx.fillStyle = ((x + y) / 20) % 2 ? '#e2e8f0' : '#f8fafc'; ctx.fillRect(x, y, 20, 20);
    }
    ctx.drawImage(this.texture, 0, 0, w, h);
    const points = this.points.map(p => ({ x: p.x * w, y: p.y * h }));
    drawWireframe(ctx, points, Object.values(profileTriangles(this.profile)).flat());
    this.handles.forEach(({ id: i }, index) => {
      const p = points[i];
      ctx.beginPath(); ctx.arc(p.x, p.y, i === this.selected ? 13 : 10, 0, Math.PI * 2);
      ctx.fillStyle = i === this.selected ? '#be123c' : '#0f172a'; ctx.fill();
      ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 2; ctx.stroke();
      ctx.fillStyle = '#ffffff'; ctx.font = 'bold 11px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(String(index + 1), p.x, p.y);
    });
  }
}

function drawWireframe(ctx: CanvasRenderingContext2D, points: readonly Point[], triangles: readonly Triangle[]): void {
  ctx.save(); ctx.strokeStyle = '#06b6d4'; ctx.lineWidth = 1;
  for (const [a, b, c] of triangles) {
    ctx.beginPath(); ctx.moveTo(points[a].x, points[a].y); ctx.lineTo(points[b].x, points[b].y); ctx.lineTo(points[c].x, points[c].y); ctx.closePath(); ctx.stroke();
  }
  ctx.restore();
}

/** Exact affine mapping of a source triangle to a destination triangle. */
export function drawTexturedTriangle(ctx: CanvasRenderingContext2D, image: CanvasImageSource, source: readonly Point[], target: readonly Point[]): void {
  const [s0, s1, s2] = source, [d0, d1, d2] = target;
  const determinant = area(s0, s1, s2);
  if (Math.abs(determinant) < 0.01 || Math.abs(area(d0, d1, d2)) < 0.01) return;
  const sx1 = s1.x - s0.x, sy1 = s1.y - s0.y, sx2 = s2.x - s0.x, sy2 = s2.y - s0.y;
  const dx1 = d1.x - d0.x, dy1 = d1.y - d0.y, dx2 = d2.x - d0.x, dy2 = d2.y - d0.y;
  const a = (dx1 * sy2 - dx2 * sy1) / determinant, c = (dx2 * sx1 - dx1 * sx2) / determinant;
  const b = (dy1 * sy2 - dy2 * sy1) / determinant, d = (dy2 * sx1 - dy1 * sx2) / determinant;
  ctx.save();
  // A subpixel overlap removes rasterization cracks along shared edges.
  const center = { x: (d0.x + d1.x + d2.x) / 3, y: (d0.y + d1.y + d2.y) / 3 };
  const expanded = target.map(p => add(p, unit(sub(p, center)), 0.45));
  ctx.beginPath(); ctx.moveTo(expanded[0].x, expanded[0].y); ctx.lineTo(expanded[1].x, expanded[1].y); ctx.lineTo(expanded[2].x, expanded[2].y); ctx.closePath(); ctx.clip();
  ctx.transform(a, b, c, d, d0.x - a * s0.x - c * s0.y, d0.y - b * s0.x - d * s0.y);
  ctx.drawImage(image, 0, 0); ctx.restore();
}

/** Independent validity/expiry per joint: losing a wrist does not reset the torso. */
export class PoseTracker {
  private joints: Array<TrackedPoint | undefined> = [];
  update(landmarks: readonly Landmark[], now: number): void {
    for (let i = 0; i < 33; i++) {
      const p = landmarks[i];
      if (!p || !Number.isFinite(p.x) || !Number.isFinite(p.y) || !Number.isFinite(p.z ?? 0) || p.x < 0 || p.x > 1 || p.y < 0 || p.y > 1 || (p.visibility ?? 1) < 0.55 || (p.presence ?? 1) < 0.55) continue;
      // Mirror only the camera coordinates. The product texture is never mirrored.
      const next = { x: 1 - p.x, y: p.y, z: p.z ?? 0, seenAt: now };
      const old = this.joints[i];
      if (!old || now - old.seenAt > 220) { this.joints[i] = next; continue; }
      const dt = Math.max(1, now - old.seenAt);
      const speed = Math.hypot(next.x - old.x, next.y - old.y) / (dt / 1000);
      const alpha = 1 - Math.exp(-dt / (speed > 0.6 ? 28 : 65));
      this.joints[i] = { ...mix(old, next, alpha), z: old.z + (next.z - old.z) * alpha, seenAt: now };
    }
  }
  get(index: number, now: number): TrackedPoint | null {
    const p = this.joints[index]; return p && now - p.seenAt <= 220 ? p : null;
  }
  clear(): void { this.joints = []; }
}

type TargetMesh = { points: Point[]; leftArm: boolean; rightArm: boolean; leftFront: boolean; rightFront: boolean };
export function buildTargetMesh(tracker: PoseTracker, now: number, w: number, h: number, fit: GarmentFit, profile: GarmentProfile = DEFAULT_PROFILE): TargetMesh | null {
  const ls = tracker.get(11, now), rs = tracker.get(12, now), lh = tracker.get(23, now), rh = tracker.get(24, now);
  if (!ls || !rs || !lh || !rh) return null;
  // Restrict to frontal tracking. A flat photograph does not describe the side/back.
  if (ls.x >= rs.x || Math.abs(ls.z - rs.z) > Math.abs(rs.x - ls.x) * 0.8) return null;
  const px = (p: Point): Point => ({ x: p.x * w, y: p.y * h });
  const sL = px(ls), sR = px(rs), hL = px(lh), hR = px(rh);
  const shoulderCenter = mix(sL, sR), hipCenter = mix(hL, hR);
  const shoulderWidth = length(sub(sR, sL)), torsoHeight = length(sub(hipCenter, shoulderCenter));
  if (shoulderWidth < w * 0.1 || torsoHeight < h * 0.13 || hipCenter.y <= shoulderCenter.y || torsoHeight / shoulderWidth > 3.5) return null;
  const across = unit(sub(sR, sL)), down = unit(sub(hipCenter, shoulderCenter));
  const shift = { x: down.x * torsoHeight * fit.offsetY, y: down.y * torsoHeight * fit.offsetY };
  const topL = add(add(sL, across, -shoulderWidth * (fit.width - 1) / 2), down, -torsoHeight * 0.045);
  const topR = add(add(sR, across, shoulderWidth * (fit.width - 1) / 2), down, -torsoHeight * 0.045);
  const axL = add(add(topL, down, torsoHeight * 0.24), across, shoulderWidth * 0.025);
  const axR = add(add(topR, down, torsoHeight * 0.24), across, -shoulderWidth * 0.025);
  let hem = add(shoulderCenter, sub(hipCenter, shoulderCenter), fit.length);
  const waist = add(shoulderCenter, sub(hipCenter, shoulderCenter), 0.68 * fit.length);
  if (profile.category === 'dress') {
    const lk = tracker.get(25, now), rk = tracker.get(26, now), la = tracker.get(27, now), ra = tracker.get(28, now);
    if (!lk || !rk || (fit.skirtLength > 1.05 && (!la || !ra))) return null;
    const knee = mix(px(lk), px(rk));
    if (knee.y <= hipCenter.y + torsoHeight * 0.15) return null;
    hem = fit.skirtLength <= 1 ? mix(waist, knee, fit.skirtLength)
      : mix(knee, la && ra ? mix(px(la), px(ra)) : add(knee, sub(knee, hipCenter)), (fit.skirtLength - 1) / 0.65);
  }
  const hipAcross = unit(sub(hR, hL));
  const halfHem = Math.max(length(sub(hR, hL)) / 2, shoulderWidth * 0.40) * fit.width * (profile.category === 'dress' ? fit.skirtWidth : 1);
  const points = [topL, topR, axL, axR, add(hem, hipAcross, -halfHem), add(hem, hipAcross, halfHem)];
  const arm = (shoulder: Point, elbowIndex: number, wristIndex: number, side: number): boolean => {
    const elbow = tracker.get(elbowIndex, now), wrist = tracker.get(wristIndex, now);
    if (profile.sleeves === 'none' || !elbow || (profile.sleeves === 'long' && !wrist)) { points.push(shoulder, shoulder, shoulder, shoulder); return false; }
    const e = px(elbow), upper = sub(e, shoulder);
    if (profile.sleeves === 'short') {
      if (length(upper) < shoulderWidth * 0.15) { points.push(shoulder, shoulder, shoulder, shoulder); return false; }
      const end = add(shoulder, upper, clamp(0.65 * fit.sleeve, 0.30, 0.95));
      const normal = unit({ x: upper.y * side, y: -upper.x * side }), half = shoulderWidth * 0.11 * fit.sleeveWidth;
      const outer = add(end, normal, half), inner = add(end, normal, -half);
      points.push(outer, inner, outer, inner); return true;
    }
    const wr = px(wrist!), lower = sub(wr, e);
    if (length(upper) < shoulderWidth * 0.15 || length(lower) < shoulderWidth * 0.15) { points.push(shoulder, shoulder, shoulder, shoulder); return false; }
    // Keep one signed normal along the whole arm. Choosing the wrist normal
    // independently can flip the forearm texture when the hand is on the waist.
    const upperNormal = unit({ x: upper.y * side, y: -upper.x * side });
    const cuffNormal = unit({ x: lower.y * side, y: -lower.x * side });
    const sum = add(upperNormal, cuffNormal);
    const normal = length(sum) > 0.15 ? unit(sum) : upperNormal;
    // A bounded miter covers the outer elbow without an unbounded spike.
    const miter = Math.min(1.8, 1 / Math.max(0.4, Math.abs(dot(normal, upperNormal))));
    const elbowHalf = shoulderWidth * 0.105 * fit.sleeveWidth * miter;
    const cuffHalf = shoulderWidth * 0.075 * fit.cuffWidth;
    const cuff = add(e, lower, fit.sleeve);
    points.push(add(e, normal, elbowHalf), add(e, normal, -elbowHalf), add(cuff, cuffNormal, cuffHalf), add(cuff, cuffNormal, -cuffHalf));
    return true;
  };
  const leftArm = arm(sL, 13, 15, -1), rightArm = arm(sR, 14, 16, 1);
  const neckLeft = add(mix(topL, topR, 0.34), down, -torsoHeight * 0.10);
  const neckRight = add(mix(topL, topR, 0.66), down, -torsoHeight * 0.10);
  const neckDepth = add(mix(topL, topR, 0.50), down, torsoHeight * 0.065);
  points.push(neckLeft, neckRight, neckDepth);
  if (profile.category === 'dress') {
    const waistHalf = shoulderWidth * 0.40 * fit.width;
    points.push(add(waist, across, -waistHalf), add(waist, across, waistHalf));
  }
  return {
    points: points.map(p => add(p, shift)), leftArm, rightArm,
    leftFront: (tracker.get(13, now)?.z ?? ls.z) < (ls.z + rs.z) / 2 + 0.025,
    rightFront: (tracker.get(14, now)?.z ?? rs.z) < (ls.z + rs.z) / 2 + 0.025,
  };
}

// One copied segmentation result, reused for fitting, gap coverage and occlusion.
export type ClothingSnapshot = { data: Uint8Array; width: number; height: number };
type GarmentPart = 'torso' | 'skirt' | 'left' | 'right';
export type GarmentPatch = { source: Point[]; target: Point[]; part: GarmentPart };
function clothingAt(mask: ClothingSnapshot, p: Point, w: number, h: number): boolean {
  const x = Math.floor((1 - p.x / w) * mask.width), y = Math.floor(p.y / h * mask.height);
  return x >= 0 && x < mask.width && y >= 0 && y < mask.height && mask.data[y * mask.width + x] === 4;
}

/** Stable widths in body-relative units; never carry a stale mask to a new frame. */
export class ClothingContourFitter {
  private history = new Map<string, { value: number; at: number }>();
  clear(): void { this.history.clear(); }
  expand(key: string, pair: Point[], mask: ClothingSnapshot | null, w: number, h: number, bodyWidth: number, margin: number, now: number): Point[] {
    if (!mask) return pair;
    const center = mix(pair[0], pair[1]), normal = unit(sub(pair[1], pair[0]));
    const half = length(sub(pair[1], pair[0])) / 2;
    const step = Math.max(1, w / mask.width / 2);
    // Require actual clothing near this section before growing its silhouette.
    if (![0, -half * 0.35, half * 0.35].some(t => clothingAt(mask, add(center, normal, t), w, h))) return pair;
    const measure = (sign: number): number => {
      let last = 0, gap = 0;
      const limit = half + bodyWidth * 0.16;
      for (let t = 0; t <= limit; t += step) {
        if (clothingAt(mask, add(center, normal, t * sign), w, h)) { last = t; gap = 0; }
        else if (++gap >= 3 && t > half * 0.35) break;
      }
      const desired = Math.max(half, last + margin * bodyWidth) / bodyWidth;
      const id = `${key}:${sign}`, previous = this.history.get(id);
      const dt = previous ? now - previous.at : Infinity;
      const alpha = !previous || dt > 220 ? 1 : 1 - Math.exp(-Math.max(1, dt) / (desired > previous.value ? 35 : 130));
      const value = previous ? previous.value + (desired - previous.value) * alpha : desired;
      this.history.set(id, { value, at: now });
      return Math.max(half, value * bodyWidth);
    };
    return [add(center, normal, -measure(-1)), add(center, normal, measure(1))];
  }
}

/** Build patches ONLY from the explicit garment calibration points.
 * No intermediate points are interpolated between the explicit calibration handles.
 */
export function createGarmentPatches(
  source: readonly Point[],
  mesh: TargetMesh,
  _mask: ClothingSnapshot | null,
  _fitter: ClothingContourFitter,
  _w: number,
  _h: number,
  _fit: GarmentFit,
  _now: number,
  profile: GarmentProfile = DEFAULT_PROFILE,
): GarmentPatch[] {
  const target = mesh.points;
  const patches: GarmentPatch[] = [];
  const topology = profileTriangles(profile);

  const addTriangles = (part: GarmentPart, triangles: readonly Triangle[]): void => {
    if (part === 'left' && !mesh.leftArm) return;
    if (part === 'right' && !mesh.rightArm) return;

    for (const [a, b, c] of triangles) {
      if (!source[a] || !source[b] || !source[c] || !target[a] || !target[b] || !target[c]) continue;
      patches.push({
        source: [source[a], source[b], source[c]],
        target: [target[a], target[b], target[c]],
        part,
      });
    }
  };

  addTriangles('torso', topology.torso);
  addTriangles('skirt', topology.skirt);
  addTriangles('left', topology.left);
  addTriangles('right', topology.right);

  // Keep the original drawing order for arm occlusion, but do not create
  // any additional/interpolated mesh vertices.
  const order = (part: GarmentPart): number =>
    (part === 'torso' || part === 'skirt') ? 1 :
      (part === 'left' ? mesh.leftFront : mesh.rightFront) ? 2 : 0;

  return patches.sort((a, b) => order(a.part) - order(b.part));
}

/** Fill transparent source regions from opaque pixels of the SAME garment part. */
class SolidGarmentAtlas {
  private readonly width: number;
  private readonly height: number;
  private readonly parts = new Map<GarmentPart, { data: Uint8ClampedArray; nearest: Int32Array }>();
  constructor(texture: HTMLCanvasElement, source: readonly Point[], profile: GarmentProfile = DEFAULT_PROFILE) {
    const scale = Math.min(1, 512 / Math.max(texture.width, texture.height));
    this.width = Math.max(1, Math.round(texture.width * scale)); this.height = Math.max(1, Math.round(texture.height * scale));
    for (const [part, triangles] of Object.entries(profileTriangles(profile)) as [GarmentPart, readonly Triangle[]][]) {
      if (!triangles.length) continue;
      const c = document.createElement('canvas'); c.width = this.width; c.height = this.height;
      const ctx = c.getContext('2d', { willReadFrequently: true })!;
      ctx.save(); ctx.beginPath();
      for (const [a, b, d] of triangles) {
        ctx.moveTo(source[a].x * c.width, source[a].y * c.height);
        ctx.lineTo(source[b].x * c.width, source[b].y * c.height);
        ctx.lineTo(source[d].x * c.width, source[d].y * c.height); ctx.closePath();
      }
      ctx.clip(); ctx.drawImage(texture, 0, 0, c.width, c.height); ctx.restore();
      const data = ctx.getImageData(0, 0, c.width, c.height).data;
      const count = c.width * c.height, nearest = new Int32Array(count).fill(-1), queue = new Int32Array(count);
      let head = 0, tail = 0;
      for (let i = 0; i < count; i++) if (data[i * 4 + 3] >= 224) { nearest[i] = i; queue[tail++] = i; }
      if (!tail) throw new Error(`La calibración de ${part === 'torso' ? 'torso' : part === 'skirt' ? 'falda' : part === 'left' ? 'manga izquierda' : 'manga derecha'} no contiene tela opaca. Revisa sus puntos.`);
      const visit = (next: number, from: number): void => {
        if (nearest[next] !== -1) return; nearest[next] = nearest[from]; queue[tail++] = next;
      };
      while (head < tail) {
        const i = queue[head++], x = i % c.width;
        if (x) visit(i - 1, i); if (x + 1 < c.width) visit(i + 1, i);
        if (i >= c.width) visit(i - c.width, i); if (i + c.width < count) visit(i + c.width, i);
      }
      this.parts.set(part, { data, nearest });
    }
  }
  paint(part: GarmentPart, p: Point, output: Uint8ClampedArray, offset: number): void {
    const atlas = this.parts.get(part)!;
    const x = clamp(Math.round(p.x * (this.width - 1)), 0, this.width - 1), y = clamp(Math.round(p.y * (this.height - 1)), 0, this.height - 1);
    const i = atlas.nearest[y * this.width + x] * 4;
    output[offset] = atlas.data[i]; output[offset + 1] = atlas.data[i + 1]; output[offset + 2] = atlas.data[i + 2]; output[offset + 3] = 255;
  }
}

function closestWeights(p: Point, triangle: readonly Point[]): { weights: number[]; distance: number } | null {
  const [a, b, c] = triangle, determinant = area(a, b, c);
  if (Math.abs(determinant) < 0.01) return null;
  const v = area(a, p, c) / determinant, t = area(a, b, p) / determinant, u = 1 - v - t;
  if (u >= 0 && v >= 0 && t >= 0) return { weights: [u, v, t], distance: 0 };
  let distance = Infinity, weights = [1, 0, 0];
  for (let i = 0; i < 3; i++) {
    const j = (i + 1) % 3, edge = sub(triangle[j], triangle[i]), d = dot(edge, edge);
    const ratio = d ? clamp(dot(sub(p, triangle[i]), edge) / d, 0, 1) : 0;
    const projected = add(triangle[i], edge, ratio), delta = sub(p, projected), squared = dot(delta, delta);
    if (squared < distance) { distance = squared; weights = [0, 0, 0]; weights[i] = 1 - ratio; weights[j] = ratio; }
  }
  return { weights, distance };
}

/** Opaque texture underlay ONLY on detected clothing near the upper-body mesh. */
export class ClothingCoverageLayer {
  private readonly canvas = document.createElement('canvas');
  private image: ImageData | null = null;
  private readonly atlas: SolidGarmentAtlas;
  constructor(texture: HTMLCanvasElement, source: readonly Point[], private readonly profile: GarmentProfile = DEFAULT_PROFILE) { this.atlas = new SolidGarmentAtlas(texture, source, profile); }
  fill(ctx: CanvasRenderingContext2D, mask: ClothingSnapshot, patches: readonly GarmentPatch[], tracker: PoseTracker, now: number, fit: GarmentFit, mesh: TargetMesh): number {
    const w = ctx.canvas.width, h = ctx.canvas.height;
    const ls = tracker.get(11, now), rs = tracker.get(12, now), lh = tracker.get(23, now), rh = tracker.get(24, now);
    if (!ls || !rs || !lh || !rh || !patches.length) return 0;
    const pixels = (p: Point): Point => ({ x: p.x * w, y: p.y * h });
    const top = pixels(mix(ls, rs)), hip = pixels(mix(lh, rh)), axis = sub(hip, top), height = length(axis), down = unit(axis);
    const bodyWidth = length(sub(pixels(rs), pixels(ls))), margin = bodyWidth * (0.18 + fit.coverageMargin);
    if (this.canvas.width !== w || this.canvas.height !== h || !this.image) { this.canvas.width = w; this.canvas.height = h; this.image = new ImageData(w, h); }
    const output = this.image.data; output.fill(0);
    const drawn = ctx.getImageData(0, 0, w, h).data;
    const candidates = [...patches].reverse().map(patch => ({
      patch,
      minX: Math.min(...patch.target.map(p => p.x)), maxX: Math.max(...patch.target.map(p => p.x)),
      minY: Math.min(...patch.target.map(p => p.y)), maxY: Math.max(...patch.target.map(p => p.y)),
    }));
    const x0 = clamp(Math.floor(Math.min(...candidates.map(c => c.minX)) - margin), 0, w), x1 = clamp(Math.ceil(Math.max(...candidates.map(c => c.maxX)) + margin), 0, w);
    const y0 = clamp(Math.floor(Math.min(...candidates.map(c => c.minY)) - margin), 0, h), y1 = clamp(Math.ceil(Math.max(...candidates.map(c => c.maxY)) + margin), 0, h);
    const necklineHole: Point[] = mesh.points.length > 16 ? [mesh.points[14], mesh.points[16], mesh.points[15]] : [];
    let filled = 0;
    for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) {
      const index = (y * w + x) * 4, point = { x: x + 0.5, y: y + 0.5 };
      if (necklineHole.length === 3 && inside(point, necklineHole)) continue;
      if (drawn[index + 3] === 255 || !clothingAt(mask, point, w, h)) continue;
      const vertical = dot(sub(point, top), down) / height;
      // Clothing class includes trousers too: explicitly limit the lower fill.
      if (vertical > fit.coverageHem || vertical < -0.25) continue;
      let best = this.profile.sleeves === 'long' ? margin * margin : 0, selected: GarmentPatch | null = null, weights: number[] = [];
      for (const candidate of candidates) {
        const dx = Math.max(candidate.minX - point.x, 0, point.x - candidate.maxX), dy = Math.max(candidate.minY - point.y, 0, point.y - candidate.maxY);
        if (dx * dx + dy * dy > best) continue;
        const hit = closestWeights(point, candidate.patch.target);
        if (hit && hit.distance <= best) {
          best = hit.distance; selected = candidate.patch; weights = hit.weights;
          if (best === 0) break;
        }
      }
      if (!selected) continue;
      const source = selected.source.reduce((sum, p, i) => add(sum, p, weights[i]), { x: 0, y: 0 });
      this.atlas.paint(selected.part, source, output, index); filled++;
    }
    const layer = this.canvas.getContext('2d')!; layer.putImageData(this.image, 0, 0);
    ctx.save(); ctx.globalCompositeOperation = 'destination-over'; ctx.drawImage(this.canvas, 0, 0); ctx.restore();
    return filled;
  }
}

/** Prevent expanded sleeves from painting the background inside bent-arm gaps. */
export class PersonSilhouetteClipper {
  private readonly canvas = document.createElement('canvas');
  private image: ImageData | null = null;
  private horizontal = new Uint8Array(0);
  apply(ctx: CanvasRenderingContext2D, mask: ClothingSnapshot, marginPixels: number, preserve: readonly GarmentPatch[] = []): void {
    const w = mask.width, h = mask.height;
    if (!this.image || this.canvas.width !== w || this.canvas.height !== h) {
      this.canvas.width = w; this.canvas.height = h; this.image = new ImageData(w, h); this.horizontal = new Uint8Array(w * h);
    }
    const radius = clamp(Math.ceil(marginPixels / ctx.canvas.width * w), 1, 6);
    const person = (index: number): number => mask.data[index] >= 1 && mask.data[index] <= 4 ? 1 : 0;
    // Separable binary dilation, O(width*height), independent of the margin size.
    for (let y = 0; y < h; y++) {
      let count = 0; for (let x = 0; x <= radius && x < w; x++)count += person(y * w + x);
      for (let x = 0; x < w; x++) {
        this.horizontal[y * w + x] = count > 0 ? 1 : 0;
        if (x - radius >= 0) count -= person(y * w + x - radius);
        if (x + radius + 1 < w) count += person(y * w + x + radius + 1);
      }
    }
    const rgba = this.image.data; rgba.fill(0);
    for (let x = 0; x < w; x++) {
      let count = 0; for (let y = 0; y <= radius && y < h; y++)count += this.horizontal[y * w + x];
      for (let y = 0; y < h; y++) {
        if (count) rgba[(y * w + x) * 4 + 3] = 255;
        if (y - radius >= 0) count -= this.horizontal[(y - radius) * w + x];
        if (y + radius + 1 < h) count += this.horizontal[(y + radius + 1) * w + x];
      }
    }
    const maskContext = this.canvas.getContext('2d')!; maskContext.putImageData(this.image, 0, 0);
    maskContext.save(); maskContext.fillStyle = '#ffffff';
    for (const patch of preserve) {
      maskContext.beginPath(); patch.target.forEach((p, i) => { const x = (1 - p.x / ctx.canvas.width) * w, y = p.y / ctx.canvas.height * h; i ? maskContext.lineTo(x, y) : maskContext.moveTo(x, y); }); maskContext.closePath(); maskContext.fill();
    }
    maskContext.restore();
    ctx.save(); ctx.globalCompositeOperation = 'destination-in'; ctx.translate(ctx.canvas.width, 0); ctx.scale(-1, 1);
    ctx.drawImage(this.canvas, 0, 0, ctx.canvas.width, ctx.canvas.height); ctx.restore();
  }
}

function inside(point: Point, polygon: readonly Point[]): boolean {
  let hit = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const a = polygon[i], b = polygon[j];
    if ((a.y > point.y) !== (b.y > point.y) && point.x < (b.x - a.x) * (point.y - a.y) / (b.y - a.y) + a.x) hit = !hit;
  }
  return hit;
}

function convexHull(points: Point[]): Point[] {
  const sorted = [...points].sort((a, b) => a.x - b.x || a.y - b.y);
  const half = (list: Point[]): Point[] => {
    const result: Point[] = [];
    for (const p of list) { while (result.length >= 2 && area(result[result.length - 2], result[result.length - 1], p) <= 0) result.pop(); result.push(p); }
    return result;
  };
  return [...half(sorted).slice(0, -1), ...half(sorted.reverse()).slice(0, -1)];
}

type Callbacks = { status: (text: string) => void; warning: (text: string) => void; stopped: () => void };

/** One captured frame is used for pose, occlusion and display, avoiding video/canvas drift. */
export class GarmentTryOnEngine {
  private static active: GarmentTryOnEngine | null = null;
  fit: GarmentFit = { ...DEFAULT_FIT };
  debug = false;
  coverage = true;
  profile: GarmentProfile = { ...DEFAULT_PROFILE };
  private readonly contourFitter = new ClothingContourFitter();
  private readonly silhouetteClipper = new PersonSilhouetteClipper();
  private coverageLayer: ClothingCoverageLayer | null = null;
  private stream: MediaStream | null = null;
  private pose: PoseLandmarker | null = null;
  private segmenter: ImageSegmenter | null = null;
  private video: HTMLVideoElement | null = null;
  private output: HTMLCanvasElement | null = null;
  private texture: HTMLCanvasElement | null = null;
  private source: Point[] | null = null;
  private readonly frame = document.createElement('canvas');
  private readonly overlay = document.createElement('canvas');
  private readonly maskCanvas = document.createElement('canvas');
  private maskData: ImageData | null = null;
  private readonly tracker = new PoseTracker();
  private token = 0;
  private raf: number | null = null;
  private lastVideoTime = -1;
  private lastFrameAt = -Infinity;
  private interval = 40;
  private lastStatus = '';
  private errors = 0;

  constructor(private readonly callbacks: Callbacks) { }
  setGarment(texture: HTMLCanvasElement | null): void { this.texture = texture; this.source = null; this.coverageLayer = null; this.contourFitter.clear(); }
  setCalibration(points: readonly Point[]): void {
    const error = validateCalibration(points, this.profile); if (error) throw new Error(error);
    if (!this.texture) throw new Error('Primero carga la prenda.');
    const layer = new ClothingCoverageLayer(this.texture, points, this.profile);
    this.source = clonePoints(points); this.coverageLayer = layer; this.contourFitter.clear();
  }
  recalibrate(): void { this.source = null; this.coverageLayer = null; this.contourFitter.clear(); }
  recenter(): void { this.tracker.clear(); this.contourFitter.clear(); this.lastVideoTime = -1; }

  async start(video: HTMLVideoElement, output: HTMLCanvasElement): Promise<void> {
    if (!navigator.mediaDevices?.getUserMedia) throw new Error('La cámara requiere HTTPS o localhost y un navegador compatible.');
    if (GarmentTryOnEngine.active && GarmentTryOnEngine.active !== this) GarmentTryOnEngine.active.stop();
    this.stop(false); GarmentTryOnEngine.active = this;
    const token = this.token; this.video = video; this.output = output;
    this.setStatus('Solicitando cámara...');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 30, max: 30 } }, audio: false });
      if (token !== this.token) { stream.getTracks().forEach(t => t.stop()); return; }
      this.stream = stream; video.srcObject = stream; await video.play();
      if (token !== this.token) return;
      this.setStatus('Cargando seguimiento corporal...');
      const files = await FilesetResolver.forVisionTasks(WASM_URL);
      if (token !== this.token) return;
      let pose: PoseLandmarker;
      const options = { runningMode: 'VIDEO' as const, numPoses: 1, minPoseDetectionConfidence: 0.6, minPosePresenceConfidence: 0.6, minTrackingConfidence: 0.6 };
      try { pose = await PoseLandmarker.createFromOptions(files, { ...options, baseOptions: { modelAssetPath: POSE_URL, delegate: 'GPU' } }); }
      catch {
        if (token !== this.token) return;
        pose = await PoseLandmarker.createFromOptions(files, { ...options, baseOptions: { modelAssetPath: POSE_URL, delegate: 'CPU' } });
      }
      if (token !== this.token) { pose.close(); return; }
      this.pose = pose;
      this.setStatus('Cargando contorno de ropa y máscara de piel...');
      try {
        const segmenter = await ImageSegmenter.createFromOptions(files, {
          baseOptions: { modelAssetPath: MASK_URL, delegate: 'CPU' }, runningMode: 'VIDEO', outputCategoryMask: true, outputConfidenceMasks: false,
        });
        if (token !== this.token) { segmenter.close(); return; }
        this.segmenter = segmenter;
      } catch {
        if (token !== this.token) return;
        this.callbacks.warning('No se pudo cargar la segmentación. Usa los ajustes manuales: la cobertura automática y la máscara de manos no están disponibles.');
      }
      if (token !== this.token) return;
      this.lastFrameAt = -Infinity; this.lastVideoTime = -1; this.interval = 40; this.errors = 0;
      this.raf = requestAnimationFrame(this.tick);
    } catch (error) {
      if (token !== this.token) return;
      this.stop(false); throw error;
    }
  }

  stop(notify = true): void {
    this.token++;
    if (this.raf !== null) cancelAnimationFrame(this.raf);
    this.raf = null;
    this.stream?.getTracks().forEach(t => t.stop()); this.stream = null;
    if (this.video) { this.video.pause(); this.video.srcObject = null; }
    this.video = null;
    this.pose?.close(); this.pose = null;
    this.segmenter?.close(); this.segmenter = null;
    this.output?.getContext('2d')?.clearRect(0, 0, this.output.width, this.output.height);
    this.output = null; this.tracker.clear(); this.contourFitter.clear();
    if (GarmentTryOnEngine.active === this) GarmentTryOnEngine.active = null;
    if (notify) this.callbacks.stopped();
  }

  private setStatus(text: string): void {
    if (text === this.lastStatus) return;
    this.lastStatus = text; this.callbacks.status(text);
  }

  private tick = (now: number): void => {
    const video = this.video, canvas = this.output, pose = this.pose;
    if (!video || !canvas || !pose) return;
    if (video.readyState >= 2 && video.videoWidth && video.currentTime !== this.lastVideoTime && now - this.lastFrameAt >= this.interval) {
      this.lastVideoTime = video.currentTime; this.lastFrameAt = now;
      const started = performance.now();
      try { this.renderFrame(video, canvas, pose, now); this.errors = 0; }
      catch (error) {
        this.callbacks.warning(error instanceof Error ? error.message : 'No se pudo procesar la cámara.');
        if (++this.errors >= 3) { this.setStatus('Se detuvo el seguimiento. Cierra y vuelve a abrir el vestidor.'); this.stop(false); return; }
      }
      this.interval = clamp((performance.now() - started) * 1.1, 33, 180);
    }
    this.raf = requestAnimationFrame(this.tick);
  };

  private renderFrame(video: HTMLVideoElement, canvas: HTMLCanvasElement, pose: PoseLandmarker, now: number): void {
    const scale = Math.min(1, 640 / video.videoWidth);
    const w = Math.round(video.videoWidth * scale), h = Math.round(video.videoHeight * scale);
    for (const c of [this.frame, this.overlay, canvas]) if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
    const frameCtx = this.frame.getContext('2d')!, ctx = canvas.getContext('2d')!, overlayCtx = this.overlay.getContext('2d')!;
    frameCtx.drawImage(video, 0, 0, w, h);
    const result = pose.detectForVideo(this.frame, now);
    this.tracker.update(result.landmarks[0] ?? [], now);
    ctx.save(); ctx.translate(w, 0); ctx.scale(-1, 1); ctx.drawImage(this.frame, 0, 0); ctx.restore();
    overlayCtx.clearRect(0, 0, w, h);
    if (!this.texture) { this.setStatus('Selecciona una prenda con fondo transparente.'); return; }
    if (!this.source) { this.setStatus(`Ajusta los ${calibrationHandles(this.profile).length} puntos de esta prenda y guarda la calibración.`); return; }
    const mesh = buildTargetMesh(this.tracker, now, w, h, this.fit, this.profile);
    if (!mesh) { this.setStatus(this.profile.category === 'dress' ? (this.fit.skirtLength > 1.05 ? 'Aléjate: muestra hombros, cadera, rodillas y tobillos.' : 'Aléjate: muestra hombros, cadera y rodillas.') : 'Ponte de frente y muestra los hombros y la cadera.'); return; }
    const mask = this.readSegmentation(now);
    const patches = createGarmentPatches(this.source, mesh, this.coverage ? mask : null, this.contourFitter, w, h, this.fit, now, this.profile);
    for (const patch of patches) {
      const source = patch.source.map(p => ({ x: p.x * this.texture!.width, y: p.y * this.texture!.height }));
      drawTexturedTriangle(overlayCtx, this.texture, source, patch.target);
    }
    if (this.coverage && mask) {
      this.coverageLayer?.fill(overlayCtx, mask, patches, this.tracker, now, this.fit, mesh);
      const bodyWidth = length(sub(mesh.points[1], mesh.points[0]));
      this.silhouetteClipper.apply(overlayCtx, mask, bodyWidth * this.fit.coverageMargin, patches.filter(p => p.part === 'skirt'));
    }
    if (mask) this.applyOcclusion(overlayCtx, mask, now, w, h);
    ctx.drawImage(this.overlay, 0, 0);
    if (this.debug) {
      for (const patch of patches) drawWireframe(ctx, patch.target, [[0, 1, 2]]);
      const ls = this.tracker.get(11, now)!, rs = this.tracker.get(12, now)!;
      const lh = this.tracker.get(23, now)!, rh = this.tracker.get(24, now)!;
      const center = mix(mix(ls, rs), mix(lh, rh), this.fit.coverageHem);
      const origin = { x: center.x * w, y: center.y * h };
      const body = sub({ x: (lh.x + rh.x) * w / 2, y: (lh.y + rh.y) * h / 2 }, { x: (ls.x + rs.x) * w / 2, y: (ls.y + rs.y) * h / 2 });
      const normal = unit({ x: -body.y, y: body.x });
      const start = add(origin, normal, -w * 0.3), end = add(origin, normal, w * 0.3);
      ctx.save(); ctx.strokeStyle = '#f97316'; ctx.lineWidth = 3; ctx.setLineDash([8, 5]);
      ctx.beginPath(); ctx.moveTo(start.x, start.y); ctx.lineTo(end.x, end.y); ctx.stroke(); ctx.restore();
    }
    this.setStatus(this.profile.sleeves === 'none' || (mesh.leftArm && mesh.rightArm)
      ? (this.coverage && mask ? 'Cobertura activa. Ajusta el límite inferior al final de tu prenda.' : 'Ajuste manual. Puedes modificar ancho de torso, mangas y puños.')
      : (this.profile.sleeves === 'short' ? 'Muestra los codos para colocar las mangas cortas.' : 'Muestra codos y muñecas para colocar las mangas largas.'));
  }

  private readSegmentation(now: number): ClothingSnapshot | null {
    if (!this.segmenter) return null;
    let snapshot: ClothingSnapshot | null = null;
    try {
      this.segmenter.segmentForVideo(this.frame, now, result => {
        const mask = result.categoryMask;
        if (mask) snapshot = { data: new Uint8Array(mask.getAsUint8Array()), width: mask.width, height: mask.height };
      });
    } catch {
      this.segmenter.close(); this.segmenter = null; this.contourFitter.clear();
      this.callbacks.warning('La segmentación falló. Continúa el ajuste manual, sin cobertura automática ni máscara de manos.');
    }
    return snapshot;
  }

  private applyOcclusion(ctx: CanvasRenderingContext2D, mask: ClothingSnapshot, now: number, w: number, h: number): void {
    const hands: Point[][] = [];
    for (const indices of [[15, 17, 19, 21], [16, 18, 20, 22]]) {
      const points = indices.map(i => this.tracker.get(i, now));
      if (points.some(p => !p || now - p.seenAt > 80)) continue;
      const valid = points as TrackedPoint[];
      const center = valid.reduce((a, p) => add(a, p, 0.25), { x: 0, y: 0 });
      hands.push(convexHull(valid.map(p => add(center, sub(p, center), 1.35))));
    }
    const ls = this.tracker.get(11, now), rs = this.tracker.get(12, now);
    const neck: Point[] = [];
    if (ls && rs) {
      const left = mix(ls, rs, 0.30), right = mix(ls, rs, 0.70), rise = Math.abs(rs.x - ls.x) * w / h * 0.6;
      neck.push({ x: left.x, y: left.y - rise }, { x: right.x, y: right.y - rise }, { x: right.x, y: right.y + rise * 0.18 }, { x: left.x, y: left.y + rise * 0.18 });
    }
    {
      if (!this.maskData || this.maskCanvas.width !== mask.width || this.maskCanvas.height !== mask.height) {
        this.maskCanvas.width = mask.width; this.maskCanvas.height = mask.height;
        this.maskData = new ImageData(mask.width, mask.height);
      }
      const labels = mask.data, data = this.maskData.data;
      data.fill(0);
      for (let i = 0; i < labels.length; i++) {
        const label = labels[i];
        // Do NOT erase all skin: bare forearms must be covered by a long sleeve.
        const position = { x: 1 - (i % mask.width + 0.5) / mask.width, y: (Math.floor(i / mask.width) + 0.5) / mask.height };
        const skin = label === 2 && (inside(position, neck) || hands.some(polygon => inside(position, polygon)));
        if (label === 1 || label === 3 || skin) data[i * 4 + 3] = 255;
      }
      this.maskCanvas.getContext('2d')!.putImageData(this.maskData, 0, 0);
      ctx.save(); ctx.globalCompositeOperation = 'destination-out';
      ctx.translate(w, 0); ctx.scale(-1, 1); ctx.drawImage(this.maskCanvas, 0, 0, w, h); ctx.restore();
    }
  }
}
