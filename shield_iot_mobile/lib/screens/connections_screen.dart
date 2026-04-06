import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/app_state.dart';
import '../models/models.dart';
import '../theme/app_theme.dart';

class ConnectionsScreen extends StatefulWidget {
  const ConnectionsScreen({super.key});

  @override
  State<ConnectionsScreen> createState() => _ConnectionsScreenState();
}

class _ConnectionsScreenState extends State<ConnectionsScreen> {
  String _search = '';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppState>().refreshConnections();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state   = context.watch<AppState>();
    final all     = state.connections;
    final conns   = _search.isEmpty
        ? all
        : all.where((c) =>
            c.remoteIp.contains(_search) ||
            c.hostname.toLowerCase().contains(_search.toLowerCase()) ||
            c.processName.toLowerCase().contains(_search.toLowerCase()) ||
            c.country.toLowerCase().contains(_search.toLowerCase())).toList();

    return Column(children: [
      // Search bar
      Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
        child: TextField(
          onChanged: (v) => setState(() => _search = v),
          decoration: InputDecoration(
            hintText: 'Filter by IP, process, country…',
            prefixIcon: const Icon(Icons.search_rounded, size: 20),
            isDense: true,
            filled: true,
            fillColor: Colors.white,
            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(color: AppTheme.slate200),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(color: AppTheme.slate200),
            ),
          ),
        ),
      ),

      // Stats row
      if (all.isNotEmpty)
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
          child: Row(children: [
            Text('${conns.length} connections', style: Theme.of(context).textTheme.bodySmall),
            const Spacer(),
            _statChip(Icons.warning_rounded, '${all.where((c) => c.isMaliciousIp).length} malicious', AppTheme.rose500),
            const SizedBox(width: 6),
            _statChip(Icons.public_rounded, '${all.where((c) => !c.isPrivate).length} external', AppTheme.sky600),
          ]),
        ),

      // List
      Expanded(
        child: RefreshIndicator(
          onRefresh: () => context.read<AppState>().refreshConnections(),
          child: conns.isEmpty
              ? const Center(child: Text('No connections'))
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  itemCount: conns.length,
                  itemBuilder: (ctx, i) => _ConnectionRow(conn: conns[i]),
                ),
        ),
      ),
    ]);
  }

  Widget _statChip(IconData icon, String label, Color color) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
    decoration: BoxDecoration(
      color: color.withAlpha(15),
      borderRadius: BorderRadius.circular(6),
      border: Border.all(color: color.withAlpha(50)),
    ),
    child: Row(mainAxisSize: MainAxisSize.min, children: [
      Icon(icon, size: 11, color: color),
      const SizedBox(width: 3),
      Text(label, style: TextStyle(fontSize: 10, color: color, fontWeight: FontWeight.w600)),
    ]),
  );
}

class _ConnectionRow extends StatelessWidget {
  final LiveConnection conn;
  const _ConnectionRow({required this.conn});

  @override
  Widget build(BuildContext context) {
    Color bg = Colors.white;
    Color bd = AppTheme.slate200;
    if (conn.isMaliciousIp)  { bg = AppTheme.rose50;   bd = AppTheme.rose500; }
    else if (conn.isSuspicious) { bg = AppTheme.amber50; bd = AppTheme.amber500; }

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 3),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: bd.withAlpha(conn.isMaliciousIp || conn.isSuspicious ? 120 : 60)),
      ),
      child: Row(children: [
        // Protocol badge
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
          decoration: BoxDecoration(
            color: AppTheme.sky50,
            borderRadius: BorderRadius.circular(4),
          ),
          child: Text(conn.protocol, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: AppTheme.sky600, fontFamily: 'monospace')),
        ),
        const SizedBox(width: 10),

        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Expanded(
                child: Text(
                  conn.hostname != conn.remoteIp ? conn.hostname : conn.remoteIp,
                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.slate800),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              if (conn.flag.isNotEmpty)
                Text(conn.flag, style: const TextStyle(fontSize: 14)),
            ]),
            const SizedBox(height: 2),
            Text(
              '${conn.remoteIp}:${conn.remotePort}  ·  ${conn.processName}',
              style: const TextStyle(fontSize: 10, color: AppTheme.slate500, fontFamily: 'monospace'),
              overflow: TextOverflow.ellipsis,
            ),
          ]),
        ),

        if (conn.isMaliciousIp)
          const Icon(Icons.gpp_bad_rounded, size: 16, color: AppTheme.rose500),
        if (!conn.isMaliciousIp && conn.isSuspicious)
          const Icon(Icons.warning_amber_rounded, size: 16, color: AppTheme.amber500),
      ]),
    );
  }
}
