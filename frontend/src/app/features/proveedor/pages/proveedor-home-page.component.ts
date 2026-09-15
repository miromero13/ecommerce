import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmCardImports } from '../../../components/card/src';

@Component({
  selector: 'app-proveedor-home-page',
  standalone: true,
  imports: [CommonModule, RouterLink, ...HlmBadgeImports, ...HlmCardImports],
  templateUrl: './proveedor-home-page.component.html',
})
export class ProveedorHomePageComponent {}
