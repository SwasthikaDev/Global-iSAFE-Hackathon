import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/app_state.dart';
import '../theme/app_theme.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _urlCtrl;

  @override
  void initState() {
    super.initState();
    _urlCtrl = TextEditingController(text: context.read<AppState>().serverUrl);
  }

  @override
  void dispose() { _urlCtrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Connection card
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                const Icon(Icons.settings_ethernet_rounded, size: 16, color: AppTheme.slate500),
                const SizedBox(width: 6),
                Text('Server Connection', style: Theme.of(context).textTheme.titleSmall),
                const Spacer(),
                Container(
                  width: 8, height: 8,
                  decoration: BoxDecoration(
                    color: state.isConnected ? AppTheme.emerald500 : AppTheme.rose500,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 4),
                Text(
                  state.isConnected ? 'Connected' : 'Disconnected',
                  style: TextStyle(
                    fontSize: 11,
                    color: state.isConnected ? AppTheme.emerald700 : AppTheme.rose700,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ]),
              const SizedBox(height: 14),
              TextField(
                controller: _urlCtrl,
                keyboardType: TextInputType.url,
                decoration: InputDecoration(
                  labelText: 'Backend URL',
                  hintText: 'http://192.168.1.x:8000',
                  helperText: 'IP address of the machine running SHIELD-IoT backend',
                  filled: true,
                  fillColor: AppTheme.slate50,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: AppTheme.slate200)),
                  enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: AppTheme.slate200)),
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () async {
                    await context.read<AppState>().setServerUrl(_urlCtrl.text.trim());
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Connecting to server…'), duration: Duration(seconds: 2)),
                      );
                    }
                  },
                  icon: const Icon(Icons.link_rounded, size: 18),
                  label: const Text('Connect'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.sky600,
                    foregroundColor: Colors.white,
                    elevation: 0,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                ),
              ),
            ]),
          ),
        ),
        const SizedBox(height: 12),

        // Info card
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                const Icon(Icons.info_outline_rounded, size: 16, color: AppTheme.slate500),
                const SizedBox(width: 6),
                Text('About', style: Theme.of(context).textTheme.titleSmall),
              ]),
              const SizedBox(height: 12),
              const _InfoRow('App', 'SHIELD-IoT Mobile'),
              const _InfoRow('Version', '1.0.0'),
              _InfoRow('Backend', state.serverUrl),
              _InfoRow('Mode', state.networkStatus?.mode ?? '—'),
              _InfoRow('Cycles', '${state.networkStatus?.cycleCount ?? 0}'),
              if (state.lastRefresh != null)
                _InfoRow('Last refresh', _formatTime(state.lastRefresh!)),
            ]),
          ),
        ),
        const SizedBox(height: 12),

        // Feature list
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                const Icon(Icons.shield_rounded, size: 16, color: AppTheme.sky600),
                const SizedBox(width: 6),
                Text('Features', style: Theme.of(context).textTheme.titleSmall),
              ]),
              const SizedBox(height: 10),
              for (final f in [
                'Real-time network monitoring via psutil',
                'ARP-based LAN device discovery',
                'IP geolocation with country flags',
                'AbuseIPDB threat intelligence',
                'Async port scanning for LAN devices',
                'Isolation Forest anomaly detection',
                'Live TCP connection tracking',
                'Security posture scoring (0–100)',
                'WebSocket push updates',
                'IP investigation tool',
              ])
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 3),
                  child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    const Icon(Icons.check_circle_outline_rounded, size: 14, color: AppTheme.emerald500),
                    const SizedBox(width: 8),
                    Expanded(child: Text(f, style: const TextStyle(fontSize: 12, color: AppTheme.slate700))),
                  ]),
                ),
            ]),
          ),
        ),
      ],
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;
  const _InfoRow(this.label, this.value);

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 4),
    child: Row(children: [
      SizedBox(width: 100, child: Text(label, style: const TextStyle(fontSize: 12, color: AppTheme.slate500))),
      Expanded(child: Text(value, style: const TextStyle(fontSize: 12, color: AppTheme.slate700, fontWeight: FontWeight.w500))),
    ]),
  );
}

String _formatTime(DateTime dt) {
  return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}:${dt.second.toString().padLeft(2, '0')}';
}
