import { Component, OnDestroy, output, signal } from '@angular/core';
import { toast } from '@spartan-ng/brain/sonner';

interface SpeechRecognitionEventLike extends Event {
  results: { [index: number]: { [index: number]: { transcript: string } } };
}
interface SpeechRecognitionLike {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}
type SpeechRecognitionCtor = new () => SpeechRecognitionLike;
interface SpeechRecognitionWindow extends Window {
  SpeechRecognition?: SpeechRecognitionCtor;
  webkitSpeechRecognition?: SpeechRecognitionCtor;
}

function recognitionCtor(): SpeechRecognitionCtor | undefined {
  if (typeof window === 'undefined') return undefined;
  const w = window as SpeechRecognitionWindow;
  return w.SpeechRecognition ?? w.webkitSpeechRecognition;
}

@Component({
  selector: 'app-voice-input-button',
  standalone: true,
  template: `
    @if (supported) {
      <button type="button" class="inline-flex h-10 items-center gap-2 rounded-md border px-3 text-sm hover:bg-slate-50"
        [attr.aria-label]="listening() ? 'Detener dictado' : 'Dictar consulta por voz'" [attr.aria-pressed]="listening()"
        (click)="toggle()">
        <span role="status">{{ listening() ? 'Escuchando…' : 'Dictar' }}</span>
      </button>
    }
  `,
})
export class VoiceInputButtonComponent implements OnDestroy {
  readonly transcript = output<string>();
  protected readonly supported = !!recognitionCtor();
  protected readonly listening = signal(false);
  private recognition: SpeechRecognitionLike | null = null;

  protected toggle(): void {
    if (this.listening()) { this.recognition?.stop(); return; }
    this.start('es-BO');
  }

  private start(lang: string): void {
    const Recognition = recognitionCtor();
    if (!Recognition) return;
    const recognition = new Recognition();
    this.recognition = recognition;
    recognition.lang = lang;
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onresult = (event) => this.transcript.emit(event.results[0][0].transcript);
    recognition.onerror = (event) => {
      this.listening.set(false);
      if (event.error === 'language-not-supported' && lang === 'es-BO') { recognition.onend = null; this.start('es-ES'); return; }
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') toast.error('Permite el micrófono para dictar la consulta');
      else if (event.error !== 'aborted') toast.error('No se pudo reconocer la voz. Puedes escribir la consulta.');
    };
    recognition.onend = () => this.listening.set(false);
    try { recognition.start(); this.listening.set(true); }
    catch { this.listening.set(false); toast.error('No se pudo iniciar el micrófono. Puedes escribir la consulta.'); }
  }

  ngOnDestroy(): void {
    const r = this.recognition;
    if (!r) return;
    r.onresult = r.onerror = r.onend = null;
    r.stop();
  }
}
