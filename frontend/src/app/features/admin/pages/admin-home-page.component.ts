import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

import { HlmCardImports } from '../../../components/card/src';

@Component({
  selector: 'app-admin-home-page',
  standalone: true,
  imports: [CommonModule, ...HlmCardImports],
  templateUrl: './admin-home-page.component.html',
})
export class AdminHomePageComponent {}
