import 'package:flutter/material.dart';

IconData deviceIconData(String type) {
  switch (type) {
    case 'router':           return Icons.router_rounded;
    case 'smart_thermostat': return Icons.thermostat_rounded;
    case 'ip_camera':        return Icons.videocam_rounded;
    case 'smart_speaker':    return Icons.speaker_rounded;
    case 'baby_monitor':     return Icons.baby_changing_station_rounded;
    case 'smart_tv':         return Icons.tv_rounded;
    case 'smart_plug':       return Icons.electrical_services_rounded;
    case 'workstation':      return Icons.computer_rounded;
    case 'mobile':           return Icons.smartphone_rounded;
    case 'printer':          return Icons.print_rounded;
    case 'smart_home':       return Icons.home_rounded;
    case 'iot_controller':   return Icons.memory_rounded;
    default:                  return Icons.device_unknown_rounded;
  }
}

class DeviceIconWidget extends StatelessWidget {
  final String type;
  final double size;
  final Color? color;

  const DeviceIconWidget({super.key, required this.type, this.size = 22, this.color});

  @override
  Widget build(BuildContext context) => Icon(
    deviceIconData(type),
    size: size,
    color: color ?? Theme.of(context).colorScheme.primary,
  );
}
