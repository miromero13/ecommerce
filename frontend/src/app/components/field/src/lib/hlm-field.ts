import { BooleanInput } from '@angular/cdk/coercion';
import { BrnField, BrnFieldA11yService } from '@spartan-ng/brain/field';
import { ChangeDetectionStrategy, Component, Directive, EffectRef, OnDestroy, booleanAttribute, computed, effect, inject, input } from '@angular/core';
import { HlmLabel } from '@spartan-ng/helm/label';
import { HlmSeparator } from '@spartan-ng/helm/separator';
import { VariantProps, cva } from 'class-variance-authority';
import { classes } from '@spartan-ng/helm/utils';

@Directive({
	selector: '[hlmFieldContent],hlm-field-content',
	host: { 'data-slot': 'field-content' },
})
export class HlmFieldContent {
	constructor() {
		classes(() => 'gap-1 group/field-content flex flex-1 flex-col leading-snug');
	}
}

@Directive({
	selector: '[hlmFieldDescription],hlm-field-description',
	host: {
		'data-slot': 'field-description',
		'[attr.id]': 'id()',
	},
})
export class HlmFieldDescription implements OnDestroy {
	private static _id = 0;

	private readonly _a11y = inject(BrnFieldA11yService, { optional: true, host: true });

	public readonly id = input<string>(`hlm-field-description-${HlmFieldDescription._id++}`);

	private _registeredId?: string;

	private readonly _cleanup: EffectRef | null = this._a11y
		? effect(() => {
				const a11y = this._a11y;
				if (!a11y) return;

				const id = this.id();
				if (this._registeredId && this._registeredId !== id) {
					a11y.unregisterDescription(this._registeredId);
				}

				if (this._registeredId !== id) {
					a11y.registerDescription(id);
					this._registeredId = id;
				}
			})
		: null;

	constructor() {
		classes(() => [
			'text-muted-foreground text-start text-xs/relaxed [[data-variant=legend]+&]:-mt-1.5 leading-normal font-normal group-has-data-horizontal/field:text-balance',
			'last:mt-0 nth-last-2:-mt-1',
			'[&>a:hover]:text-primary [&>a]:underline [&>a]:underline-offset-4',
		]);
	}

	ngOnDestroy() {
		this._cleanup?.destroy();

		if (this._registeredId) {
			this._a11y?.unregisterDescription(this._registeredId);
		}
	}
}

@Component({
	selector: 'hlm-field-error',
	changeDetection: ChangeDetectionStrategy.OnPush,
	host: {
		role: 'alert',
		'data-slot': 'field-error',
		'[attr.id]': 'id()',
		'[hidden]': '!_display()',
	},
	template: `
		@if (_display()) {
			<ng-content />
		}
	`,
})
export class HlmFieldError implements OnDestroy {
	private static _id = 0;

	private readonly _field = inject(BrnField, { optional: true });
	private readonly _a11y = inject(BrnFieldA11yService, { optional: true, host: true });

	private _registeredId?: string | undefined;

	private readonly _hasParentField = !!this._field;

	public readonly id = input<string>(`hlm-field-error-${HlmFieldError._id++}`);

	public readonly validator = input<string>();

	public readonly forceShow = input<boolean, BooleanInput>(false, { transform: booleanAttribute });

	protected readonly _display = computed(() => !this._hasParentField || this.forceShow() || this._hasError());

	protected readonly _hasError = computed(() => {
		const errors = this._field?.errors();
		if (!errors) return false;

		const validator = this.validator();
		const spartanInvalid = this._field?.controlState()?.spartanInvalid;

		if (!spartanInvalid) return false;

		return validator ? validator in errors : Object.keys(errors).length > 0;
	});

	private readonly _cleanup: EffectRef | null = this._a11y
		? effect(() => {
				const a11y = this._a11y;
				if (!a11y) return;

				const id = this.id();
				const hasError = this._hasError();

				if (this._registeredId && (this._registeredId !== id || !hasError)) {
					a11y.unregisterError(this._registeredId);
					this._registeredId = undefined;
				}

				if (hasError && this._registeredId !== id) {
					a11y.registerError(id);
					this._registeredId = id;
				}
			})
		: null;

	constructor() {
		classes(() => 'text-destructive text-xs font-normal');
	}

	ngOnDestroy() {
		this._cleanup?.destroy();

		if (this._registeredId) {
			this._a11y?.unregisterError(this._registeredId);
		}
	}
}

