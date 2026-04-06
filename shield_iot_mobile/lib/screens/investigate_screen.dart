import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/app_state.dart';
import '../models/models.dart';
import '../theme/app_theme.dart';
import '../widgets/status_badge.dart';

class InvestigateScreen extends StatefulWidget {
  const InvestigateScreen({super.key});

  @override
  State<InvestigateScreen> createState() => _InvestigateScreenState();
}

class _InvestigateScreenState extends State<InvestigateScreen> {
  final _ctrl   = TextEditingController();
  bool _loading = false;
  IPInvestigation? _result;
  String? _error;

  static const _quickPick = ['192.168.1.1', '8.8.8.8', '1.1.1.1'];

  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  Future<void> _investigate() async {
    final ip = _ctrl.text.trim();
    if (ip.isEmpty) return;
    FocusScope.of(context).unfocus();
    setState(() { _loading = true; _result = null; _error = null; });
    try {
      final r = await context.read<AppState>().investigateIP(ip);
      setState(() { _result = r; });
    } catch (e) {
      setState(() { _error = e.toString().replaceFirst('Exception: ', ''); });
    } finally {
      setState(() { _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => FocusScope.of(context).unfocus(),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Search row
          Row(children: [
            Expanded(
              child: TextField(
                controller: _ctrl,
                keyboardType: TextInputType.number,
                onSubmitted: (_) => _investigate(),
                decoration: InputDecoration(
                  hintText: 'Enter IP address…',
                  prefixIcon: const Icon(Icons.search_rounded, size: 20),
                  isDense: true,
                  filled: true,
                  fillColor: Colors.white,
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: AppTheme.slate200)),
                  enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: AppTheme.slate200)),
                  focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: AppTheme.sky600, width: 2)),
                ),
              ),
            ),
            const SizedBox(width: 8),
            ElevatedButton(
              onPressed: _loading ? null : _investigate,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.sky600,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                elevation: 0,
              ),
              child: _loading
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.search_rounded, size: 20),
            ),
          ]),

          // Quick-pick chips
          const SizedBox(height: 10),
          Wrap(
            spacing: 6,
            children: _quickPick.map((ip) => ActionChip(
              label: Text(ip, style: const TextStyle(fontFamily: 'monospace', fontSize: 12)),
              onPressed: () { _ctrl.text = ip; _investigate(); },
              backgroundColor: AppTheme.slate50,
              side: const BorderSide(color: AppTheme.slate200),
              padding: const EdgeInsets.symmetric(horizontal: 4),
            )).toList(),
          ),

          // Error
          if (_error != null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: AppTheme.rose50, borderRadius: BorderRadius.circular(8), border: Border.all(color: AppTheme.rose500.withAlpha(80))),
              child: Row(children: [
                const Icon(Icons.error_outline_rounded, color: AppTheme.rose500, size: 18),
                const SizedBox(width: 8),
                Expanded(child: Text(_error!, style: const TextStyle(fontSize: 12, color: AppTheme.rose700))),
              ]),
            ),
          ],

          // Results
          if (_result != null) ...[
            const SizedBox(height: 16),
            _ResultsView(result: _result!),
          ],

          // Empty state
          if (_result == null && !_loading && _error == null) ...[
            const SizedBox(height: 40),
            Center(
              child: Column(children: [
                const Icon(Icons.manage_search_rounded, size: 52, color: Color(0xFFCBD5E1)),
                const SizedBox(height: 12),
                Text('Enter any IP to investigate', style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 6),
                const Text('Works for LAN and public IPs', style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8))),
              ]),
            ),
          ],
        ],
      ),
    );
  }
}

class _ResultsView extends StatelessWidget {
  final IPInvestigation r;
  const _ResultsView({required IPInvestigation result}) : r = result;

  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      // Summary banner
      _SummaryBanner(r: r),
      const SizedBox(height: 12),

