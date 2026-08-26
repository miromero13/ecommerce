import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { SessionService } from './features/shared/services/session.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  private readonly session = inject(SessionService);

  constructor() {
    void this.session.bootstrap();
  }
}
