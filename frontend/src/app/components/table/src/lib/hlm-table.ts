import { Directive } from '@angular/core';
import { classes } from '@spartan-ng/helm/utils';

@Directive({
  selector: 'table[hlmTable]',
})
export class HlmTable {
  constructor() {
    classes(
      () =>
        'w-full caption-bottom text-sm [&_tr]:border-b [&_tr]:data-[state=selected]:bg-muted [&_td]:p-4 [&_th]:h-12 [&_th]:px-4 [&_th]:text-left [&_th]:align-middle [&_th]:font-medium [&_tr:last-child]:border-0',
    );
  }
}
