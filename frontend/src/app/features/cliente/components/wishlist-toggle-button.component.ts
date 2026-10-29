import { Component, Input, OnInit, computed, inject, signal } from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideHeart } from '@ng-icons/lucide';
import { toast } from '@spartan-ng/brain/sonner';

import { getErrorMessage } from '../../../core/utils/http-error.util';
import { WishlistApiService } from '../../shared/services/wishlist-api.service';

/** CU16 heart button: adds or removes a garment from the customer's wishlist. */
@Component({
  selector: 'app-wishlist-toggle-button',
  standalone: true,
  imports: [NgIcon],
  providers: [provideIcons({ lucideHeart })],
  template: `
    @if (wishlist.canUse()) {
      <button
        type="button"
        class="flex size-9 cursor-pointer items-center justify-center rounded-full bg-white/90 shadow-sm transition hover:scale-105"
        [class.text-rose-600]="saved()"
        [class.text-slate-500]="!saved()"
        [attr.aria-pressed]="saved()"
        [attr.aria-label]="saved() ? 'Quitar de mi lista de deseos' : 'Añadir a mi lista de deseos'"
        [disabled]="busy()"
        (click)="toggle($event)"
      >
        <ng-icon name="lucideHeart" [style.fill]="saved() ? 'currentColor' : 'none'" />
      </button>
    }
  `,
})
export class WishlistToggleButtonComponent implements OnInit {
  protected readonly wishlist = inject(WishlistApiService);
  @Input({ required: true }) productId!: string;
  protected readonly busy = signal(false);
  protected readonly saved = computed(() => this.wishlist.savedIds().has(this.productId));

  ngOnInit(): void {
    void this.wishlist.ensureLoaded();
  }

  protected async toggle(event: Event): Promise<void> {
    event.stopPropagation(); // the card itself opens the product detail
    this.busy.set(true);
    try {
      toast.success(await this.wishlist.toggle(this.productId));
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo actualizar tu lista de deseos.'));
    } finally {
      this.busy.set(false);
    }
  }
}
