import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmCardImports } from '../../../components/card/src';

@Component({
  selector: 'app-cliente-home-page',
  standalone: true,
  imports: [CommonModule, ...HlmBadgeImports, ...HlmCardImports],
  templateUrl: './cliente-home-page.component.html',
})
export class ClienteHomePageComponent {}
