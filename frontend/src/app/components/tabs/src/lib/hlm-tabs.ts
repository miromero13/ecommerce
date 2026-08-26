import { Directive, input } from '@angular/core';
import { BrnTabs, BrnTabsList, BrnTabsTrigger } from '@spartan-ng/brain/tabs';
import { classes } from '@spartan-ng/helm/utils';

@Directive({
  selector: '[hlmTabs],hlm-tabs',
  hostDirectives: [
    {
      directive: BrnTabs,
      inputs: ['orientation', 'activationMode', 'brnTabs: tab'],
      outputs: ['tabActivated'],
    },
  ],
  host: {
    'data-slot': 'tabs',
  },
})
export class HlmTabs {
  public readonly tab = input.required<string>();

  constructor() {
    classes(() => 'group/tabs flex w-full flex-col gap-3');
  }
}

@Directive({
  selector: '[hlmTabsList],hlm-tabs-list',
  hostDirectives: [BrnTabsList],
  host: {
    'data-slot': 'tabs-list',
  },
})
export class HlmTabsList {
  constructor() {
    classes(() => 'grid w-full grid-cols-3 rounded-2xl border border-border bg-card/80 p-0.5 backdrop-blur');
  }
}

@Directive({
  selector: '[hlmTabsTrigger]',
  hostDirectives: [{ directive: BrnTabsTrigger, inputs: ['brnTabsTrigger: hlmTabsTrigger', 'disabled'] }],
  host: {
    'data-slot': 'tabs-trigger',
  },
})
export class HlmTabsTrigger {
  public readonly triggerFor = input.required<string>({ alias: 'hlmTabsTrigger' });

  constructor() {
    classes(() => [
      'flex min-h-12 flex-col items-center justify-center gap-0.5 rounded-xl px-2 py-1.5 text-center text-sm font-medium transition',
      'text-muted-foreground hover:bg-primary/60 hover:text-white data-active:bg-primary data-active:text-primary-foreground data-active:shadow-sm',
      'disabled:pointer-events-none disabled:opacity-50',
    ]);
  }
}

export const HlmTabsImports = [HlmTabs, HlmTabsList, HlmTabsTrigger] as const;
