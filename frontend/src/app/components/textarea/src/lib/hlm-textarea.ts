import { Directive } from '@angular/core';
import { BrnFieldControlDescribedBy } from '@spartan-ng/brain/field';
import { classes } from '@spartan-ng/helm/utils';

@Directive({
  selector: 'textarea[hlmTextarea]',
  hostDirectives: [BrnFieldControlDescribedBy],
})
export class HlmTextarea {
  constructor() {
    classes(
      () =>
        'border-input placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 dark:bg-input/30 flex min-h-20 w-full rounded-md border bg-transparent px-3 py-2 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50',
    );
  }
}
