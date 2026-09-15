import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
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
        type="button"
        class="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
        (click)="toggleMenu.emit()"
        aria-label="Abrir acciones"
      >
        <ng-icon name="lucideMoreVertical" />
      </button>

      @if (isOpen) {
        <div class="absolute left-1/2 top-full z-20 mt-2 min-w-44 -translate-x-1/2 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg">
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
  @Input() isOpen = false;
  @Input() activeLabel = 'Activar';
  @Input() showActive = true;
  @Input() showProducts = false;

  @Output() toggleMenu = new EventEmitter<void>();
  @Output() edit = new EventEmitter<void>();
  @Output() toggleActive = new EventEmitter<void>();
  @Output() delete = new EventEmitter<void>();
  @Output() viewProducts = new EventEmitter<void>();
}
