import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class StatusBadge extends StatelessWidget {
  final String label;
  final Color color;
  final Color bg;

  const StatusBadge({super.key, required this.label, required this.color, required this.bg});

  factory StatusBadge.severity(String severity) => StatusBadge(
    label: severity.toUpperCase(),
    color: severityColor(severity),
    bg:    severityBg(severity),
  );

  factory StatusBadge.risk(String risk) => StatusBadge(
    label: risk.toUpperCase(),
    color: riskColor(risk),
    bg:    _riskBg(risk),
  );

  static Color _riskBg(String risk) {
    switch (risk.toLowerCase()) {
      case 'critical': return AppTheme.rose50;
      case 'high':     return AppTheme.amber50;
      case 'medium':   return AppTheme.yellow50;
      case 'low':      return AppTheme.sky50;
      case 'none':     return AppTheme.emerald50;
      default:         return AppTheme.slate100;
    }
  }

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
    decoration: BoxDecoration(
      color: bg,
      borderRadius: BorderRadius.circular(6),
      border: Border.all(color: color.withAlpha(50)),
    ),
    child: Text(
      label,
      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: color, letterSpacing: 0.3),
    ),
  );
}

class LiveDot extends StatefulWidget {
  final Color color;
  const LiveDot({super.key, required this.color});

  @override
  State<LiveDot> createState() => _LiveDotState();
}

class _LiveDotState extends State<LiveDot> with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(seconds: 1))
      ..repeat(reverse: true);
    _anim = Tween<double>(begin: 0.3, end: 1.0).animate(_ctrl);
  }

  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) => FadeTransition(
    opacity: _anim,
    child: Container(
      width: 8, height: 8,
      decoration: BoxDecoration(color: widget.color, shape: BoxShape.circle),
    ),
  );
}
