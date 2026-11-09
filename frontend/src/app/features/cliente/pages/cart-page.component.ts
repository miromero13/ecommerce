import { CommonModule } from '@angular/common';
import { Component, DestroyRef, ElementRef, ViewChild, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Stripe, StripeElements, StripePaymentElement, loadStripe } from '@stripe/stripe-js';

import { toast } from '@spartan-ng/brain/sonner';

import { HlmBadgeImports } from '../../../components/badge/src';
import { HlmButton } from '../../../components/button/src';
import { HlmCardImports } from '../../../components/card/src';
import { HlmInputImports } from '../../../components/input/src';
import { HlmTable } from '../../../components/table/src';
import { HlmTabsImports } from '../../../components/tabs/src';
import { getErrorMessage } from '../../../core/utils/http-error.util';
import { requestWithToast } from '../../../core/utils/request-toast.util';
import { downloadSimplePdf } from '../../../core/utils/simple-pdf.util';
import { BrandingService } from '../../../core/services/branding.service';
import { Cart } from '../../shared/models/cart.model';
import { CatalogBranch } from '../../shared/models/catalog.model';
import { CartApiService } from '../../shared/services/cart-api.service';
import { OfflineCartService } from '../../../core/services/offline-cart.service';
import { LoyaltyApiService } from '../../shared/services/loyalty-api.service';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideCreditCard, lucideMapPin, lucideStar, lucideStore, lucideWallet } from '@ng-icons/lucide';
import { CatalogApiService } from '../../shared/services/catalog-api.service';
import { Order } from '../../shared/models/order.model';
import { CheckoutApiService } from '../../shared/services/checkout-api.service';
import { DeliveryApiService } from '../../shared/services/delivery-api.service';
import { DeliveryAddress, DeliveryQuote } from '../../shared/models/delivery.model';
import { WalletApiService } from '../../shared/services/wallet-api.service';
import { environment } from '../../../../environments/environment';

type StripeCheckout = {
  orderId: string;
  pickupExpiresAt: string;
};

import { LocationPickerMapComponent } from '../../shared/components/location-picker-map.component';

@Component({
  selector: 'app-cart-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    NgIcon,
    HlmButton,
    HlmTable,
    LocationPickerMapComponent,
    ...HlmTabsImports,
    ...HlmBadgeImports,
    ...HlmCardImports,
    ...HlmInputImports,
  ],
  providers: [provideIcons({ lucideStore, lucideMapPin, lucideCreditCard, lucideWallet, lucideStar })],
  templateUrl: './cart-page.component.html',
})
export class CartPageComponent {
  private readonly branding = inject(BrandingService);
  private readonly cartApi = inject(CartApiService);
  /** CU25/CU30: prendas agregadas sin conexión, pendientes de enviarse al carrito. */
  protected readonly offlineCart = inject(OfflineCartService);
  protected readonly online = signal(navigator.onLine);
  private readonly catalogApi = inject(CatalogApiService);
  private readonly checkoutApi = inject(CheckoutApiService);
  private readonly walletApi = inject(WalletApiService);
  private stripe: Stripe | null = null;
  private stripeElements: StripeElements | null = null;
  private stripePaymentElement: StripePaymentElement | null = null;

  @ViewChild('paymentElement')
  private set paymentElementHost(host: ElementRef<HTMLDivElement> | undefined) {
    if (host && this.stripePaymentElement) this.stripePaymentElement.mount(host.nativeElement);
  }

  protected readonly cartBranchId = signal<string>(this.getCartBranchId());
  protected readonly cartBranchName = signal<string>(this.getCartBranchName());

