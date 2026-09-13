import 'package:flutter/foundation.dart';

import '../../core/network/api_client.dart';
import '../../core/network/api_exception.dart';
import '../auth/auth_controller.dart';
import '../catalog/catalog_api.dart';
import '../catalog/catalog_models.dart';
import 'reservation_api.dart';
import 'reservation_models.dart';

enum ReservationControllerStatus { idle, loading, saving, ready, error }

class ReservationController extends ChangeNotifier {
  ReservationController({
    ReservationApi? api,
    CatalogApi? catalogApi,
    AuthController? authController,
  }) : _api =
           api ??
           ReservationApi(
             client: ApiClient(
               tokenProvider: () => authController?.accessToken,
               onUnauthorized: authController?.handleUnauthorized,
             ),
           ),
       _catalogApi = catalogApi ?? CatalogApi();

  final ReservationApi _api;
  final CatalogApi _catalogApi;

  ReservationControllerStatus status = ReservationControllerStatus.idle;
  List<Reservation> reservations = const [];
  List<Branch> branches = const [];
  Reservation? selectedReservation;
  String? errorMessage;
  String? feedbackMessage;

  Future<void> load() async {
    status = ReservationControllerStatus.loading;
    errorMessage = null;
    feedbackMessage = null;
    notifyListeners();

    try {
      final results = await Future.wait([
        _api.getMine(),
        _catalogApi.getBranches(),
      ]);
      final reservationResult = results[0] as ReservationListResult;
      reservations = reservationResult.reservations;
      branches = results[1] as List<Branch>;
      feedbackMessage = reservationResult.message;
      status = ReservationControllerStatus.ready;
    } catch (error) {
      status = ReservationControllerStatus.error;
      errorMessage = _messageFor(error);
    }
    notifyListeners();
  }

  Future<void> create({
    required String branchId,
    required DateTime visitDate,
    required List<ReservationDraftItem> items,
  }) {
    return _runSave(
      () => _api.create(branchId: branchId, visitDate: visitDate, items: items),
      onSuccess: (reservation) {
        reservations = [reservation, ...reservations];
      },
    );
  }

  Future<void> cancel(String reservationId) {
    return _runSave(
      () => _api.cancel(reservationId: reservationId),
      onSuccess: (reservation) {
        reservations = [
          for (final item in reservations)
            item.id == reservation.id ? reservation : item,
        ];
      },
    );
  }

  Future<void> loadDetail(String reservationId) async {
    status = ReservationControllerStatus.loading;
    errorMessage = null;
    notifyListeners();
    try {
      final result = await _api.getById(reservationId: reservationId);
      selectedReservation = result.reservation;
      feedbackMessage = result.message;
      status = ReservationControllerStatus.ready;
    } catch (error) {
      status = ReservationControllerStatus.error;
      errorMessage = _messageFor(error);
    }
    notifyListeners();
  }

  Future<void> _runSave(
    Future<ReservationResult> Function() operation, {
    required void Function(Reservation reservation) onSuccess,
  }) async {
    status = ReservationControllerStatus.saving;
    errorMessage = null;
    feedbackMessage = null;
    notifyListeners();
    try {
      final result = await operation();
      onSuccess(result.reservation);
      feedbackMessage = result.message;
      status = ReservationControllerStatus.ready;
    } catch (error) {
      status = ReservationControllerStatus.error;
      errorMessage = _messageFor(error);
    }
    notifyListeners();
  }

  static String _messageFor(Object error) {
    if (error is ApiException) return error.message;
    return 'No se pudo sincronizar las reservas.';
  }
}
