import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class DashboardService {
  static const _baseUrl = 'http://10.0.2.2:5000/api';
  static final _storage = FlutterSecureStorage();

  static Future<String?> getToken() async {
    return await _storage.read(key: 'jwt_token');
  }

  static Future<Map<String, dynamic>?> fetchDashboardData({String? month}) async {
    final token = await getToken();
    print('DASHBOARD TOKEN: $token');
    if (token == null) return null;
    final uri = Uri.parse('$_baseUrl/dashboard${month != null ? '?month=$month' : ''}');
    final response = await http.get(
      uri,
      headers: {'Authorization': 'Bearer $token'},
    );
    print('DASHBOARD RESPONSE: \\${response.statusCode} ${response.body}');
    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
    return null;
  }

  static Future<Map<String, dynamic>?> fetchFinancialHealthData() async {
    final token = await getToken();
    if (token == null) return null;
    final uri = Uri.parse('$_baseUrl/financial_health');
    final response = await http.get(
      uri,
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    }
    return null;
  }
} 