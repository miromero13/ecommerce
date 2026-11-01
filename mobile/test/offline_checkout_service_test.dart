import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/offline/offline_checkout_service.dart';

void main() {
  test('pending offline card purchase is per user and cleared after use', () async {
    FlutterSecureStorage.setMockInitialValues({});
    final service = OfflineCheckoutService();

    await service.save(userId: 'u1', pickupBranchId: 'b1', points: 200);
    final pending = await service.pending('u1');
    expect(pending?['pickup_branch_id'], 'b1');
    expect(pending?['points'], 200);
    expect(await service.pending('u2'), isNull); // another account never pays it

    await service.clear();
    expect(await service.pending('u1'), isNull);

    await service.cacheBranches([{'id': 'b1', 'name': 'Centro', 'city': 'SCZ', 'is_default': true, 'is_active': true}]);
    expect((await service.cachedBranches()).single['name'], 'Centro');
  });
}
