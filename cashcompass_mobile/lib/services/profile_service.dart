import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/profile.dart';
import 'package:flutter/material.dart';

class ProfileService {
  static const _baseUrl = 'http://10.0.2.2:5000/api/profile';
  static final _storage = FlutterSecureStorage();

  static Future<Profile> fetchProfile(BuildContext context) async {
    final token = await _storage.read(key: 'jwt_token');
    final response = await http.get(
      Uri.parse(_baseUrl),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body)['profile'];
      return Profile.fromJson(data);
    } else if (response.statusCode == 401) {
      await _storage.delete(key: 'jwt_token');
      Navigator.of(context).pushReplacementNamed('/login');
      throw Exception('Session expired. Please log in again.');
    } else {
      throw Exception('Failed to load profile');
    }
  }

  static Future<void> updateProfile(BuildContext context, Map<String, dynamic> profileData) async {
    final token = await _storage.read(key: 'jwt_token');
    final response = await http.put(
      Uri.parse(_baseUrl),
      headers: {'Authorization': 'Bearer $token', 'Content-Type': 'application/json'},
      body: jsonEncode(profileData),
    );
    if (response.statusCode == 200) {
      return;
    } else if (response.statusCode == 401) {
      await _storage.delete(key: 'jwt_token');
      Navigator.of(context).pushReplacementNamed('/login');
      throw Exception('Session expired. Please log in again.');
    } else {
      throw Exception('Failed to update profile');
    }
  }

  static Future<void> changePassword(BuildContext context, String currentPassword, String newPassword) async {
    final token = await _storage.read(key: 'jwt_token');
    final response = await http.post(
      Uri.parse('http://10.0.2.2:5000/api/change_password'),
      headers: {'Authorization': 'Bearer $token', 'Content-Type': 'application/json'},
      body: jsonEncode({
        'current_password': currentPassword,
        'new_password': newPassword,
      }),
    );
    if (response.statusCode == 200) {
      return;
    } else if (response.statusCode == 401) {
      await _storage.delete(key: 'jwt_token');
      Navigator.of(context).pushReplacementNamed('/login');
      throw Exception('Session expired. Please log in again.');
    } else {
      final msg = jsonDecode(response.body)['msg'] ?? 'Failed to change password';
      throw Exception(msg);
    }
  }

  static Future<void> deleteAccount(BuildContext context, String password) async {
    final token = await _storage.read(key: 'jwt_token');
    final response = await http.post(
      Uri.parse('http://10.0.2.2:5000/api/delete_account'),
      headers: {'Authorization': 'Bearer $token', 'Content-Type': 'application/json'},
      body: jsonEncode({'password': password}),
    );
    if (response.statusCode == 200) {
      await _storage.delete(key: 'jwt_token');
      Navigator.of(context).pushReplacementNamed('/login');
      return;
    } else if (response.statusCode == 401) {
      await _storage.delete(key: 'jwt_token');
      Navigator.of(context).pushReplacementNamed('/login');
      throw Exception('Session expired. Please log in again.');
    } else {
      final msg = jsonDecode(response.body)['msg'] ?? 'Failed to delete account';
      throw Exception(msg);
    }
  }
} 