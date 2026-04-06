import 'package:flutter/material.dart';

class AppTheme {
  // Colour palette (mirrors the web Tailwind slate/sky palette)
  static const Color slate50  = Color(0xFFF8FAFC);
  static const Color slate100 = Color(0xFFF1F5F9);
  static const Color slate200 = Color(0xFFE2E8F0);
  static const Color slate300 = Color(0xFFCBD5E1);
  static const Color slate400 = Color(0xFF94A3B8);
  static const Color slate500 = Color(0xFF64748B);
  static const Color slate600 = Color(0xFF475569);
  static const Color slate700 = Color(0xFF334155);
  static const Color slate800 = Color(0xFF1E293B);

  static const Color sky500   = Color(0xFF0EA5E9);
  static const Color sky600   = Color(0xFF0284C7);
  static const Color sky50    = Color(0xFFF0F9FF);

  static const Color emerald500 = Color(0xFF10B981);
  static const Color emerald50  = Color(0xFFECFDF5);
  static const Color emerald700 = Color(0xFF047857);

  static const Color rose500  = Color(0xFFF43F5E);
  static const Color rose50   = Color(0xFFFFF1F2);
  static const Color rose700  = Color(0xFFBE123C);

  static const Color amber500 = Color(0xFFF59E0B);
  static const Color amber50  = Color(0xFFFFFBEB);
  static const Color amber700 = Color(0xFFB45309);

  static const Color yellow50  = Color(0xFFFEFCE8);
  static const Color yellow700 = Color(0xFFA16207);

  static ThemeData get light {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: sky600,
        brightness: Brightness.light,
        surface: slate50,
      ),
      scaffoldBackgroundColor: slate100,
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.white,
        foregroundColor: slate800,
        elevation: 0,
        shadowColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
        titleTextStyle: TextStyle(
          color: slate800,
          fontSize: 17,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.3,
        ),
      ),
      cardTheme: CardThemeData(
        color: Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: slate200, width: 1),
        ),
        margin: EdgeInsets.zero,
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: Colors.white,
        indicatorColor: sky50,
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: sky600,
            );
          }
          return const TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w500,
            color: slate500,
          );
        }),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const IconThemeData(color: sky600, size: 22);
          }
          return const IconThemeData(color: slate400, size: 22);
        }),
        elevation: 0,
        shadowColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
      ),
      chipTheme: ChipThemeData(
        backgroundColor: slate100,
        labelStyle: const TextStyle(fontSize: 11, color: slate700),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
      ),
      dividerTheme: const DividerThemeData(
        color: slate200,
        thickness: 1,
        space: 1,
      ),
      textTheme: const TextTheme(
        titleLarge:  TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: slate800, letterSpacing: -0.5),
        titleMedium: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: slate800, letterSpacing: -0.2),
        titleSmall:  TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: slate700),
        bodyMedium:  TextStyle(fontSize: 13, fontWeight: FontWeight.w400, color: slate700),
        bodySmall:   TextStyle(fontSize: 11, fontWeight: FontWeight.w400, color: slate500),
        labelLarge:  TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: sky600, letterSpacing: 0),
      ),
    );
  }
}

// Severity colour helpers
Color severityColor(String severity) {
  switch (severity.toLowerCase()) {
    case 'critical': return AppTheme.rose700;
    case 'high':     return AppTheme.amber700;
    case 'medium':   return const Color(0xFFA16207);
    case 'low':      return AppTheme.sky600;
    default:         return AppTheme.slate500;
  }
}

Color severityBg(String severity) {
  switch (severity.toLowerCase()) {
    case 'critical': return AppTheme.rose50;
    case 'high':     return AppTheme.amber50;
    case 'medium':   return AppTheme.yellow50;
    case 'low':      return AppTheme.sky50;
    default:         return AppTheme.slate100;
  }
}

Color riskColor(String risk) {
  switch (risk.toLowerCase()) {
    case 'critical': return AppTheme.rose700;
    case 'high':     return AppTheme.amber700;
    case 'medium':   return AppTheme.yellow700;
    case 'low':      return AppTheme.sky600;
    case 'none':     return AppTheme.emerald700;
    default:         return AppTheme.slate500;
  }
}
