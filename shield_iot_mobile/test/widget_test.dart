import 'package:flutter_test/flutter_test.dart';
import 'package:shield_iot_mobile/main.dart';

void main() {
  testWidgets('App starts', (WidgetTester tester) async {
    await tester.pumpWidget(const ShieldIoTApp());
    expect(find.text('SHIELD-IoT'), findsWidgets);
  });
}
