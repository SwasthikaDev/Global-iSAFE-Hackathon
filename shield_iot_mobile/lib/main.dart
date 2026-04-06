import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'services/app_state.dart';
import 'theme/app_theme.dart';
import 'screens/dashboard_screen.dart';
import 'screens/devices_screen.dart';
import 'screens/alerts_screen.dart';
import 'screens/connections_screen.dart';
import 'screens/investigate_screen.dart';
import 'screens/settings_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
    ),
  );
  runApp(
    ChangeNotifierProvider(
      create: (_) => AppState(),
      child: const ShieldIoTApp(),
    ),
  );
}

class ShieldIoTApp extends StatelessWidget {
  const ShieldIoTApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SHIELD-IoT',
      theme: AppTheme.light,
      debugShowCheckedModeBanner: false,
      home: const _MainShell(),
    );
  }
}

class _MainShell extends StatefulWidget {
  const _MainShell();

  @override
  State<_MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<_MainShell> {
  int _index = 0;

  static const _screens = <Widget>[
    DashboardScreen(),
    DevicesScreen(),
    AlertsScreen(),
    ConnectionsScreen(),
    InvestigateScreen(),
    SettingsScreen(),
  ];

  static const _destinations = <NavigationDestination>[
    NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard_rounded), label: 'Dashboard'),
    NavigationDestination(icon: Icon(Icons.devices_outlined), selectedIcon: Icon(Icons.devices_rounded), label: 'Devices'),
    NavigationDestination(icon: Icon(Icons.notifications_outlined), selectedIcon: Icon(Icons.notifications_rounded), label: 'Alerts'),
    NavigationDestination(icon: Icon(Icons.cable_outlined), selectedIcon: Icon(Icons.cable_rounded), label: 'Traffic'),
    NavigationDestination(icon: Icon(Icons.manage_search_outlined), selectedIcon: Icon(Icons.manage_search_rounded), label: 'Investigate'),
    NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings_rounded), label: 'Settings'),
  ];

  @override
  Widget build(BuildContext context) {
    final state   = context.watch<AppState>();
    final alerts  = state.alerts.where((a) => a.status == 'active').length;

    return Scaffold(
      appBar: AppBar(
        title: Row(children: [
          const Icon(Icons.shield_rounded, color: AppTheme.sky600, size: 22),
          const SizedBox(width: 8),
          const Text('SHIELD-IoT'),
          const Spacer(),
          if (state.isLoading)
            const SizedBox(
              width: 16, height: 16,
              child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.sky600),
            ),
          if (!state.isConnected && !state.isLoading)
            const Icon(Icons.wifi_off_rounded, color: AppTheme.rose500, size: 18),
        ]),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(color: AppTheme.slate200, height: 1),
        ),
      ),
      body: IndexedStack(index: _index, children: _screens),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: AppTheme.slate200, width: 1)),
        ),
        child: NavigationBar(
          selectedIndex: _index,
          onDestinationSelected: (i) => setState(() => _index = i),
          destinations: [
            ..._destinations.take(2),
            NavigationDestination(
              icon: Badge(
                isLabelVisible: alerts > 0,
                label: Text('$alerts'),
                child: const Icon(Icons.notifications_outlined),
              ),
              selectedIcon: Badge(
                isLabelVisible: alerts > 0,
                label: Text('$alerts'),
                child: const Icon(Icons.notifications_rounded),
              ),
              label: 'Alerts',
            ),
            ..._destinations.skip(3),
          ],
        ),
      ),
    );
  }
}
