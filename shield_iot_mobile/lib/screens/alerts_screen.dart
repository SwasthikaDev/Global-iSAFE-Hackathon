import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/app_state.dart';
import '../models/models.dart';
import '../theme/app_theme.dart';
import '../widgets/status_badge.dart';

class AlertsScreen extends StatelessWidget {
  const AlertsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final alerts = context.watch<AppState>().alerts;

    return RefreshIndicator(
      onRefresh: context.read<AppState>().refresh,
      child: alerts.isEmpty
          ? _AllClearView()
          : ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: alerts.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (ctx, i) => _AlertCard(alert: alerts[i]),
            ),
    );
  }
}

class _AllClearView extends StatelessWidget {
  @override
  Widget build(BuildContext context) => Center(
    child: Column(mainAxisSize: MainAxisSize.min, children: [
      const Icon(Icons.shield_rounded, size: 56, color: AppTheme.emerald500),
      const SizedBox(height: 16),
      Text('All Clear', style: Theme.of(context).textTheme.titleLarge?.copyWith(color: AppTheme.emerald700)),
      const SizedBox(height: 8),
      Text(
        'No active threats detected.\nSHIELD-IoT is monitoring live traffic.',
        style: Theme.of(context).textTheme.bodySmall,
        textAlign: TextAlign.center,
      ),
    ]),
  );
}

class _AlertCard extends StatelessWidget {
  final Alert alert;
  const _AlertCard({required this.alert});

  @override
  Widget build(BuildContext context) {
    final isActive = alert.status == 'active';
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => _showDetail(context),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            // Severity indicator
            Container(
              width: 4, height: 50,
              decoration: BoxDecoration(
                color: severityColor(alert.severity),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(width: 12),

            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Expanded(
                    child: Text(
                      alert.type.replaceAll('_', ' ').toUpperCase(),
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppTheme.slate700, letterSpacing: 0.3),
                    ),
                  ),
                  StatusBadge.severity(alert.severity),
                  if (!isActive) ...[
                    const SizedBox(width: 4),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                      decoration: BoxDecoration(
                        color: AppTheme.slate100,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: const Text('resolved', style: TextStyle(fontSize: 9, color: AppTheme.slate500)),
                    ),
                  ],
                ]),
                const SizedBox(height: 4),
                Text(
                  alert.description,
                  style: Theme.of(context).textTheme.bodySmall,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 6),
                Row(children: [
                  const Icon(Icons.devices_rounded, size: 12, color: AppTheme.slate400),
                  const SizedBox(width: 4),
                  Text(alert.deviceName, style: const TextStyle(fontSize: 11, color: AppTheme.slate500)),
                  const Spacer(),
                  Text(_formatTs(alert.timestamp), style: const TextStyle(fontSize: 10, color: AppTheme.slate400)),
                ]),
              ]),
            ),
          ]),
        ),
      ),
    );
  }

  void _showDetail(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Center(
            child: Container(width: 36, height: 4, decoration: BoxDecoration(color: AppTheme.slate200, borderRadius: BorderRadius.circular(2))),
          ),
          const SizedBox(height: 16),
          Row(children: [
            StatusBadge.severity(alert.severity),
            const SizedBox(width: 8),
            Text(
              alert.type.replaceAll('_', ' ').toUpperCase(),
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppTheme.slate800),
            ),
          ]),
          const SizedBox(height: 12),
          Text(alert.description, style: const TextStyle(fontSize: 13, color: AppTheme.slate700)),
          const Divider(height: 24),
          _Row('Device',    alert.deviceName),
          _Row('Status',    alert.status),
          _Row('Timestamp', _formatTs(alert.timestamp)),
          if (alert.anomalyScore != null)
            _Row('Anomaly score', alert.anomalyScore!.toStringAsFixed(3)),
          const SizedBox(height: 16),
        ]),
      ),
    );
  }
}

class _Row extends StatelessWidget {
  final String label;
  final String value;
  const _Row(this.label, this.value);

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 4),
    child: Row(children: [
      SizedBox(width: 110, child: Text(label, style: const TextStyle(fontSize: 12, color: AppTheme.slate500))),
      Expanded(child: Text(value, style: const TextStyle(fontSize: 12, color: AppTheme.slate800, fontWeight: FontWeight.w500))),
    ]),
  );
}

String _formatTs(String ts) {
  if (ts.isEmpty) return '—';
  try {
    final dt = DateTime.parse(ts).toLocal();
    return '${dt.hour.toString().padLeft(2,'0')}:${dt.minute.toString().padLeft(2,'0')}:${dt.second.toString().padLeft(2,'0')}';
  } catch (_) { return ts; }
}
