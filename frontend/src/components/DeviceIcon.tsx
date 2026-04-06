import {
  Thermometer,
  Camera,
  Speaker,
  Baby,
  Tv,
  Plug,
  Router,
  Cpu,
  Monitor,
  Smartphone,
  Printer,
  Home,
  Globe,
} from "lucide-react";

interface Props {
  type: string;
  className?: string;
}

export function DeviceIcon({ type, className = "w-5 h-5" }: Props) {
  const icons: Record<string, React.ElementType> = {
    // Simulated IoT types
    smart_thermostat: Thermometer,
    ip_camera: Camera,
    smart_speaker: Speaker,
    baby_monitor: Baby,
    smart_tv: Tv,
    smart_plug: Plug,
    router: Router,
    // Real device types
    workstation: Monitor,
    mobile: Smartphone,
    printer: Printer,
    smart_home: Home,
    iot_controller: Cpu,
    unknown: Globe,
  };
  const Icon = icons[type] ?? Cpu;
  return <Icon className={className} />;
}
