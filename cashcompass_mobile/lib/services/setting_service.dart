import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/setting.dart';
import 'package:flutter/material.dart';

class SettingService {
  static const _baseUrl = 'http://10.0.2.2:5000/api/settings';
  static final _storage = FlutterSecureStorage();

  static Future<List<Setting>> fetchSettings(BuildContext context) async {
    final token = await _storage.read(key: 'jwt_token');
    final response = await http.get(
      Uri.parse(_baseUrl),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode == 200) {
      final List data = jsonDecode(response.body);
      return data.map((e) => Setting.fromJson(e)).toList();
    } else if (response.statusCode == 401) {
      await _storage.delete(key: 'jwt');
      Navigator.of(context).pushReplacementNamed('/login');
      throw Exception('Session expired. Please log in again.');
    } else {
      throw Exception('Failed to load settings');
    }
  }

  static Future<void> updateSettings(BuildContext context, Map<String, dynamic> settingsData) async {
    final token = await _storage.read(key: 'jwt_token');
    final response = await http.put(
      Uri.parse(_baseUrl),
      headers: {'Authorization': 'Bearer $token', 'Content-Type': 'application/json'},
      body: jsonEncode(settingsData),
    );
    if (response.statusCode == 200) {
      return;
    } else if (response.statusCode == 401) {
      await _storage.delete(key: 'jwt');
      Navigator.of(context).pushReplacementNamed('/login');
      throw Exception('Session expired. Please log in again.');
    } else {
      throw Exception('Failed to update settings');
    }
  }
} 