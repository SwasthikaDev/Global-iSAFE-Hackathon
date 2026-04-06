import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:async';
import 'dart:convert';
import '../models/models.dart';
import 'api_service.dart';

class AppState extends ChangeNotifier {
  // ── Server configuration ─────────────────────────────────────────────────
  String _serverUrl = 'http://192.168.1.4:8000';
  String get serverUrl => _serverUrl;

  late ApiService _api;

  // ── Data ─────────────────────────────────────────────────────────────────
  NetworkStatus? networkStatus;
  List<Device>  devices       = [];
  List<Alert>   alerts        = [];
  SecurityScore? securityScore;
  List<LiveConnection> connections = [];
  List<BandwidthPoint> bandwidth   = [];
  double currentSentKbps = 0;
  double currentRecvKbps = 0;
  double peakSentKbps    = 0;
  double peakRecvKbps    = 0;

  // ── State ─────────────────────────────────────────────────────────────────
  bool isLoading     = false;
  bool isConnected   = false;
  String? errorMsg;
  DateTime? lastRefresh;

  // ── WebSocket ────────────────────────────────────────────────────────────
  WebSocketChannel? _ws;
  StreamSubscription? _wsSub;
  Timer? _refreshTimer;

  AppState() {
    _api = ApiService(_serverUrl);
    _loadPrefs();
  }

  Future<void> _loadPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    _serverUrl = prefs.getString('server_url') ?? _serverUrl;
    _api = ApiService(_serverUrl);
    refresh();
  }

  Future<void> setServerUrl(String url) async {
    _serverUrl = url.trimRight().replaceAll(RegExp(r'/$'), '');
    _api = ApiService(_serverUrl);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('server_url', _serverUrl);
    _disconnectWs();
    refresh();
  }

  // ── Refresh all data ─────────────────────────────────────────────────────
  Future<void> refresh() async {
    isLoading = true;
    errorMsg  = null;
    notifyListeners();
    try {
      final results = await Future.wait([
        _api.getNetworkStatus(),
        _api.getDevices(),
        _api.getAlerts(),
        _api.getSecurityScore(),
        _api.getBandwidth(),
      ]);
      networkStatus = results[0] as NetworkStatus;
      devices       = results[1] as List<Device>;
      alerts        = results[2] as List<Alert>;
      securityScore = results[3] as SecurityScore;
      final bw = results[4] as Map<String, dynamic>;
      bandwidth     = (bw['history'] as List<dynamic>? ?? [])
          .map((p) => BandwidthPoint.fromJson(p as Map<String, dynamic>))
          .toList();
      currentSentKbps = (bw['current_sent_kbps'] as num?)?.toDouble() ?? 0;
      currentRecvKbps = (bw['current_recv_kbps'] as num?)?.toDouble() ?? 0;
      peakSentKbps    = (bw['peak_sent_kbps'] as num?)?.toDouble() ?? 0;
      peakRecvKbps    = (bw['peak_recv_kbps'] as num?)?.toDouble() ?? 0;
      isConnected = true;
      lastRefresh = DateTime.now();
      _ensureWsConnected();
      _startAutoRefresh();
    } catch (e) {
      isConnected = false;
      errorMsg = e.toString().replaceFirst('Exception: ', '');
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  Future<void> refreshConnections() async {
    try {
      connections = await _api.getConnections();
      notifyListeners();
    } catch (_) {}
  }

  Future<IPInvestigation?> investigateIP(String ip) async {
    try {
      return await _api.investigateIP(ip);
    } catch (e) {
      throw Exception(e.toString().replaceFirst('Exception: ', ''));
    }
  }

  // ── Auto-refresh every 5 s ───────────────────────────────────────────────
  void _startAutoRefresh() {
    _refreshTimer?.cancel();
    _refreshTimer = Timer.periodic(const Duration(seconds: 5), (_) => refresh());
  }

  // ── WebSocket ────────────────────────────────────────────────────────────
  void _ensureWsConnected() {
    if (_ws != null) return;
    try {
      final wsUrl = '${_serverUrl.replaceFirst(RegExp(r'^http'), 'ws')}/ws';
      _ws    = WebSocketChannel.connect(Uri.parse(wsUrl));
      _wsSub = _ws!.stream.listen(
        _onWsMessage,
        onError: (_) => _disconnectWs(),
        onDone:  () => _disconnectWs(),
      );
    } catch (_) {}
  }

  void _onWsMessage(dynamic raw) {
    try {
      final msg = json.decode(raw as String) as Map<String, dynamic>;
      final type = msg['type'] as String?;
      final data = msg['data'] as Map<String, dynamic>?;
      if (data == null) return;

      switch (type) {
        case 'alert':
          final alert = Alert.fromJson(data['alert'] as Map<String, dynamic>);
          if (!alerts.any((a) => a.id == alert.id)) {
            alerts = [alert, ...alerts];
            notifyListeners();
          }
        case 'device_update':
          final updated = Device.fromJson(data['device'] as Map<String, dynamic>);
          devices = devices.map((d) => d.id == updated.id ? updated : d).toList();
          notifyListeners();
        case 'device_added':
          final added = Device.fromJson(data['device'] as Map<String, dynamic>);
          if (!devices.any((d) => d.id == added.id)) {
            devices = [...devices, added];
            notifyListeners();
          }
      }
    } catch (_) {}
  }

  void _disconnectWs() {
    _wsSub?.cancel();
    _ws?.sink.close();
    _ws = null;
  }

  @override
  void dispose() {
    _disconnectWs();
    _refreshTimer?.cancel();
    super.dispose();
  }
}
