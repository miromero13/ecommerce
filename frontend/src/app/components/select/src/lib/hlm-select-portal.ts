import { DialogRef } from '@angular/cdk/dialog';
import { Directive, effect, inject } from '@angular/core';
import { BrnPopoverContent } from '@spartan-ng/brain/popover';
import { injectBrnSelectBase } from '@spartan-ng/brain/select';

@Directive({
  selector: '[hlmSelectPortal]',
  hostDirectives: [{ directive: BrnPopoverContent, inputs: ['context', 'class'] }],
})
export class HlmSelectPortal {}

@Directive({
  selector: '[hlmSelectPanel]',
})
export class HlmSelectPanel {
  private readonly dialogRef = inject(DialogRef);
  private readonly select = injectBrnSelectBase();

  constructor() {
    effect(() => {
      const width = this.select.triggerWidth();

      if (width) {
        this.dialogRef.updateSize(`${width}px`);
      }
    });
  }
}