      // Details card
      Card(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              const Icon(Icons.public_rounded, size: 14, color: AppTheme.slate500),
              const SizedBox(width: 6),
              Text(r.isPrivate ? 'Local Network' : 'Geolocation', style: Theme.of(context).textTheme.titleSmall),
            ]),
            const SizedBox(height: 10),
            if (!r.isPrivate) ...[
              _Row('Country', '${r.flag} ${r.countryName}'),
              if (r.city.isNotEmpty) _Row('City', r.city),
              if (r.isp.isNotEmpty)  _Row('ISP', r.isp),
              if (r.isHighRiskCountry)
                const _WarningRow('High-risk country'),
            ] else
              const _Row('Type', 'Private / LAN IP'),
            if (r.hostname != r.ip) _Row('Hostname', r.hostname, mono: true),
          ]),
        ),
      ),
      const SizedBox(height: 10),

      // Threat card
      Card(
        color: r.isMalicious ? AppTheme.rose50 : Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: BorderSide(color: r.isMalicious ? AppTheme.rose500.withAlpha(80) : AppTheme.slate200),
        ),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Icon(
                r.isMalicious ? Icons.gpp_bad_rounded : Icons.verified_user_rounded,
                size: 14,
                color: r.isMalicious ? AppTheme.rose500 : AppTheme.emerald500,
              ),
              const SizedBox(width: 6),
              Text('Threat Intelligence', style: Theme.of(context).textTheme.titleSmall),
            ]),
            const SizedBox(height: 10),
            if (r.isMalicious)
              const _WarningRow('MALICIOUS IP DETECTED', color: AppTheme.rose700)
            else
              const Row(children: [
                Icon(Icons.check_circle_rounded, size: 14, color: AppTheme.emerald500),
                SizedBox(width: 6),
                Text('No known threats', style: TextStyle(fontSize: 12, color: AppTheme.emerald700, fontWeight: FontWeight.w600)),
              ]),
            _Row('Source', r.threatSource),
          ]),
        ),
      ),
      const SizedBox(height: 10),

      // Open ports
      if (r.openPorts.isNotEmpty) ...[
        Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                const Icon(Icons.lock_open_rounded, size: 14, color: AppTheme.slate500),
                const SizedBox(width: 6),
                Text('Open Ports (${r.openPorts.length})', style: Theme.of(context).textTheme.titleSmall),
                if (r.openPorts.any((p) => p.risk == 'critical' || p.risk == 'high')) ...[
                  const Spacer(),
                  Text('${r.openPorts.where((p) => p.risk == 'critical' || p.risk == 'high').length} dangerous', style: const TextStyle(fontSize: 11, color: AppTheme.rose700, fontWeight: FontWeight.w600)),
                ],
              ]),
              const SizedBox(height: 10),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: r.openPorts.map((p) {
                  final color = riskColor(p.risk);
                  return Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: color.withAlpha(15),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: color.withAlpha(60)),
                    ),
                    child: Text(
                      '${p.port} ${p.service}',
                      style: TextStyle(fontSize: 11, fontFamily: 'monospace', color: color, fontWeight: FontWeight.w600),
                    ),
                  );
                }).toList(),
              ),
            ]),
          ),
        ),
        const SizedBox(height: 10),
      ],

      // Active connections
      Card(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              const Icon(Icons.electrical_services_rounded, size: 14, color: AppTheme.slate500),
              const SizedBox(width: 6),
              Text('Active Connections (${r.connectionCount})', style: Theme.of(context).textTheme.titleSmall),
            ]),
            const SizedBox(height: 8),
            if (r.activeConnections.isEmpty)
              const Text('No active connections to this IP', style: TextStyle(fontSize: 12, color: AppTheme.slate400))
            else
              ...r.activeConnections.take(6).map((c) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Row(children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                    decoration: BoxDecoration(color: AppTheme.sky50, borderRadius: BorderRadius.circular(4)),
                    child: Text(c['protocol'] ?? '', style: const TextStyle(fontSize: 10, color: AppTheme.sky600, fontWeight: FontWeight.w700)),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '${c['remote_ip']}:${c['remote_port']}',
                      style: const TextStyle(fontSize: 11, fontFamily: 'monospace', color: AppTheme.slate700),
                    ),
                  ),
                  Text(
                    (c['process_name'] as String? ?? '').replaceAll('.exe', ''),
                    style: const TextStyle(fontSize: 10, color: AppTheme.slate400),
                  ),
                ]),
              )),
          ]),
        ),
      ),

      // Registered device
      if (r.registeredDevice != null) ...[
        const SizedBox(height: 10),
        Card(
          color: AppTheme.sky50,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: const BorderSide(color: AppTheme.sky500, width: 1),
          ),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                const Icon(Icons.dns_rounded, size: 14, color: AppTheme.sky600),
                const SizedBox(width: 6),
                Text('Registered Device', style: Theme.of(context).textTheme.titleSmall),
              ]),
              const SizedBox(height: 8),
              _Row('Name', r.registeredDevice!['name'] ?? ''),
              _Row('Type', r.registeredDevice!['type'] ?? ''),
              if ((r.registeredDevice!['mac'] as String? ?? '').isNotEmpty)
                _Row('MAC', r.registeredDevice!['mac'] ?? '', mono: true),
            ]),
          ),
        ),
      ],
      const SizedBox(height: 20),
    ]);
  }
}

