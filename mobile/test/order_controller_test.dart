import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/features/orders/order_api.dart';
import 'package:mobile/features/orders/order_controller.dart';
import 'package:mobile/features/orders/order_models.dart';

void main() {
  test('carga detalle y agrega el checkout al listado', () async {
    final controller = OrderController(api: _FakeOrderApi());

    await controller.load();
    expect(controller.status, OrderControllerStatus.ready);
    expect(controller.orders, hasLength(1));

    await controller.checkoutCash(pickupBranchId: 'branch-id');
    expect(controller.orders, hasLength(2));
    expect(controller.selectedOrder?.id, 'created-order');

    await controller.loadDetail('order-id');
    expect(controller.selectedOrder?.id, 'order-id');
  });

  test('inicia el pago de un pedido existente', () async {
    final controller = OrderController(api: _FakeOrderApi());

    final result = await controller.payOrder(orderId: 'order-id');

    expect(result?.checkout.orderId, 'order-id');
    expect(controller.status, OrderControllerStatus.ready);
  });
}

class _FakeOrderApi extends OrderApi {
  _FakeOrderApi() : super();

  @override
  Future<OrderListResult> getMine() async {
    return OrderListResult(
      orders: [_order('order-id')],
      message: 'Pedidos obtenidos exitosamente',
    );
  }

  @override
  Future<List<PickupBranch>> getPublicBranches() async {
    return const [
      PickupBranch(
        id: 'branch-id',
        name: 'Sucursal Central',
        city: 'La Paz',
        isDefault: true,
        isActive: true,
      ),
    ];
  }

  @override
  Future<OrderResult> checkoutCash({required String pickupBranchId}) async {
    return OrderResult(
      order: _order('created-order'),
      message: 'Pago en efectivo procesado exitosamente',
    );
  }

  @override
  Future<OrderResult> getById({required String orderId}) async {
    return OrderResult(
      order: _order(orderId),
      message: 'Pedido obtenido exitosamente',
    );
  }

  @override
  Future<StripeCheckoutResult> payOrder({required String orderId}) async {
    return StripeCheckoutResult(
      checkout: StripeCheckout(
        orderId: orderId,
        clientSecret: 'secret',
        paymentIntentId: 'intent-id',
      ),
      message: 'Pago con Stripe iniciado exitosamente',
    );
  }
}

Order _order(String id) {
  return Order(
    id: id,
    userId: 'user-id',
    status: OrderStatus.paid,
    paymentMethod: PaymentMethod.cash,
    paymentStatus: PaymentStatus.paid,
    subtotal: 100,
    discountAmount: 0,
    totalAmount: 100,
    currency: 'usd',
    createdAt: DateTime.utc(2026, 9, 1),
    items: const [],
  );
}
