import { CommonModule } from '@angular/common';
import { Component, effect, inject, signal } from '@angular/core';

import { SessionService } from '../services/session.service';

@Component({
  selector: 'app-profile-page',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './profile-page.component.html',
})
export class ProfilePageComponent {
  private readonly session = inject(SessionService);

  protected readonly user = signal(this.session.user());

  constructor() {
    effect(() => {
      this.user.set(this.session.user());
    });
  }
}
