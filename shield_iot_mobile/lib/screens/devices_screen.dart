import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/app_state.dart';
import '../models/models.dart';
import '../theme/app_theme.dart';
import '../widgets/status_badge.dart';
import '../widgets/device_icon.dart';

class DevicesScreen extends StatelessWidget {
  const DevicesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final devices = context.watch<AppState>().devices;

    return RefreshIndicator(
      onRefresh: context.read<AppState>().refresh,
      child: devices.isEmpty
          ? const Center(child: Text('No devices found'))
          : ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: devices.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (ctx, i) => _DeviceCard(device: devices[i]),
            ),
    );
  }
}

class _DeviceCard extends StatelessWidget {
  final Device device;
  const _DeviceCard({required this.device});

  @override
  Widget build(BuildContext context) {
    final isIsolated  = device.isIsolated;
    final threatLevel = device.threatLevel;
    final hasThreat   = threatLevel != 'normal' && threatLevel.isNotEmpty;

    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => _showDeviceDetail(context, device),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(children: [
            // Icon
            Container(
              width: 44, height: 44,
              decoration: BoxDecoration(
                color: hasThreat ? AppTheme.rose50 : AppTheme.sky50,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Center(
                child: DeviceIconWidget(
                  type: device.type,
                  size: 22,
                  color: hasThreat ? AppTheme.rose500 : AppTheme.sky600,
                ),
              ),
            ),
            const SizedBox(width: 12),

            // Info
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Expanded(
                    child: Text(
                      device.name,
                      style: Theme.of(context).textTheme.titleSmall,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  if (isIsolated)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: AppTheme.amber50,
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(color: AppTheme.amber500.withAlpha(80)),
                      ),
                      child: const Text('ISOLATED', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: AppTheme.amber700)),
                    ),
                ]),
                const SizedBox(height: 2),
                Text(device.ip, style: Theme.of(context).textTheme.bodySmall?.copyWith(fontFamily: 'monospace')),
                const SizedBox(height: 6),
                Row(children: [
                  StatusBadge.severity(threatLevel.isEmpty ? 'normal' : threatLevel),
                  if (device.portScan?.scanTime != null) ...[
                    const SizedBox(width: 6),
                    _PortBadge(scan: device.portScan!),
                  ],
                ]),
              ]),
            ),

            const Icon(Icons.chevron_right_rounded, color: AppTheme.slate400),
          ]),
        ),
      ),
    );
  }

  void _showDeviceDetail(BuildContext context, Device device) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _DeviceDetailSheet(device: device),
    );
  }
}

class _PortBadge extends StatelessWidget {
  final PortScanSummary scan;
  const _PortBadge({required this.scan});

  @override
  Widget build(BuildContext context) {
    final color = riskColor(scan.riskLevel);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withAlpha(15),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color.withAlpha(60)),
      ),
      child: Text(
        '${scan.openPortCount ?? 0} ports · ${scan.riskLevel}',
        style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: color),
      ),
    );
  }
}

class _DeviceDetailSheet extends StatelessWidget {
  final Device device;
  const _DeviceDetailSheet({required this.device});

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.6,
      maxChildSize: 0.9,
      minChildSize: 0.4,
      expand: false,
      builder: (_, ctrl) => SingleChildScrollView(
        controller: ctrl,
        padding: const EdgeInsets.all(20),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          // Handle
          Center(
            child: Container(
              width: 36, height: 4,
              decoration: BoxDecoration(color: AppTheme.slate200, borderRadius: BorderRadius.circular(2)),
            ),
          ),
          const SizedBox(height: 16),

          // Header
          Row(children: [
            DeviceIconWidget(type: device.type, size: 28, color: AppTheme.sky600),
            const SizedBox(width: 10),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(device.name, style: Theme.of(context).textTheme.titleMedium),
                Text(device.type.replaceAll('_', ' '), style: Theme.of(context).textTheme.bodySmall),
              ]),
            ),
          ]),
          const Divider(height: 24),

          // Fields
          _Field('IP Address',   device.ip,           mono: true),
          _Field('MAC Address',  device.mac,           mono: true),
          _Field('Manufacturer', device.manufacturer),
          _Field('Status',       device.status),
          _Field('Threat Level', device.threatLevel),
          if (device.isIsolated)
            const _Field('Isolated', 'Yes — traffic is blocked'),

          if (device.portScan != null) ...[
            const Divider(height: 24),
            Text('Port Scan', style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 8),
            _Field('Risk Level',  device.portScan!.riskLevel),
            _Field('Open Ports',  '${device.portScan!.openPortCount ?? 0}'),
            if (device.portScan!.scanTime != null)
              _Field('Scanned At', device.portScan!.scanTime!),
          ],
          const SizedBox(height: 20),
        ]),
      ),
    );
  }
}

class _Field extends StatelessWidget {
  final String label;
  final String value;
  final bool mono;

  const _Field(this.label, this.value, {this.mono = false});

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 5),
    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      SizedBox(
        width: 110,
        child: Text(label, style: Theme.of(context).textTheme.bodySmall),
      ),
      Expanded(
        child: Text(
          value.isEmpty ? '—' : value,
          style: TextStyle(
            fontSize: 13,
            color: AppTheme.slate700,
            fontFamily: mono ? 'monospace' : null,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
    ]),
  );
}