  protected readonly cart = signal<Cart | null>(null);
  protected readonly branches = signal<CatalogBranch[]>([]);
  protected readonly lastOrder = signal<Order | null>(null);
  protected readonly stripeCheckout = signal<StripeCheckout | null>(null);
  protected readonly stripePaymentStatus = signal<string | null>(null);
  protected readonly loading = signal(false);
  protected readonly updatingItemId = signal<string | null>(null);
  // Web orders are always paid online by card (Stripe); QR and cash only exist at the till.
  protected readonly pickupBranchId = signal(this.getCartBranchId());
  protected readonly checkingOut = signal(false);
  protected readonly couponCode = signal('');
  // CU17: points of the cart's company; 100 points = 1 Bs off the products.
  private readonly loyaltyApi = inject(LoyaltyApiService);
  protected readonly availablePoints = signal(0);
  protected readonly pointsToRedeem = signal(0);
  // CU19: store wallet
  protected readonly walletBalance = signal<number | null>(null);
  protected readonly paymentMethod = signal<'stripe' | 'wallet'>('stripe');
  // CU20: in-store pickup or home delivery shipped from the selected branch.
  private readonly deliveryApi = inject(DeliveryApiService);
  protected readonly fulfillment = signal<'pickup' | 'delivery'>('pickup');
  protected readonly deliveryAddress = signal('');
  protected readonly deliveryReference = signal('');
  protected readonly latitude = signal('');
  protected readonly longitude = signal('');
  protected readonly quote = signal<DeliveryQuote | null>(null);
  protected readonly quoting = signal(false);

  // Wizard steps on right aside (web only): resumen | entrega | pago
  protected readonly checkoutStep = signal<'resumen' | 'entrega' | 'pago'>('resumen');

  constructor() {
    // Pickup branches belong to the cart's company, so they load after the cart.
    void this.loadCart().then(() => this.loadBranches());
    window.addEventListener('offline', this.onConnectionChange);
    window.addEventListener('online', this.onConnectionChange);
    inject(DestroyRef).onDestroy(() => {
      window.removeEventListener('offline', this.onConnectionChange);
      window.removeEventListener('online', this.onConnectionChange);
    });
  }

  private readonly onConnectionChange = (): void => {
    this.online.set(navigator.onLine);
    if (navigator.onLine) void this.loadCart();
  };

  /** El pago con tarjeta (Stripe) necesita internet: sin conexión no se inicia ni se confirma. */
  private requireConnection(): boolean {
    if (navigator.onLine) return true;
    toast.warning('Sin conexión: el pago con tarjeta (Stripe) requiere internet. Tu carrito se conserva hasta que vuelva la conexión.');
    return false;
  }

  protected goToStep(step: 'resumen' | 'entrega' | 'pago'): void {
    if (step === 'pago') {
      if (!this.pickupBranchId()) {
        toast.warning(this.fulfillment() === 'delivery' ? 'Selecciona la sucursal de despacho.' : 'Selecciona una sucursal para el retiro.');
        return;
      }
      if (this.fulfillment() === 'delivery' && !this.quote()) {
        toast.warning('Ingresa tu dirección y calcula el costo de envío.');
        return;
      }
    }
    this.checkoutStep.set(step);
  }

  protected get itemCount(): number {
    return this.cart()?.item_count ?? 0;
  }

  protected get subtotal(): string {
    return this.cart()?.subtotal ?? '0.00';
  }

  protected get discount(): string {
    return this.cart()?.discount_amount ?? '0.00';
  }

  protected get total(): string {
    return this.cart()?.total_amount ?? '0.00';
  }

  protected async refresh(): Promise<void> {
    await this.loadCart();
  }

  protected async increase(itemId: string, quantity: number): Promise<void> {
    await this.updateQuantity(itemId, quantity + 1);
  }

  protected async decrease(itemId: string, quantity: number): Promise<void> {
    await this.updateQuantity(itemId, quantity - 1);
  }

  protected async remove(itemId: string): Promise<void> {
    this.updatingItemId.set(itemId);
    try {
      const response = await requestWithToast(
        this.cartApi.removeItem(itemId),
        { loading: 'Eliminando item...', success: 'Item eliminado.', error: 'No se pudo eliminar el item.' },
      );
      this.cart.set(response.data ?? null);
    } catch {
      // toast handled by requestWithToast
    } finally {
      this.updatingItemId.set(null);
    }
  }

