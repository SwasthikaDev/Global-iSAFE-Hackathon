import {
  Thermometer,
  Camera,
  Speaker,
  Baby,
  Tv,
  Plug,
  Router,
  Cpu,
} from "lucide-react";

interface Props {
  type: string;
  className?: string;
}

export function DeviceIcon({ type, className = "w-5 h-5" }: Props) {
  const icons: Record<string, React.ElementType> = {
    smart_thermostat: Thermometer,
    ip_camera: Camera,
    smart_speaker: Speaker,
    baby_monitor: Baby,
    smart_tv: Tv,
    smart_plug: Plug,
    router: Router,
  };
  const Icon = icons[type] ?? Cpu;
  return <Icon className={className} />;
}
