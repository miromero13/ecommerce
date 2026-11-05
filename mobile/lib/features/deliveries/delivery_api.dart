import '../../core/network/api_client.dart';
import 'delivery_models.dart';

class DeliveryApi {
  DeliveryApi({
    ApiClient? client,
    String? Function()? tokenProvider,
    void Function()? onUnauthorized,
  }) : _client = client ??
            ApiClient(
              tokenProvider: tokenProvider,
              onUnauthorized: onUnauthorized,
            );

  final ApiClient _client;

  Future<List<DeliveryOrder>> getMyDeliveries() async {
    final response = await _client.get<List<dynamic>>(
      'delivery/my-orders',
      parser: (value) => value as List<dynamic>,
    );
    final data = response.data ?? const [];
    return data
        .whereType<Map<String, dynamic>>()
        .map(DeliveryOrder.fromJson)
        .toList(growable: false);
  }
}
