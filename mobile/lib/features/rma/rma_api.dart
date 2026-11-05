import '../../core/network/api_client.dart';
import '../../core/network/api_response.dart';
import 'rma_models.dart';

class RmaApi {
  RmaApi({
    ApiClient? client,
    String? Function()? tokenProvider,
    void Function()? onUnauthorized,
  }) : _client = client ??
            ApiClient(
              tokenProvider: tokenProvider,
              onUnauthorized: onUnauthorized,
            );

  final ApiClient _client;

  Future<List<EligibleOrder>> getEligibleOrders() async {
    final response = await _client.get<List<dynamic>>(
      'rma/eligible-orders',
      parser: (value) => value as List<dynamic>,
    );
    final data = response.data ?? const [];
    return data
        .whereType<Map<String, dynamic>>()
        .map(EligibleOrder.fromJson)
        .toList(growable: false);
  }

  Future<List<RmaRequest>> getMyRmaRequests() async {
    final response = await _client.get<List<dynamic>>(
      'rma/requests',
      parser: (value) => value as List<dynamic>,
    );
    final data = response.data ?? const [];
    return data
        .whereType<Map<String, dynamic>>()
        .map(RmaRequest.fromJson)
        .toList(growable: false);
  }

  Future<ApiResponse<RmaRequest>> createRmaRequest({
    required String orderId,
    required List<Map<String, dynamic>> items,
    String? customerNotes,
  }) {
    return _client.post<RmaRequest>(
      'rma/requests',
      data: {
        'order_id': orderId,
        'items': items,
        if (customerNotes != null && customerNotes.isNotEmpty)
          'customer_notes': customerNotes,
      },
      parser: (value) => RmaRequest.fromJson(Map<String, dynamic>.from(value as Map)),
    );
  }
}