@Directive({
	selector: '[hlmFieldGroup],hlm-field-group',
	host: { 'data-slot': 'field-group' },
})
export class HlmFieldGroup {
	constructor() {
		classes(() => 'gap-5 data-[slot=checkbox-group]:gap-3 *:data-[slot=field-group]:gap-4 group/field-group @container/field-group flex w-full flex-col');
	}
}

@Directive({
	selector: '[hlmFieldLabel],hlm-field-label',
	hostDirectives: [HlmLabel],
	host: { 'data-slot': 'field-label' },
})
export class HlmFieldLabel {
	constructor() {
		classes(() => [
			'has-data-checked:bg-primary/5 has-data-checked:border-primary/30 dark:has-data-checked:border-primary/20 dark:has-data-checked:bg-primary/10 gap-2 leading-snug group-data-[disabled=true]/field:opacity-50 has-[>[data-slot=field]]:rounded-lg has-[>[data-slot=field]]:border *:data-[slot=field]:p-2.5 group/field-label peer/field-label flex w-fit',
			'has-[>[data-slot=field]]:w-full has-[>[data-slot=field]]:flex-col',
		]);
	}
}

@Directive({
	selector: 'legend[hlmFieldLegend]',
	host: {
		'data-slot': 'field-legend',
		'[attr.data-variant]': 'variant()',
	},
})
export class HlmFieldLegend {
	public readonly variant = input<'label' | 'legend'>('legend');

	constructor() {
		classes(() => 'mb-2.5 font-medium data-[variant=label]:text-xs data-[variant=legend]:text-sm');
	}
}

@Component({
	selector: 'hlm-field-separator',
	imports: [HlmSeparator],
	changeDetection: ChangeDetectionStrategy.OnPush,
	host: { 'data-slot': 'field-separator' },
	template: `
		<hlm-separator class="absolute inset-0 top-1/2" />
		<span data-slot="field-separator-content" class="text-muted-foreground px-2 bg-background relative mx-auto block w-fit">
			<ng-content />
		</span>
	`,
})
export class HlmFieldSeparator {
	constructor() {
		classes(() => '-my-2 h-5 text-xs group-data-[variant=outline]/field-group:-mb-2 relative');
	}
}

@Directive({
	selector: 'fieldset[hlmFieldSet]',
	host: { 'data-slot': 'field-set' },
})
export class HlmFieldSet {
	constructor() {
		classes(() => 'gap-4 has-[>[data-slot=checkbox-group]]:gap-3 has-[>[data-slot=radio-group]]:gap-3 flex flex-col');
	}
}

@Directive({
	selector: '[hlmFieldTitle],hlm-field-title',
	host: { 'data-slot': 'field-label' },
})
export class HlmFieldTitle {
	constructor() {
		classes(() => 'gap-2 text-xs/relaxed group-data-[disabled=true]/field:opacity-50 flex w-fit items-center');
	}
}

const fieldVariants = cva('data-[matches-spartan-invalid=true]:text-destructive gap-2 group/field flex w-full', {
	variants: {
		orientation: {
			vertical: 'flex-col *:w-full [&>.sr-only]:w-auto',
			horizontal: [
				'flex-row items-center',
				'*:data-[slot=field-label]:flex-auto',
				'has-[>[data-slot=field-content]]:items-start has-[>[data-slot=field-content]]:[&>[role=checkbox],[role=radio]]:mt-px',
			],
			responsive: [
				'flex-col *:w-full @md/field-group:flex-row @md/field-group:items-center @md/field-group:*:w-auto [&>.sr-only]:w-auto',
				'@md/field-group:*:data-[slot=field-label]:flex-auto',
				'@md/field-group:has-[>[data-slot=field-content]]:items-start @md/field-group:has-[>[data-slot=field-content]]:[&>[role=checkbox],[role=radio]]:mt-px',
			],
		},
	},
	defaultVariants: {
		orientation: 'vertical',
	},
});

export type FieldVariants = VariantProps<typeof fieldVariants>;

@Directive({
	selector: '[hlmField],hlm-field',
	hostDirectives: [{ directive: BrnField, inputs: ['data-invalid', 'forceInvalid'] }],
	host: {
		role: 'group',
		'data-slot': 'field',
		'[attr.data-orientation]': 'orientation()',
	},
})
export class HlmField {
	public readonly orientation = input<FieldVariants['orientation']>('vertical');

	constructor() {
		classes(() => fieldVariants({ orientation: this.orientation() }));
	}
}

export const HlmFieldImports = [
	HlmField,
	HlmFieldContent,
	HlmFieldDescription,
	HlmFieldError,
	HlmFieldGroup,
	HlmFieldLabel,
	HlmFieldLegend,
	HlmFieldSeparator,
	HlmFieldSet,
	HlmFieldTitle,
] as const;
