import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/models.dart';
import '../services/app_state.dart';
import '../theme/app_theme.dart';
import '../widgets/score_gauge.dart';
import '../widgets/status_badge.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();

    if (state.isLoading && state.networkStatus == null) {
      return const Center(child: CircularProgressIndicator());
    }

    if (!state.isConnected && state.networkStatus == null) {
      return _ErrorView(message: state.errorMsg ?? 'Cannot reach server', onRetry: state.refresh);
    }

    final ns = state.networkStatus!;
    return RefreshIndicator(
      onRefresh: state.refresh,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // ── Status bar ──────────────────────────────────────────────────
          _StatusBanner(status: ns.overallStatus, summary: ns.summary, mode: ns.mode),
          const SizedBox(height: 12),

          // ── Stats row ───────────────────────────────────────────────────
          Row(children: [
            _StatCard(label: 'Devices',  value: '${ns.deviceCount}',      icon: Icons.devices_rounded,       color: AppTheme.sky600),
            const SizedBox(width: 10),
            _StatCard(label: 'Alerts',   value: '${ns.alertCount}',       icon: Icons.notifications_rounded, color: ns.alertCount > 0 ? AppTheme.rose500 : AppTheme.emerald500),
            const SizedBox(width: 10),
            _StatCard(label: 'Cycles',   value: '${ns.cycleCount}',       icon: Icons.loop_rounded,          color: AppTheme.slate500),
          ]),
          const SizedBox(height: 12),

          // ── Security score + factor list ─────────────────────────────
          if (state.securityScore != null) ...[
            _SecurityScoreCard(securityScore: state.securityScore!),
            const SizedBox(height: 12),
          ],

          // ── Bandwidth chart ──────────────────────────────────────────
          if (state.bandwidth.isNotEmpty) ...[
            _BandwidthCard(state: state),
            const SizedBox(height: 12),
          ],

          // ── Last refresh ─────────────────────────────────────────────
          if (state.lastRefresh != null)
            Center(
              child: Text(
                'Last updated ${_timeAgo(state.lastRefresh!)}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}

// ── Widgets ──────────────────────────────────────────────────────────────────

class _StatusBanner extends StatelessWidget {
  final String status;
  final String summary;
  final String mode;

  const _StatusBanner({required this.status, required this.summary, required this.mode});

  @override
  Widget build(BuildContext context) {
    final isSecure  = status == 'secure';
    final bgColor   = isSecure ? AppTheme.emerald50  : AppTheme.rose50;
    final bdColor   = isSecure ? AppTheme.emerald500 : AppTheme.rose500;
    final icon      = isSecure ? Icons.shield_rounded : Icons.warning_rounded;
    final textColor = isSecure ? AppTheme.emerald700  : AppTheme.rose700;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: bdColor.withAlpha(100)),
      ),
      child: Row(children: [
        Icon(icon, color: bdColor, size: 28),
        const SizedBox(width: 12),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(
              isSecure ? 'Network Secure' : 'Threat Detected',
              style: TextStyle(fontWeight: FontWeight.w700, color: textColor, fontSize: 14),
            ),
            const SizedBox(height: 2),
            Text(summary, style: TextStyle(fontSize: 12, color: textColor.withAlpha(200))),
          ]),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
          decoration: BoxDecoration(
            color: mode == 'real' ? AppTheme.emerald50 : AppTheme.sky50,
            borderRadius: BorderRadius.circular(6),
            border: Border.all(color: mode == 'real' ? AppTheme.emerald500 : AppTheme.sky600, width: 1),
          ),
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            LiveDot(color: mode == 'real' ? AppTheme.emerald500 : AppTheme.sky500),
            const SizedBox(width: 4),
            Text(
              mode == 'real' ? 'Live' : 'Sim',
              style: TextStyle(
                fontSize: 10, fontWeight: FontWeight.w700,
                color: mode == 'real' ? AppTheme.emerald700 : AppTheme.sky600,
              ),
            ),
          ]),
        ),
      ]),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;

  const _StatCard({required this.label, required this.value, required this.icon, required this.color});

  @override
  Widget build(BuildContext context) => Expanded(
    child: Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
        child: Column(children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 6),
          Text(value, style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: color)),
          Text(label, style: Theme.of(context).textTheme.bodySmall),
        ]),
      ),
    ),
  );
}

class _SecurityScoreCard extends StatelessWidget {
  final SecurityScore securityScore;
  const _SecurityScoreCard({required this.securityScore});

