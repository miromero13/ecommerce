import '../../core/network/api_client.dart';
import 'reservation_models.dart';
import '../cart/cart_models.dart';

class ReservationApi {
  ReservationApi({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  Future<ReservationListResult> getMine() async {
    final response = await _client.get<List<Reservation>>(
      'reservations/me',
      parser: (value) => _parseList(value, Reservation.fromJson),
    );
    return ReservationListResult(
      reservations: response.data ?? const [],
      message: response.message,
    );
  }

  Future<ReservationResult> getById({required String reservationId}) async {
    final response = await _client.get<Reservation>(
      'reservations/$reservationId',
      parser: _parseReservation,
    );
    return _result(response.data, response.message);
  }

  Future<ReservationResult> create({
    required String branchId,
    required DateTime visitDate,
    required List<ReservationDraftItem> items,
  }) async {
    final response = await _client.post<Reservation>(
      'reservations/',
      data: {
        'branch_id': branchId,
        'visit_date': formatReservationDate(visitDate),
        'items': [for (final item in items) item.toJson()],
      },
      parser: _parseReservation,
    );
    return _result(response.data, response.message);
  }

  Future<ReservationResult> cancel({required String reservationId}) async {
    final response = await _client.patch<Reservation>(
      'reservations/$reservationId/cancel',
      parser: _parseReservation,
    );
    return _result(response.data, response.message);
  }

  Future<ReservationResult> decide({
    required String reservationId,
    required bool purchase,
  }) async {
    final response = await _client.patch<Reservation>(
      'reservations/$reservationId/decision',
      data: {'purchase': purchase},
      parser: _parseReservation,
    );
    return _result(response.data, response.message);
  }

  Future<CartOperationResult> transferToCart({required String reservationId}) async {
    final response = await _client.post<Cart>(
      'reservations/$reservationId/to-cart',
      parser: (value) => Cart.fromJson(Map<String, dynamic>.from(value as Map)),
    );
    final cart = response.data;
    if (cart == null) throw const FormatException('La respuesta no contiene un carrito');
    return CartOperationResult(cart: cart, message: response.message);
  }

  static Reservation _parseReservation(dynamic value) {
    if (value is! Map) {
      throw const FormatException('La respuesta de la reserva es inválida');
    }
    return Reservation.fromJson(Map<String, dynamic>.from(value));
  }

  static List<T> _parseList<T>(
    dynamic value,
    T Function(Map<String, dynamic>) parser,
  ) {
    if (value is! List) {
      throw const FormatException('La respuesta de reservas no es una lista');
    }
    return value
        .map((item) {
          if (item is! Map) {
            throw const FormatException('Una reserva es inválida');
          }
          return parser(Map<String, dynamic>.from(item));
        })
        .toList(growable: false);
  }

  static ReservationResult _result(Reservation? reservation, String message) {
    if (reservation == null) {
      throw const FormatException('La respuesta no contiene una reserva');
    }
    return ReservationResult(reservation: reservation, message: message);
  }
}

class ReservationListResult {
  const ReservationListResult({
    required this.reservations,
    required this.message,
  });

  final List<Reservation> reservations;
  final String message;
}

class ReservationResult {
  const ReservationResult({required this.reservation, required this.message});

  final Reservation reservation;
  final String message;
}
