// Data models mirroring the backend API responses

class NetworkStatus {
  final bool agentRunning;
  final int cycleCount;
  final int threatsDetected;
  final int devicesIsolated;
  final String overallStatus;
  final int threatLevel;
  final String summary;
  final int deviceCount;
  final int alertCount;
  final String mode;

  const NetworkStatus({
    required this.agentRunning,
    required this.cycleCount,
    required this.threatsDetected,
    required this.devicesIsolated,
    required this.overallStatus,
    required this.threatLevel,
    required this.summary,
    required this.deviceCount,
    required this.alertCount,
    required this.mode,
  });

  factory NetworkStatus.fromJson(Map<String, dynamic> j) => NetworkStatus(
    agentRunning:     j['agent']?['running'] ?? false,
    cycleCount:       j['agent']?['cycle_count'] ?? 0,
    threatsDetected:  j['agent']?['threats_detected'] ?? 0,
    devicesIsolated:  j['agent']?['devices_isolated'] ?? 0,
    overallStatus:    j['network_summary']?['overall_status'] ?? 'unknown',
    threatLevel:      j['network_summary']?['threat_level'] ?? 0,
    summary:          j['network_summary']?['summary'] ?? '',
    deviceCount:      j['device_count'] ?? 0,
    alertCount:       j['alert_count'] ?? 0,
    mode:             j['mode'] ?? 'real',
  );
}

class Device {
  final String id;
  final String name;
  final String type;
  final String ip;
  final String mac;
  final String manufacturer;
  final String status;
  final String threatLevel;
  final bool isIsolated;
  final PortScanSummary? portScan;

  const Device({
    required this.id,
    required this.name,
    required this.type,
    required this.ip,
    required this.mac,
    required this.manufacturer,
    required this.status,
    required this.threatLevel,
    required this.isIsolated,
    this.portScan,
  });

  factory Device.fromJson(Map<String, dynamic> j) => Device(
    id:           j['id'] ?? '',
    name:         j['name'] ?? '',
    type:         j['type'] ?? 'unknown',
    ip:           j['ip'] ?? '',
    mac:          j['mac'] ?? '',
    manufacturer: j['manufacturer'] ?? '',
    status:       j['status'] ?? 'unknown',
    threatLevel:  j['threat_level'] ?? 'normal',
    isIsolated:   j['is_isolated'] ?? false,
    portScan: j['port_scan'] != null ? PortScanSummary.fromJson(j['port_scan']) : null,
  );
}

class PortScanSummary {
  final String riskLevel;
  final int? openPortCount;
  final String? scanTime;

  const PortScanSummary({required this.riskLevel, this.openPortCount, this.scanTime});

  factory PortScanSummary.fromJson(Map<String, dynamic> j) => PortScanSummary(
    riskLevel:     j['risk_level'] ?? 'unknown',
    openPortCount: j['open_port_count'],
    scanTime:      j['scan_time'],
  );
}

class Alert {
  final String id;
  final String deviceId;
  final String deviceName;
  final String type;
  final String severity;
  final String status;
  final String description;
  final String timestamp;
  final double? anomalyScore;

  const Alert({
    required this.id,
    required this.deviceId,
    required this.deviceName,
    required this.type,
    required this.severity,
    required this.status,
    required this.description,
    required this.timestamp,
    this.anomalyScore,
  });

  factory Alert.fromJson(Map<String, dynamic> j) => Alert(
    id:          j['id'] ?? '',
    deviceId:    j['device_id'] ?? '',
    deviceName:  j['device_name'] ?? '',
    type:        j['type'] ?? '',
    severity:    j['severity'] ?? 'low',
    status:      j['status'] ?? 'active',
    description: j['description'] ?? '',
    timestamp:   j['timestamp'] ?? '',
    anomalyScore: (j['anomaly_score'] as num?)?.toDouble(),
  );
}

class LiveConnection {
  final String localIp;
  final int localPort;
  final String remoteIp;
  final int remotePort;
  final String hostname;
  final String protocol;
  final String processName;
  final bool isOutbound;
  final bool isPrivate;
  final String country;
  final String city;
  final String flag;
  final bool isMaliciousIp;
  final bool isSuspicious;

  const LiveConnection({
    required this.localIp,
    required this.localPort,
    required this.remoteIp,
    required this.remotePort,
    required this.hostname,
    required this.protocol,
    required this.processName,
    required this.isOutbound,
    required this.isPrivate,
    required this.country,
    required this.city,
    required this.flag,
    required this.isMaliciousIp,
    required this.isSuspicious,
  });