  @override
  Widget build(BuildContext context) {
    final s = securityScore;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Icon(Icons.security_rounded, size: 16, color: AppTheme.slate500),
            const SizedBox(width: 6),
            Text('Security Score', style: Theme.of(context).textTheme.titleSmall),
          ]),
          const SizedBox(height: 16),
          Row(crossAxisAlignment: CrossAxisAlignment.center, children: [
            ScoreGauge(score: s.score, grade: s.grade),
            const SizedBox(width: 20),
            Expanded(
              child: Column(
                children: s.factors.take(4).map<Widget>((f) {
                  final isPass = f.status == 'pass';
                  final icon   = isPass ? Icons.check_circle_rounded : Icons.cancel_rounded;
                  final color  = isPass ? AppTheme.emerald500 : (f.status == 'warn' ? AppTheme.amber500 : AppTheme.rose500);
                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 3),
                    child: Row(children: [
                      Icon(icon, size: 14, color: color),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          f.name,
                          style: const TextStyle(fontSize: 11, color: AppTheme.slate700),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      if (!isPass)
                        Text('${f.deduction}', style: const TextStyle(fontSize: 11, color: AppTheme.rose700, fontWeight: FontWeight.w600)),
                    ]),
                  );
                }).toList(),
              ),
            ),
          ]),
        ]),
      ),
    );
  }
}

class _BandwidthCard extends StatelessWidget {
  final AppState state;
  const _BandwidthCard({required this.state});

  @override
  Widget build(BuildContext context) {
    final points = state.bandwidth.take(30).toList();
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Icon(Icons.show_chart_rounded, size: 16, color: AppTheme.slate500),
            const SizedBox(width: 6),
            Text('Bandwidth', style: Theme.of(context).textTheme.titleSmall),
            const Spacer(),
            _BwStat(label: '↑', value: state.currentSentKbps, color: AppTheme.sky600),
            const SizedBox(width: 12),
            _BwStat(label: '↓', value: state.currentRecvKbps, color: AppTheme.emerald500),
          ]),
          const SizedBox(height: 12),
          SizedBox(
            height: 80,
            child: LineChart(LineChartData(
              gridData: const FlGridData(show: false),
              titlesData: const FlTitlesData(show: false),
              borderData: FlBorderData(show: false),
              lineTouchData: const LineTouchData(enabled: false),
              lineBarsData: [
                _line(points.map((p) => p.sentKbps).toList(), AppTheme.sky500),
                _line(points.map((p) => p.recvKbps).toList(), AppTheme.emerald500),
              ],
            )),
          ),
          const SizedBox(height: 8),
          Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            _legend(AppTheme.sky500, 'Upload'),
            const SizedBox(width: 16),
            _legend(AppTheme.emerald500, 'Download'),
          ]),
        ]),
      ),
    );
  }

  LineChartBarData _line(List<double> data, Color color) => LineChartBarData(
    spots: data.asMap().entries.map((e) => FlSpot(e.key.toDouble(), e.value)).toList(),
    isCurved: true,
    color: color,
    barWidth: 2,
    dotData: const FlDotData(show: false),
    belowBarData: BarAreaData(
      show: true,
      color: color.withAlpha(30),
    ),
  );

  Widget _legend(Color c, String label) => Row(children: [
    Container(width: 12, height: 3, decoration: BoxDecoration(color: c, borderRadius: BorderRadius.circular(2))),
    const SizedBox(width: 4),
    Text(label, style: const TextStyle(fontSize: 10, color: AppTheme.slate500)),
  ]);
}

class _BwStat extends StatelessWidget {
  final String label;
  final double value;
  final Color color;

  const _BwStat({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) => Row(mainAxisSize: MainAxisSize.min, children: [
    Text(label, style: TextStyle(fontSize: 11, color: color, fontWeight: FontWeight.w700)),
    const SizedBox(width: 3),
    Text('${value.toStringAsFixed(1)} KB/s', style: const TextStyle(fontSize: 11, color: AppTheme.slate700)),
  ]);
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(32),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        const Icon(Icons.wifi_off_rounded, size: 48, color: AppTheme.slate400),
        const SizedBox(height: 16),
        Text('Cannot reach SHIELD-IoT server', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        Text(message, style: Theme.of(context).textTheme.bodySmall, textAlign: TextAlign.center),
        const SizedBox(height: 24),
        ElevatedButton.icon(
          onPressed: onRetry,
          icon: const Icon(Icons.refresh_rounded),
          label: const Text('Retry'),
        ),
      ]),
    ),
  );
}

String _timeAgo(DateTime dt) {
  final diff = DateTime.now().difference(dt);
  if (diff.inSeconds < 10) return 'just now';
  if (diff.inSeconds < 60) return '${diff.inSeconds}s ago';
  return '${diff.inMinutes}m ago';
}
