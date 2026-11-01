import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/network/api_exception.dart';
import 'package:mobile/core/offline/offline_cart_service.dart';
import 'package:mobile/features/cart/cart_api.dart';
import 'package:mobile/features/cart/cart_models.dart';

void main() {
  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
    OfflineCartService.resetLockNotice();
    OfflineCartService.now = DateTime.now;
  });

  Future<OfflineCartService> withTwoPending() async {
    final service = OfflineCartService();
    final offline = _Api(const ApiException(message: 'sin red'));
    await service.addItem(offline, variantId: 'v1', quantity: 1);
    await service.addItem(offline, variantId: 'v2', quantity: 2);
    expect((await service.pending()).length, 2);
    return service;
  }

  test('carrito bloqueado: conserva todas las prendas y devuelve un solo aviso', () async {
    final service = await withTwoPending();
    final api = _Api(const ApiException(
      statusCode: 400,
      message: 'Tienes un pedido pendiente de pago. Págalo o cancélalo para modificar el carrito.',
    ));

    final rejected = await service.syncPending(api);

    expect(rejected, [OfflineCartService.lockedSyncMessage]);
    expect(api.calls, 1); // stops at the first rejection
    expect((await service.pending()).length, 2);
  });

  test('carrito bloqueado: el segundo sync no llama a la red hasta resetear el aviso', () async {
    final service = await withTwoPending();
    final api = _Api(const ApiException(
      statusCode: 400,
      message: 'Tienes un pedido pendiente de pago. Págalo o cancélalo para modificar el carrito.',
    ));

    expect(await service.syncPending(api), [OfflineCartService.lockedSyncMessage]);
    expect(api.calls, 1);
    expect(await service.syncPending(api), isEmpty);
    expect(api.calls, 1);

    OfflineCartService.resetLockNotice();
    expect(await service.syncPending(api), [OfflineCartService.lockedSyncMessage]);
    expect(api.calls, 2);
  });

  test('tras 5 minutos reintenta una vez; el aviso se muestra solo la primera vez', () async {
    var clock = DateTime.utc(2026, 1, 1, 10);
    OfflineCartService.now = () => clock;
    final service = await withTwoPending();
    final api = _Api(const ApiException(statusCode: 400, message: 'Tienes un pedido pendiente de pago.'));

    expect(await service.syncPending(api), [OfflineCartService.lockedSyncMessage]);
    expect(api.calls, 1);

    clock = clock.add(const Duration(minutes: 4));
    expect(await service.syncPending(api), isEmpty);
    expect(api.calls, 1); // within the window: no network

    clock = clock.add(const Duration(minutes: 2)); // 6 min after the lock
    expect(await service.syncPending(api), isEmpty); // still locked: no repeated message
    expect(api.calls, 2);
    expect(await service.syncPending(api), isEmpty);
    expect(api.calls, 2); // window restarted

    clock = clock.add(const Duration(minutes: 6));
    final ok = _Api(null);
    expect(await service.syncPending(ok), isEmpty); // lock gone: garments synced
    expect(ok.calls, 2);
    expect(await service.pending(), isEmpty);

    // flag reset: a new lock notifies again
    await service.addItem(_Api(const ApiException(message: 'sin red')), variantId: 'v3', quantity: 1);
    expect(await service.syncPending(api), [OfflineCartService.lockedSyncMessage]);
  });

  test('otro rechazo del servidor descarta la prenda y sigue', () async {
    final service = await withTwoPending();
    final api = _Api(const ApiException(statusCode: 400, message: 'Sin stock'));

    final rejected = await service.syncPending(api);

    expect(rejected, ['Sin stock', 'Sin stock']);
    expect(await service.pending(), isEmpty);
  });
}

class _Api extends CartApi {
  _Api(this.failure) : super();

  final ApiException? failure;
  var calls = 0;

  @override
  Future<CartOperationResult> addItem({
    required String variantId,
    required int quantity,
    String? offlineRequestedAt,
  }) async {
    calls++;
    if (failure != null) throw failure!;
    return CartOperationResult(cart: _emptyCart, message: 'ok');
  }
}

final _emptyCart = Cart(
  id: 'c',
  userId: 'u',
  status: CartStatus.active,
  subtotal: 0,
  discountAmount: 0,
  totalAmount: 0,
  itemCount: 0,
  createdAt: DateTime.utc(2026),
  items: const [],
);