  protected async clear(): Promise<void> {
    try {
      const response = await requestWithToast(
        this.cartApi.clearCart(),
        { loading: 'Vaciando carrito...', success: 'Carrito vaciado.', error: 'No se pudo vaciar el carrito.' },
      );
      this.clearCartBranch();
      this.cart.set(response.data ?? null);
    } catch {
      // toast handled by requestWithToast
    }
  }

  // [CU15 - Secuencia: Paso 3] El Cliente ejecuta applyCoupon() en CartPageComponent
  protected async applyCoupon(): Promise<void> {
    const code = this.couponCode().trim();
    if (!code) {
      toast.warning('Ingresa un código promocional.');
      return;
    }
    try {
      const response = await requestWithToast(
        this.cartApi.applyCoupon(code),
        { loading: 'Aplicando cupón...', success: 'Cupón aplicado.', error: 'No se pudo aplicar el cupón.' },
      );
      this.cart.set(response.data ?? null);
    } catch {
      // toast handled by requestWithToast
    }
  }

  // [CU15 - Secuencia: Paso 4] El Cliente ejecuta removeCoupon() en CartPageComponent
  protected async removeCoupon(): Promise<void> {
    try {
      const response = await requestWithToast(
        this.cartApi.removeCoupon(),
        { loading: 'Retirando cupón...', success: 'Cupón retirado.', error: 'No se pudo retirar el cupón.' },
      );
      this.cart.set(response.data ?? null);
    } catch {
      // toast handled by requestWithToast
    }
  }

  // [CU19 - Secuencia: Paso 4] El Cliente ejecuta checkout() en CartPageComponent
  protected async checkout(): Promise<void> {
    if (!this.requireConnection()) return;
    if (!this.cart()?.items?.length) {
      toast.warning('Tu carrito está vacío.');
      return;
    }
    const pickupBranchId = this.pickupBranchId();
    if (!pickupBranchId) {
      toast.warning(this.fulfillment() === 'delivery' ? 'Selecciona la sucursal desde donde se enviará el pedido.' : 'Selecciona una sucursal para el retiro.');
      return;
    }
    const delivery = this.deliveryPayload();
    if (this.fulfillment() === 'delivery' && !delivery) {
      toast.warning('Ingresa la dirección y calcula el costo de envío antes de confirmar.');
      return;
    }

    this.checkingOut.set(true);
    try {
      if (this.paymentMethod() === 'wallet') {
        const res = await requestWithToast(
          this.walletApi.checkout({
            pickup_branch_id: pickupBranchId,
            delivery,
            points_to_redeem: this.pointsToRedeem(),
          }),
          { loading: 'Procesando pago con Billetera Digital...', success: '¡Pedido pagado exitosamente con tu Billetera!', error: 'No se pudo pagar con la billetera.' }
        );
        if (res.data) {
          this.lastOrder.set(res.data);
        }
        await this.loadCart();
        void this.loadWallet();
      } else {
        await this.startStripeCheckout(pickupBranchId, delivery);
        await this.loadCart();
      }
    } catch {
      // requestWithToast already showed the error.
    } finally {
      this.checkingOut.set(false);
    }
  }

  protected lineTotal(item: { line_total: string }): string {
    return item.line_total;
  }

  protected orderLabel(): string {
    return this.lastOrder() ? `Pedido #${this.lastOrder()!.id}` : 'Sin pedido todavía';
  }

