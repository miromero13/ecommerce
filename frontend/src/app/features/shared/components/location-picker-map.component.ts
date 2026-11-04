import { CommonModule } from '@angular/common';
import {
  AfterViewInit,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  OnDestroy,
  Output,
  SimpleChanges,
  ViewChild,
  signal,
} from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideCrosshair, lucideMapPin } from '@ng-icons/lucide';
import * as L from 'leaflet';

const BOLIVIA_CITIES: { name: string; lat: number; lng: number }[] = [
  { name: 'La Paz', lat: -16.4990, lng: -68.1337 },
  { name: 'Santa Cruz', lat: -17.7833, lng: -63.1821 },
  { name: 'Cochabamba', lat: -17.3935, lng: -66.1570 },
];

@Component({
  selector: 'app-location-picker-map',
  standalone: true,
  imports: [CommonModule, NgIcon],
  providers: [
    provideIcons({
      lucideMapPin,
      lucideCrosshair,
    }),
  ],
  template: `
    <div class="space-y-2">
      <div class="flex items-center justify-between text-xs">
        <span class="font-medium text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
          <ng-icon name="lucideMapPin" class="text-primary w-4 h-4"></ng-icon>
          {{ label }}
        </span>

        <!-- Botón Mi ubicación -->
        <button
          *ngIf="!readonly"
          type="button"
          (click)="locateUser()"
          class="inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:underline bg-primary/5 hover:bg-primary/10 px-2 py-0.5 rounded transition-colors"
        >
          <ng-icon name="lucideCrosshair" class="w-3.5 h-3.5"></ng-icon>
          Usar mi ubicación
        </button>
      </div>

      <!-- Quick jump cities (helpful for testing and quick navigation) -->
      <div *ngIf="!readonly" class="flex flex-wrap items-center gap-1 text-[11px] text-muted-foreground">
        <span>Ir a:</span>
        <button
          *ngFor="let city of cities"
          type="button"
          (click)="flyToCity(city.lat, city.lng)"
          class="px-1.5 py-0.5 rounded border border-border bg-card hover:bg-muted text-foreground transition-colors"
        >
          {{ city.name }}
        </button>
      </div>

      <!-- Map Container -->
      <div class="relative rounded-lg overflow-hidden border border-border shadow-inner bg-slate-100 dark:bg-slate-800">
        <div #mapContainer [style.height]="height" class="w-full z-0"></div>

        <!-- Coordinates overlay -->
        <div
          *ngIf="currentLat() !== null && currentLng() !== null"
          class="absolute bottom-2 left-2 z-[400] bg-white/90 dark:bg-slate-900/90 backdrop-blur-sm text-[11px] font-mono px-2 py-1 rounded border shadow-sm text-slate-700 dark:text-slate-300"
        >
          {{ currentLat() | number:'1.5-5' }}, {{ currentLng() | number:'1.5-5' }}
        </div>
      </div>

      <p *ngIf="!readonly" class="text-[11px] text-muted-foreground">
        Hacé clic en el mapa o arrastrá el marcador para definir la ubicación exacta de entrega.
      </p>
    </div>
  `,
})
export class LocationPickerMapComponent implements AfterViewInit, OnChanges, OnDestroy {
  @ViewChild('mapContainer', { static: true }) mapContainer!: ElementRef<HTMLDivElement>;

  @Input() latitude: number | null = null;
  @Input() longitude: number | null = null;
  @Input() height = '220px';
  @Input() readonly = false;
  @Input() label = 'Ubicación en el mapa';

  @Output() locationChange = new EventEmitter<{ latitude: number; longitude: number }>();

  protected readonly currentLat = signal<number | null>(null);
  protected readonly currentLng = signal<number | null>(null);
  protected readonly cities = BOLIVIA_CITIES;

  private map: L.Map | null = null;
  private marker: L.Marker | null = null;

  private readonly pinIcon = L.divIcon({
    className: 'custom-leaflet-marker',
    html: `
      <div style="position: absolute; transform: translate(-50%, -100%);">
        <svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 24 24" fill="#0f766e" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">
          <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
          <circle cx="12" cy="10" r="3" fill="#ffffff"/>
        </svg>
      </div>
    `,
    iconSize: [0, 0],
    iconAnchor: [0, 0],
  });

  ngAfterViewInit(): void {
    this.initMap();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if ((changes['latitude'] || changes['longitude']) && this.map) {
      this.updateMarkerFromInputs();
    }
  }

  ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
  }

  private initMap(): void {
    const initialLat = this.latitude ?? -16.4990;
    const initialLng = this.longitude ?? -68.1337;
    const initialZoom = this.latitude && this.longitude ? 15 : 13;

    this.map = L.map(this.mapContainer.nativeElement, {
      center: [initialLat, initialLng],
      zoom: initialZoom,
      zoomControl: true,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap contributors',
    }).addTo(this.map);

    if (this.latitude !== null && this.longitude !== null) {
      this.placeMarker(this.latitude, this.longitude);
    }

    if (!this.readonly) {
      this.map.on('click', (e: L.LeafletMouseEvent) => {
        const lat = Number(e.latlng.lat.toFixed(6));
        const lng = Number(e.latlng.lng.toFixed(6));
        this.placeMarker(lat, lng);
        this.locationChange.emit({ latitude: lat, longitude: lng });
      });
    }

    // Leaflet needs invalidateSize once rendered in tabs/modals
    setTimeout(() => {
      this.map?.invalidateSize();
    }, 200);
  }

  private placeMarker(lat: number, lng: number): void {
    if (!this.map) return;

    this.currentLat.set(lat);
    this.currentLng.set(lng);

    if (this.marker) {
      this.marker.setLatLng([lat, lng]);
    } else {
      this.marker = L.marker([lat, lng], {
        icon: this.pinIcon,
        draggable: !this.readonly,
      }).addTo(this.map);

      if (!this.readonly) {
        this.marker.on('dragend', () => {
          if (!this.marker) return;
          const pos = this.marker.getLatLng();
          const latFixed = Number(pos.lat.toFixed(6));
          const lngFixed = Number(pos.lng.toFixed(6));
          this.currentLat.set(latFixed);
          this.currentLng.set(lngFixed);
          this.locationChange.emit({ latitude: latFixed, longitude: lngFixed });
        });
      }
    }
  }

  private updateMarkerFromInputs(): void {
    if (this.latitude !== null && this.longitude !== null) {
      this.placeMarker(this.latitude, this.longitude);
      this.map?.setView([this.latitude, this.longitude], this.map.getZoom());
    } else if (this.marker && this.map) {
      this.map.removeLayer(this.marker);
      this.marker = null;
      this.currentLat.set(null);
      this.currentLng.set(null);
    }
  }

  protected flyToCity(lat: number, lng: number): void {
    if (!this.map) return;
    this.map.flyTo([lat, lng], 14, { duration: 1 });
    this.placeMarker(lat, lng);
    this.locationChange.emit({ latitude: lat, longitude: lng });
  }

  protected locateUser(): void {
    if (!navigator.geolocation) {
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = Number(pos.coords.latitude.toFixed(6));
        const lng = Number(pos.coords.longitude.toFixed(6));
        if (this.map) {
          this.map.flyTo([lat, lng], 16, { duration: 1.2 });
          this.placeMarker(lat, lng);
          this.locationChange.emit({ latitude: lat, longitude: lng });
        }
      },
      (err) => {
        console.warn('Geolocation error:', err);
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }
}