class _SummaryBanner extends StatelessWidget {
  final IPInvestigation r;
  const _SummaryBanner({required this.r});

  @override
  Widget build(BuildContext context) {
    final color = riskColor(r.riskLevel);
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withAlpha(15),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withAlpha(80)),
      ),
      child: Row(children: [
        _riskIcon(r.riskLevel, color),
        const SizedBox(width: 12),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Text(r.ip, style: const TextStyle(fontFamily: 'monospace', fontSize: 16, fontWeight: FontWeight.w800, color: AppTheme.slate800)),
              const SizedBox(width: 8),
              StatusBadge.risk(r.riskLevel),
            ]),
            const SizedBox(height: 2),
            Text(
              r.hostname != r.ip ? r.hostname : (r.countryName.isNotEmpty ? r.countryName : 'Private Network'),
              style: const TextStyle(fontSize: 11, color: Color(0xFF475569)),
              overflow: TextOverflow.ellipsis,
            ),
          ]),
        ),
        Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
          Row(mainAxisSize: MainAxisSize.min, children: [
            Icon(r.isAlive ? Icons.wifi_rounded : Icons.wifi_off_rounded, size: 14, color: r.isAlive ? AppTheme.emerald500 : AppTheme.slate400),
            const SizedBox(width: 4),
            Text(
              r.isAlive ? (r.latencyMs != null ? '${r.latencyMs!.toInt()}ms' : 'Online') : 'Offline',
              style: TextStyle(fontSize: 11, color: r.isAlive ? AppTheme.emerald700 : AppTheme.slate400, fontWeight: FontWeight.w600),
            ),
          ]),
          if (r.flag.isNotEmpty) Text(r.flag, style: const TextStyle(fontSize: 18)),
        ]),
      ]),
    );
  }

  Widget _riskIcon(String risk, Color color) {
    IconData icon;
    switch (risk) {
      case 'critical': icon = Icons.gpp_bad_rounded; break;
      case 'high':     icon = Icons.warning_rounded; break;
      case 'medium':   icon = Icons.error_outline_rounded; break;
      default:         icon = Icons.verified_user_rounded; break;
    }
    return Icon(icon, color: color, size: 30);
  }
}

class _Row extends StatelessWidget {
  final String label;
  final String value;
  final bool mono;
  const _Row(this.label, this.value, {this.mono = false});

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 3),
    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      SizedBox(width: 90, child: Text(label, style: const TextStyle(fontSize: 12, color: AppTheme.slate500))),
      Expanded(
        child: Text(
          value.isEmpty ? '—' : value,
          style: TextStyle(fontSize: 12, color: AppTheme.slate800, fontWeight: FontWeight.w500, fontFamily: mono ? 'monospace' : null),
        ),
      ),
    ]),
  );
}

class _WarningRow extends StatelessWidget {
  final String text;
  final Color color;
  const _WarningRow(this.text, {this.color = AppTheme.amber700});

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 4),
    child: Row(children: [
      Icon(Icons.warning_amber_rounded, size: 13, color: color),
      const SizedBox(width: 5),
      Text(text, style: TextStyle(fontSize: 11, color: color, fontWeight: FontWeight.w700)),
    ]),
  );
}