  protected async downloadSalesNote(order: Order): Promise<void> {
    downloadSimplePdf({
      brand: await this.branding.pdfBrand(order.tenant_id),
      filename: `nota-venta-${order.id}.pdf`,
      title: 'Nota de venta',
      generatedAt: new Date().toLocaleString('es-BO'),
      filters: [
        ['Pedido', order.id],
        ['Fecha', new Date(order.created_at).toLocaleString('es-BO')],
        ['Pago', ({ pending: 'Pendiente', paid: 'Pagado', failed: 'Fallido' } satisfies Record<Order['payment_status'], string>)[order.payment_status]],
        ['Método', order.payment_method === 'stripe' ? 'Tarjeta' : 'QR'],
        ...(order.pickup_code ? [['Código de retiro', order.pickup_code]] : []),
        ['Subtotal', `${order.subtotal} ${order.currency}`],
        ['Descuento', `${order.discount_amount} ${order.currency}`],
        ['Total', `${order.total_amount} ${order.currency}`],
      ],
      columns: ['Producto', 'Variante', 'Cantidad', 'Precio unitario', 'Total'],
      rows: order.items.map((item) => [
        item.product_name,
        [item.size_name, item.color_name].filter(Boolean).join(' / ') || item.variant_sku,
        String(item.quantity),
        `${item.unit_price} ${order.currency}`,
        `${item.line_total} ${order.currency}`,
      ]),
    });
  }

  protected selectFulfillment(type: 'pickup' | 'delivery'): void {
    this.fulfillment.set(type);
    this.quote.set(null);
  }

  protected onMapLocationSelected(coords: { latitude: number; longitude: number }): void {
    this.latitude.set(coords.latitude.toFixed(6));
    this.longitude.set(coords.longitude.toFixed(6));
    if (this.pickupBranchId()) {
      void this.quoteDelivery();
    }
  }

  protected setCoordinate(target: 'latitude' | 'longitude', event: Event): void {
    this[target].set((event.target as HTMLInputElement).value);
    this.quote.set(null);
  }

