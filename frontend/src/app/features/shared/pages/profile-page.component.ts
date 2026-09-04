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
  protected readonly userRoleLabel = signal('');

  constructor() {
    effect(() => {
      const currentUser = this.session.user();
      this.user.set(currentUser);

      if (!currentUser) {
        this.userRoleLabel.set('');
        return;
      }

      switch (currentUser.rol) {
        case 'administrador':
          this.userRoleLabel.set('Administrador');
          break;
        case 'proveedor':
          this.userRoleLabel.set('Proveedor');
          break;
        case 'encargado':
          this.userRoleLabel.set('Encargado');
          break;
        case 'cajero':
          this.userRoleLabel.set('Cajero');
          break;
        case 'delivery':
          this.userRoleLabel.set('Delivery');
          break;
        default:
          this.userRoleLabel.set('Cliente');
      }
    });
  }
}
