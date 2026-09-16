import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { DonutChartComponent } from 'angular-chrts';
import type { BulletLegendItemInterface } from '@unovis/ts';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmCardImports } from '../../../components/card/src';
import { OnBrowserDirective } from '@spartan-ng/helm/utils';
import { ReservationApiService } from '../../shared/services/reservation-api.service';
import { CheckoutApiService } from '../../shared/services/checkout-api.service';
import { CartApiService } from '../../shared/services/cart-api.service';
import { Reservation } from '../../shared/models/reservation.model';
import { Order } from '../../shared/models/order.model';
import { Cart } from '../../shared/models/cart.model';

@Component({
  selector: 'app-cliente-home-page',
  standalone: true,
  imports: [CommonModule, RouterLink, DonutChartComponent, OnBrowserDirective, ...HlmBadgeImports, ...HlmCardImports],
  templateUrl: './cliente-home-page.component.html',
})
export class ClienteHomePageComponent {
  private readonly reservationsApi = inject(ReservationApiService);
  private readonly checkoutApi = inject(CheckoutApiService);
  private readonly cartApi = inject(CartApiService);
  protected readonly reservations = signal<Reservation[]>([]);
  protected readonly orders = signal<Order[]>([]);
  protected readonly cart = signal<Cart | null>(null);
  private readonly statusInfo: Record<Reservation['status'], { name: string; color: string }> = {
    pending: { name: 'Pendientes', color: '#f59e0b' }, confirmed: { name: 'Confirmadas', color: '#0ea5e9' },
    attended: { name: 'Atendidas', color: '#10b981' }, purchase_pending: { name: 'Compra pendiente', color: '#8b5cf6' },
    sold: { name: 'Vendidas', color: '#14b8a6' }, not_sold: { name: 'No compradas', color: '#64748b' },
    cancelled: { name: 'Canceladas', color: '#f43f5e' }, expired: { name: 'Vencidas', color: '#94a3b8' },
  };
  protected readonly reservationDistribution = computed(() => Object.entries(this.statusInfo)
    .map(([key, info]) => ({ key, info, value: this.reservations().filter((reservation) => reservation.status === key).length }))
    .filter((item) => item.value > 0));
  protected readonly reservationChartData = computed(() => this.reservationDistribution().map((item) => item.value));
  protected readonly reservationCategories = computed<Record<string, BulletLegendItemInterface>>(() =>
    Object.fromEntries(this.reservationDistribution().map(({ key, info }) => [key, { name: info.name, color: info.color }])));
  constructor() { void this.load(); }
  private async load(): Promise<void> {
    try { const [reservations, orders, cart] = await Promise.all([firstValueFrom(this.reservationsApi.listMyReservations()), firstValueFrom(this.checkoutApi.listOrders()), firstValueFrom(this.cartApi.getCurrentCart())]); this.reservations.set(reservations.data ?? []); this.orders.set(orders.data ?? []); this.cart.set(cart.data ?? null); } catch { /* keep the dashboard empty */ }
  }
}
