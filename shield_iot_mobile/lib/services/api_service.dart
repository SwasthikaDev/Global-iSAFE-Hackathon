import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/models.dart';

class ApiService {
  final String baseUrl;

  ApiService(this.baseUrl);

  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  Future<T> _get<T>(String path, T Function(dynamic) parse) async {
    final res = await http.get(_uri(path)).timeout(const Duration(seconds: 10));
    if (res.statusCode == 200) {
      return parse(json.decode(res.body));
    }
    throw Exception('HTTP ${res.statusCode} on $path');
  }

  Future<NetworkStatus> getNetworkStatus() =>
      _get('/api/network/status', (j) => NetworkStatus.fromJson(j));

  Future<List<Device>> getDevices() => _get(
      '/api/devices/',
      (j) => (j['devices'] as List).map((d) => Device.fromJson(d)).toList());

  Future<List<Alert>> getAlerts({int limit = 50}) => _get(
      '/api/alerts/?limit=$limit',
      (j) => (j['alerts'] as List).map((a) => Alert.fromJson(a)).toList());

  Future<SecurityScore> getSecurityScore() =>
      _get('/api/network/security-score', (j) => SecurityScore.fromJson(j));

  Future<List<LiveConnection>> getConnections() => _get(
      '/api/connections/',
      (j) => (j['connections'] as List)
          .map((c) => LiveConnection.fromJson(c))
          .toList());

  Future<Map<String, dynamic>> getBandwidth() =>
      _get('/api/network/bandwidth', (j) => j as Map<String, dynamic>);

  Future<IPInvestigation> investigateIP(String ip) =>
      _get('/api/investigate/$ip', (j) => IPInvestigation.fromJson(j));

  Future<Map<String, dynamic>> getDevicePorts(String deviceId) =>
      _get('/api/devices/$deviceId/ports', (j) => j as Map<String, dynamic>);
}
