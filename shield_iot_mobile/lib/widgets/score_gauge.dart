import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../theme/app_theme.dart';

class ScoreGauge extends StatelessWidget {
  final int score;
  final String grade;
  final double size;

  const ScoreGauge({super.key, required this.score, required this.grade, this.size = 120});

  Color get _color {
    if (score >= 90) return AppTheme.emerald500;
    if (score >= 75) return AppTheme.sky500;
    if (score >= 60) return const Color(0xFFF59E0B);
    if (score >= 45) return AppTheme.amber500;
    return AppTheme.rose500;
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size, height: size,
      child: CustomPaint(
        painter: _GaugePainter(score: score, color: _color),
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                grade,
                style: TextStyle(
                  fontSize: size * 0.28,
                  fontWeight: FontWeight.w800,
                  color: _color,
                  height: 1,
                ),
              ),
              Text(
                '$score',
                style: TextStyle(
                  fontSize: size * 0.16,
                  fontWeight: FontWeight.w600,
                  color: const Color(0xFF475569),
                  height: 1.2,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _GaugePainter extends CustomPainter {
  final int score;
  final Color color;

  _GaugePainter({required this.score, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width  / 2;
    final cy = size.height / 2;
    final r  = (size.width  / 2) - 8;
    const startAngle = math.pi * 0.75;
    const sweepAll   = math.pi * 1.5;

    // Track
    canvas.drawArc(
      Rect.fromCircle(center: Offset(cx, cy), radius: r),
      startAngle, sweepAll, false,
      Paint()
        ..color = AppTheme.slate200
        ..style = PaintingStyle.stroke
        ..strokeWidth = 8
        ..strokeCap = StrokeCap.round,
    );

    // Progress
    final sweep = sweepAll * (score / 100);
    canvas.drawArc(
      Rect.fromCircle(center: Offset(cx, cy), radius: r),
      startAngle, sweep, false,
      Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = 8
        ..strokeCap = StrokeCap.round,
    );
  }

  @override
  bool shouldRepaint(_GaugePainter old) => old.score != score;
}

