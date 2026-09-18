import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ChatbotUiService {
  private readonly closeRequestedSubject = new Subject<void>();

  readonly closeRequested$ = this.closeRequestedSubject.asObservable();

  requestClose(): void {
    this.closeRequestedSubject.next();
  }
}
