import { BooleanInput } from '@angular/cdk/coercion';
import {
  booleanAttribute,
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
} from '@angular/core';
import { hlm } from '@spartan-ng/helm/utils';
import { HlmSelectPanel, HlmSelectPortal } from './hlm-select-portal';
import { HlmSelectScrollDown } from './hlm-select-scroll-down';
import { HlmSelectScrollUp } from './hlm-select-scroll-up';

@Component({
  selector: 'hlm-select-content',
  imports: [HlmSelectPanel, HlmSelectPortal, HlmSelectScrollUp, HlmSelectScrollDown],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <ng-template hlmSelectPortal [class]="_computedContentClasses()">
      <div hlmSelectPanel>
        @if (showScroll()) {
          <hlm-select-scroll-up />
        }

        <div role="listbox" [class]="_computedListboxClasses()">
          <ng-content />
        </div>

        @if (showScroll()) {
          <hlm-select-scroll-down />
        }
      </div>
    </ng-template>
  `,
})
export class HlmSelectContent {
  protected readonly _computedContentClasses = computed(() =>
    hlm(
      'bg-background p-1 no-scrollbar text-foreground data-open:animate-in data-closed:animate-out data-closed:fade-out-0 data-open:fade-in-0 data-closed:zoom-out-95 data-open:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 ring-foreground/10 relative isolate flex max-h-72 w-auto min-w-36 flex-col overflow-x-hidden overflow-y-auto rounded-md shadow-md ring-1 duration-100',
    ),
  );

  protected readonly _computedListboxClasses = computed(() =>
    hlm('flex min-w-0 flex-col [&_[data-slot=select-item]]:break-words'),
  );

  public readonly showScroll = input<boolean, BooleanInput>(false, { transform: booleanAttribute });
}