  protected useMyLocation(): void {
    if (!navigator.geolocation) {
      toast.error('Tu navegador no permite obtener la ubicación.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        this.latitude.set(position.coords.latitude.toFixed(6));
        this.longitude.set(position.coords.longitude.toFixed(6));
        void this.quoteDelivery();
      },
      () => toast.error('No se pudo obtener tu ubicación. Ingrésala manualmente.'),
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }

  // [CU20 - Secuencia: Paso 1] El Cliente ejecuta quoteDelivery() en CartPageComponent
  protected async quoteDelivery(): Promise<void> {
    const latitude = Number(this.latitude());
    const longitude = Number(this.longitude());
    if (!this.pickupBranchId() || !this.latitude() || !this.longitude() || Number.isNaN(latitude) || Number.isNaN(longitude)) {
      toast.warning('Selecciona la sucursal e indica tu ubicación.');
      return;
    }
    this.quoting.set(true);
    try {
      const response = await firstValueFrom(this.deliveryApi.quote({ branch_id: this.pickupBranchId(), latitude, longitude }));
      this.quote.set(response.data ?? null);
      toast.success(response.message);
    } catch (error) {
      this.quote.set(null);
      toast.error(getErrorMessage(error, 'No se pudo calcular el envío.'));
    } finally {
      this.quoting.set(false);
    }
  }

  protected totalWithShipping(): number {
    return Number(this.total) + (this.fulfillment() === 'delivery' ? this.quote()?.shipping_cost ?? 0 : 0);
  }

  private deliveryPayload(): DeliveryAddress | undefined {
    if (this.fulfillment() !== 'delivery' || !this.quote() || this.deliveryAddress().trim().length < 5) return undefined;
    return {
      address: this.deliveryAddress().trim(),
      reference: this.deliveryReference().trim() || null,
      latitude: Number(this.latitude()),
      longitude: Number(this.longitude()),
    };
  }

  protected branchLabel(branchId: string | null | undefined): string {
    const branch = this.branches().find((item) => item.id === branchId);
    return branch ? `${branch.name} - ${branch.city}` : 'Sin sucursal';
  }

  protected async confirmStripePayment(): Promise<void> {
    if (!this.requireConnection()) return;
    if (!this.stripe || !this.stripeElements) {
      toast.warning('Primero inicia el pago con Stripe.');
      return;
    }

    this.checkingOut.set(true);
    try {
      const { error, paymentIntent } = await this.stripe.confirmPayment({
        elements: this.stripeElements,
        confirmParams: { return_url: window.location.href },
        redirect: 'if_required',
      });
      if (error) {
        this.stripePaymentStatus.set('error');
        toast.error(error.message ?? 'No se pudo confirmar el pago.');
      } else if (paymentIntent?.status === 'succeeded') {
        const orderId = this.stripeCheckout()?.orderId;
        if (!orderId) return;
        const response = await firstValueFrom(this.checkoutApi.getOrder(orderId));
        const order = response.data ?? null;
        this.lastOrder.set(order);
        if (order?.payment_status === 'paid') {
          this.stripePaymentStatus.set('paid');
          toast.success('Pago confirmado. Tu pedido queda pendiente de retiro.');
        } else {
          this.stripePaymentStatus.set('pending');
          toast.info('Pago enviado. Esperando confirmación del servidor.');
        }
      } else if (paymentIntent?.status === 'canceled') {
        this.stripePaymentStatus.set('cancelled');
        toast.warning('El pago fue cancelado.');
      } else {
        this.stripePaymentStatus.set('pending');
        toast.info('El pago está pendiente de confirmación.');
      }
    } catch {
      this.stripePaymentStatus.set('error');
      toast.error('No se pudo confirmar el pago.');
    } finally {
      this.checkingOut.set(false);
    }
  }

  private async loadCart(): Promise<void> {
    this.loading.set(true);
    try {
      await this.offlineCart.syncPending(); // CU30: primero se envían las prendas guardadas sin conexión
      const response = await firstValueFrom(this.cartApi.getCurrentCart());
      this.cart.set(response.data ?? null);
      void this.loadPoints();
    } catch (error) {
      // Sin conexión se conserva el último carrito cargado y se muestran las prendas pendientes.
      if (navigator.onLine) {
        toast.error(getErrorMessage(error, 'No se pudo cargar el carrito.'));
        this.cart.set(null);
      }
    } finally {
      this.loading.set(false);
    }
  }

  protected setPoints(value: string): void {
    this.pointsToRedeem.set(Math.max(0, Math.floor(Number(value) || 0)));
  }

  private async loadPoints(): Promise<void> {
    this.pointsToRedeem.set(0);
    const tenantId = this.cart()?.tenant_id;
    try {
      const balances = tenantId ? (await firstValueFrom(this.loyaltyApi.balances())).data ?? [] : [];
      this.availablePoints.set(balances.find((row) => row.tenant_id === tenantId)?.points_balance ?? 0);
    } catch {
      this.availablePoints.set(0); // checkout still works without points
    }
    void this.loadWallet();
  }

  protected async loadWallet(): Promise<void> {
    try {
      const res = await firstValueFrom(this.walletApi.balance());
      this.walletBalance.set(res.data?.balance ?? 0);
    } catch {
      this.walletBalance.set(0);
    }
  }

  protected async convertPointsToWallet(): Promise<void> {
    const tenantId = this.cart()?.tenant_id;
    const points = Math.floor(this.availablePoints() / 100) * 100;
    if (!tenantId || points < 100) return;
    try {
      const res = await firstValueFrom(this.walletApi.convertPoints({ tenant_id: tenantId, points }));
      toast.success(res.message || 'Puntos convertidos exitosamente a saldo en tu Billetera.');
      await this.loadPoints();
      await this.loadWallet();
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron convertir los puntos a saldo.'));
    }
  }

  private async loadBranches(): Promise<void> {
    try {
      const tenantId = this.cart()?.tenant_id;
      if (!tenantId) {
        this.branches.set([]);
        return;
      }
      const response = await firstValueFrom(this.catalogApi.listPublicBranches(tenantId));
      const branchList = response.data ?? [];
      this.branches.set(branchList);
      const serverBranch = this.cart()?.branch_id;
      const preferred = (serverBranch && branchList.some((b) => b.id === serverBranch))
        ? serverBranch
        : (branchList.some((b) => b.id === this.cartBranchId()) ? this.cartBranchId() : '');
      const chosen = preferred || (branchList.length === 1 ? branchList[0].id : '');
      this.pickupBranchId.set(chosen);
      if (chosen && chosen !== this.cart()?.branch_id) {
        void this.syncCartBranch(chosen, false);
      }
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudieron cargar las sucursales.'));
    }
  }

  protected async onBranchChange(newBranchId: string): Promise<void> {
    this.pickupBranchId.set(newBranchId);
    await this.syncCartBranch(newBranchId, true);
  }

  private async syncCartBranch(branchId: string, notifyUser: boolean): Promise<void> {
    try {
      const response = await firstValueFrom(this.cartApi.setBranch(branchId || null));
      this.cart.set(response.data ?? null);
      if (branchId) {
        const branch = this.branches().find((b) => b.id === branchId);
        if (branch) {
          this.setCartBranch(branch.id, `${branch.name} (${branch.city})`);
        }
      } else {
        this.clearCartBranch();
      }
      if (notifyUser && response.message && response.message.includes('retirado')) {
        toast.warning(response.message);
      }
    } catch (error) {
      toast.error(getErrorMessage(error, 'No se pudo actualizar la sucursal del carrito.'));
    }
  }

  private setCartBranch(branchId: string, branchName: string): void {
    try {
      localStorage.setItem('fashionstore_cart_branch_id', branchId);
      localStorage.setItem('fashionstore_cart_branch_name', branchName);
    } catch {}
    this.cartBranchId.set(branchId);
    this.cartBranchName.set(branchName);
  }

  private getCartBranchId(): string {
    try {
      return localStorage.getItem('fashionstore_cart_branch_id') || '';
    } catch {
      return '';
    }
  }

  private getCartBranchName(): string {
    try {
      return localStorage.getItem('fashionstore_cart_branch_name') || '';
    } catch {
      return '';
    }
  }

  protected clearCartBranch(): void {
    try {
      localStorage.removeItem('fashionstore_cart_branch_id');
      localStorage.removeItem('fashionstore_cart_branch_name');
    } catch {}
    this.cartBranchId.set('');
    this.cartBranchName.set('');
    this.pickupBranchId.set('');
  }

  private async startStripeCheckout(pickupBranchId: string, delivery?: DeliveryAddress): Promise<void> {
    if (!environment.stripePublishableKey) {
      toast.error('Stripe no está configurado para esta aplicación.');
      return;
    }
    try {
      this.stripe = await loadStripe(environment.stripePublishableKey);
    } catch {
      toast.error('No se pudo cargar Stripe.');
      return;
    }
    if (!this.stripe) {
      toast.error('No se pudo cargar Stripe.');
      return;
    }
    const response = await requestWithToast(
      this.checkoutApi.checkoutStripe({ pickup_branch_id: pickupBranchId, delivery, points_to_redeem: this.pointsToRedeem() }),
      { loading: 'Iniciando Stripe...', success: 'Completa los datos de tu tarjeta.', error: 'No se pudo iniciar Stripe.' },
    );
    const checkout = response.data;
    if (!checkout) return;

    this.clearStripeCheckout();
    this.stripeElements = this.stripe.elements({ clientSecret: checkout.client_secret });
    this.stripePaymentElement = this.stripeElements.create('payment');
    this.stripeCheckout.set({ orderId: checkout.order_id, pickupExpiresAt: checkout.pickup_expires_at });
    this.stripePaymentStatus.set('ready');
  }

  private clearStripeCheckout(): void {
    this.stripePaymentElement?.destroy();
    this.stripePaymentElement = null;
    this.stripeElements = null;
    this.stripeCheckout.set(null);
    this.stripePaymentStatus.set(null);
  }

  private async updateQuantity(itemId: string, quantity: number): Promise<void> {
    if (quantity < 0) {
      return;
    }
    this.updatingItemId.set(itemId);
    try {
      const response = await requestWithToast(
        this.cartApi.updateItem(itemId, { quantity }),
        { loading: 'Actualizando carrito...', success: 'Carrito actualizado.', error: 'No se pudo actualizar el carrito.' },
      );
      this.cart.set(response.data ?? null);
    } catch {
      // toast handled by requestWithToast
    } finally {
      this.updatingItemId.set(null);
    }
  }
}
