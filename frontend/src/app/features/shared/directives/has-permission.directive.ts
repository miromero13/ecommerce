import {
  Directive,
  Input,
  TemplateRef,
  ViewContainerRef,
  effect,
  inject,
} from '@angular/core';
import { SessionService } from '../services/session.service';

@Directive({
  selector: '[hasPermission]',
  standalone: true,
})
export class HasPermissionDirective {
  private readonly templateRef = inject(TemplateRef<unknown>);
  private readonly viewContainer = inject(ViewContainerRef);
  private readonly sessionService = inject(SessionService);

  private requiredPermission = '';
  private isVisible = false;

  @Input()
  set hasPermission(permission: string) {
    this.requiredPermission = permission;
    this.updateView();
  }

  constructor() {
    effect(() => {
      // Re-evaluate whenever session user changes
      this.sessionService.user();
      this.updateView();
    });
  }

  private updateView(): void {
    if (!this.requiredPermission) {
      if (!this.isVisible) {
        this.viewContainer.createEmbeddedView(this.templateRef);
        this.isVisible = true;
      }
      return;
    }

    const hasPerm = this.sessionService.hasPermission(this.requiredPermission);
    if (hasPerm && !this.isVisible) {
      this.viewContainer.createEmbeddedView(this.templateRef);
      this.isVisible = true;
    } else if (!hasPerm && this.isVisible) {
      this.viewContainer.clear();
      this.isVisible = false;
    }
  }
}
