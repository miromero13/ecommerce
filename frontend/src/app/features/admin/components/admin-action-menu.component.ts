import { CommonModule } from '@angular/common';
import { Component, ElementRef, EventEmitter, Input, Output, ViewChild } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideMoreVertical, lucidePencil, lucidePower, lucideTrash2, lucidePackageSearch } from '@ng-icons/lucide';

@Component({
  selector: 'app-admin-action-menu',
  standalone: true,
  imports: [CommonModule, NgIcon],
  providers: [provideIcons({ lucideMoreVertical, lucidePencil, lucidePower, lucideTrash2, lucidePackageSearch })],
  template: `
    <div class="relative flex w-full items-center justify-center">
      <button
        #triggerButton
        type="button"
        class="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
        (click)="toggle()"
        aria-label="Abrir acciones"
      >
        <ng-icon name="lucideMoreVertical" />
      </button>

      @if (isOpen) {
        <div
          class="fixed z-50 min-w-44 -translate-x-1/2 overflow-y-auto rounded-lg border border-slate-200 bg-white shadow-lg"
          [style.top.px]="menuPosition.top"
          [style.left.px]="menuPosition.left"
          [style.max-height.px]="menuPosition.maxHeight"
        >
          <button type="button" class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50" (click)="edit.emit()">
            <ng-icon name="lucidePencil" />
            <span>Editar</span>
          </button>
           @if (showActive) {
            <button type="button" class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50" (click)="toggleActive.emit()">
              <ng-icon name="lucidePower" />
              <span>{{ activeLabel }}</span>
            </button>
           }
           @if (showProducts) {
             <button type="button" class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50" (click)="viewProducts.emit()">
               <ng-icon name="lucidePackageSearch" />
               <span>Ver productos</span>
             </button>
           }
          <button type="button" class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-red-700 hover:bg-red-50" (click)="delete.emit()">
            <ng-icon name="lucideTrash2" />
            <span>Eliminar</span>
          </button>
        </div>
      }
    </div>
  `,
})
export class AdminActionMenuComponent {
  @ViewChild('triggerButton') private triggerButton?: ElementRef<HTMLButtonElement>;

  @Input() isOpen = false;
  @Input() activeLabel = 'Activar';
  @Input() showActive = true;
  @Input() showProducts = false;

  @Output() toggleMenu = new EventEmitter<void>();
  @Output() edit = new EventEmitter<void>();
  @Output() toggleActive = new EventEmitter<void>();
  @Output() delete = new EventEmitter<void>();
  @Output() viewProducts = new EventEmitter<void>();

  protected menuPosition = { top: 0, left: 0, maxHeight: 0 };

  protected toggle(): void {
    if (!this.isOpen) {
      const rect = this.triggerButton?.nativeElement.getBoundingClientRect();
      if (rect) {
        const estimatedHeight = this.showProducts ? (this.showActive ? 176 : 144) : this.showActive ? 144 : 112;
        const spaceBelow = window.innerHeight - rect.bottom - 8;
        const openAbove = spaceBelow < estimatedHeight && rect.top > estimatedHeight;
        const top = openAbove ? Math.max(8, rect.top - estimatedHeight) : rect.bottom + 8;

        this.menuPosition = {
          top,
          left: rect.left + rect.width / 2,
          maxHeight: Math.max(80, openAbove ? rect.top - top - 8 : window.innerHeight - top - 8),
        };
      }
    }

    this.toggleMenu.emit();
  }
}
