import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmCardImports } from '../../../components/card/src';

@Component({
  selector: 'app-cajero-home-page',
  standalone: true,
  imports: [CommonModule, ...HlmBadgeImports, ...HlmCardImports],
  templateUrl: './cajero-home-page.component.html',
})
export class CajeroHomePageComponent {}
