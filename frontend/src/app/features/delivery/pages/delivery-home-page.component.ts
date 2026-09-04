import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmCardImports } from '../../../components/card/src';

@Component({
  selector: 'app-delivery-home-page',
  standalone: true,
  imports: [CommonModule, ...HlmBadgeImports, ...HlmCardImports],
  templateUrl: './delivery-home-page.component.html',
})
export class DeliveryHomePageComponent {}
