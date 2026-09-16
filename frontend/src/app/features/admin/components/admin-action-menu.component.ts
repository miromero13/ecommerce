import { CommonModule } from '@angular/common';
import { Component, ElementRef, EventEmitter, HostListener, Input, Output, ViewChild } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
 import { lucideMoreVertical, lucidePencil, lucidePower, lucideTrash2, lucidePackageSearch, lucideEye, lucideClipboardList } from '@ng-icons/lucide';

@Component({
  selector: 'app-admin-action-menu',
  standalone: true,
  imports: [CommonModule, NgIcon],
    providers: [provideIcons({ lucideMoreVertical, lucidePencil, lucidePower, lucideTrash2, lucidePackageSearch, lucideEye, lucideClipboardList })],
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
           @if (showEdit) {
             <button type="button" class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50" (click)="run(edit)">
               <ng-icon name="lucidePencil" />
               <span>{{ editLabel }}</span>
             </button>
           }
           @if (showActive) {
             <button type="button" class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50" (click)="run(toggleActive)">
              <ng-icon name="lucidePower" />
              <span>{{ activeLabel }}</span>
            </button>
           }
           @if (showProducts) {
               <button type="button" class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50" (click)="run(viewProducts)">
               <ng-icon name="lucidePackageSearch" />
               <span>Ver productos</span>
             </button>
           }
            @if (showView) {
             <button type="button" class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50" (click)="run(view)">
               <ng-icon name="lucideEye" />
               <span>Ver</span>
             </button>
            }
            @if (showRequest) {
              <button type="button" class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50" (click)="run(request)">
                <ng-icon name="lucideClipboardList" />
                <span>Solicitar</span>
              </button>
            }
           @if (showDelete) {
             <button type="button" class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-red-700 hover:bg-red-50" (click)="run(delete)">
               <ng-icon name="lucideTrash2" />
               <span>Eliminar</span>
             </button>
           }
        </div>
      }
    </div>
  `,
})
export class AdminActionMenuComponent {
  @ViewChild('triggerButton') private triggerButton?: ElementRef<HTMLButtonElement>;

  @Input() isOpen = false;
  @Input() activeLabel = 'Activar';
   @Input() editLabel = 'Editar';
   @Input() showEdit = true;
   @Input() showActive = true;
   @Input() showProducts = false;
   @Input() showView = false;
    @Input() showDelete = true;
    @Input() showRequest = false;

  @Output() toggleMenu = new EventEmitter<void>();
  @Output() edit = new EventEmitter<void>();
  @Output() toggleActive = new EventEmitter<void>();
  @Output() delete = new EventEmitter<void>();
   @Output() viewProducts = new EventEmitter<void>();
    @Output() view = new EventEmitter<void>();
    @Output() request = new EventEmitter<void>();

  protected menuPosition = { top: 0, left: 0, maxHeight: 0 };

  constructor(private readonly element: ElementRef<HTMLElement>) {}

  @HostListener('document:pointerdown', ['$event'])
  protected onDocumentPointerDown(event: PointerEvent): void {
    if (this.isOpen && !this.element.nativeElement.contains(event.target as Node)) this.toggleMenu.emit();
  }

  protected run(action: EventEmitter<void>): void {
    this.toggleMenu.emit();
    action.emit();
  }

  protected toggle(): void {
    if (!this.isOpen) {
      const rect = this.triggerButton?.nativeElement.getBoundingClientRect();
      if (rect) {
         const estimatedHeight = (this.showEdit ? 40 : 0) + (this.showActive ? 40 : 0) + (this.showProducts ? 40 : 0) + (this.showView ? 40 : 0) + (this.showRequest ? 40 : 0) + (this.showDelete ? 40 : 0);
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