  factory LiveConnection.fromJson(Map<String, dynamic> j) => LiveConnection(
    localIp:      j['local_ip'] ?? '',
    localPort:    j['local_port'] ?? 0,
    remoteIp:     j['remote_ip'] ?? '',
    remotePort:   j['remote_port'] ?? 0,
    hostname:     j['hostname'] ?? '',
    protocol:     j['protocol'] ?? '',
    processName:  j['process_name'] ?? '',
    isOutbound:   j['is_outbound'] ?? true,
    isPrivate:    j['is_private'] ?? false,
    country:      j['country'] ?? '',
    city:         j['city'] ?? '',
    flag:         j['flag'] ?? '🌐',
    isMaliciousIp: j['is_malicious_ip'] ?? false,
    isSuspicious:  j['is_suspicious'] ?? false,
  );
}

class BandwidthPoint {
  final DateTime ts;
  final double sentKbps;
  final double recvKbps;

  const BandwidthPoint({required this.ts, required this.sentKbps, required this.recvKbps});

  factory BandwidthPoint.fromJson(Map<String, dynamic> j) => BandwidthPoint(
    ts:       DateTime.tryParse(j['ts'] ?? '') ?? DateTime.now(),
    sentKbps: (j['sent_kbps'] as num?)?.toDouble() ?? 0,
    recvKbps: (j['recv_kbps'] as num?)?.toDouble() ?? 0,
  );
}

class SecurityScore {
  final int score;
  final String grade;
  final String color;
  final List<ScoreFactor> factors;

  const SecurityScore({
    required this.score,
    required this.grade,
    required this.color,
    required this.factors,
  });

  factory SecurityScore.fromJson(Map<String, dynamic> j) => SecurityScore(
    score:   j['score'] ?? 0,
    grade:   j['grade'] ?? 'F',
    color:   j['color'] ?? 'rose',
    factors: (j['factors'] as List<dynamic>? ?? [])
        .map((f) => ScoreFactor.fromJson(f as Map<String, dynamic>))
        .toList(),
  );
}

class ScoreFactor {
  final String name;
  final int deduction;
  final String status;

  const ScoreFactor({required this.name, required this.deduction, required this.status});

  factory ScoreFactor.fromJson(Map<String, dynamic> j) => ScoreFactor(
    name:      j['name'] ?? '',
    deduction: j['deduction'] ?? 0,
    status:    j['status'] ?? 'pass',
  );
}

class IPInvestigation {
  final String ip;
  final String hostname;
  final bool isPrivate;
  final bool isAlive;
  final double? latencyMs;
  final String riskLevel;
  final String country;
  final String countryName;
  final String city;
  final String isp;
  final String flag;
  final bool isHighRiskCountry;
  final bool isMalicious;
  final String threatSource;
  final List<OpenPort> openPorts;
  final List<Map<String, dynamic>> activeConnections;
  final int connectionCount;
  final Map<String, dynamic>? registeredDevice;

  const IPInvestigation({
    required this.ip,
    required this.hostname,
    required this.isPrivate,
    required this.isAlive,
    this.latencyMs,
    required this.riskLevel,
    required this.country,
    required this.countryName,
    required this.city,
    required this.isp,
    required this.flag,
    required this.isHighRiskCountry,
    required this.isMalicious,
    required this.threatSource,
    required this.openPorts,
    required this.activeConnections,
    required this.connectionCount,
    this.registeredDevice,
  });

  factory IPInvestigation.fromJson(Map<String, dynamic> j) => IPInvestigation(
    ip:              j['ip'] ?? '',
    hostname:        j['hostname'] ?? '',
    isPrivate:       j['is_private'] ?? false,
    isAlive:         j['is_alive'] ?? false,
    latencyMs:       (j['latency_ms'] as num?)?.toDouble(),
    riskLevel:       j['risk_level'] ?? 'none',
    country:         j['country'] ?? '',
    countryName:     j['country_name'] ?? '',
    city:            j['city'] ?? '',
    isp:             j['isp'] ?? '',
    flag:            j['flag'] ?? '🌐',
    isHighRiskCountry: j['is_high_risk_country'] ?? false,
    isMalicious:     j['is_malicious'] ?? false,
    threatSource:    j['threat_source'] ?? 'clean',
    openPorts: (j['open_ports'] as List<dynamic>? ?? [])
        .map((p) => OpenPort.fromJson(p as Map<String, dynamic>))
        .toList(),
    activeConnections: (j['active_connections'] as List<dynamic>? ?? [])
        .cast<Map<String, dynamic>>(),
    connectionCount: j['connection_count'] ?? 0,
    registeredDevice: j['registered_device'] as Map<String, dynamic>?,
  );
}

class OpenPort {
  final int port;
  final String service;
  final String risk;

  const OpenPort({required this.port, required this.service, required this.risk});

  factory OpenPort.fromJson(Map<String, dynamic> j) => OpenPort(
    port:    j['port'] ?? 0,
    service: j['service'] ?? '',
    risk:    j['risk'] ?? 'low',
  );
}
