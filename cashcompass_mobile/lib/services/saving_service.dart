import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/saving.dart';
import 'package:flutter/material.dart';

class SavingService {
  static const _baseUrl = 'http://10.0.2.2:5000/api/savings';
  static final _storage = FlutterSecureStorage();

  static Future<List<Saving>> fetchSavings(BuildContext context) async {
    final token = await _storage.read(key: 'jwt_token');
    final response = await http.get(
      Uri.parse(_baseUrl),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode == 200) {
      final List data = jsonDecode(response.body)['savings'];
      return data.map((e) => Saving.fromJson(e)).toList();
    } else if (response.statusCode == 401) {
      await _storage.delete(key: 'jwt_token');
      Navigator.of(context).pushReplacementNamed('/login');
      throw Exception('Session expired. Please log in again.');
    } else {
      throw Exception('Failed to load savings');
    }
  }

  static Future<void> addSaving(BuildContext context, double amount, String goal, double targetAmount) async {
    final token = await _storage.read(key: 'jwt_token');
    final response = await http.post(
      Uri.parse(_baseUrl),
      headers: {'Authorization': 'Bearer $token', 'Content-Type': 'application/json'},
      body: jsonEncode({'amount': amount, 'goal': goal, 'target_amount': targetAmount}),
    );
    if (response.statusCode == 201) {
      return;
    } else if (response.statusCode == 401) {
      await _storage.delete(key: 'jwt_token');
      Navigator.of(context).pushReplacementNamed('/login');
      throw Exception('Session expired. Please log in again.');
    } else {
      throw Exception('Failed to add saving');
    }
  }

  static Future<void> updateSaving(BuildContext context, int id, double amount, String goal, double targetAmount) async {
    final token = await _storage.read(key: 'jwt_token');
    final response = await http.put(
      Uri.parse('$_baseUrl/$id'),
      headers: {'Authorization': 'Bearer $token', 'Content-Type': 'application/json'},
      body: jsonEncode({'amount': amount, 'goal': goal, 'target_amount': targetAmount}),
    );
    if (response.statusCode == 200) {
      return;
    } else if (response.statusCode == 401) {
      await _storage.delete(key: 'jwt_token');
      Navigator.of(context).pushReplacementNamed('/login');
      throw Exception('Session expired. Please log in again.');
    } else {
      throw Exception('Failed to update saving');
    }
  }

  static Future<void> deleteSaving(BuildContext context, int id) async {
    final token = await _storage.read(key: 'jwt_token');
    final response = await http.delete(
      Uri.parse('$_baseUrl/$id'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode == 200) {
      return;
    } else if (response.statusCode == 401) {
      await _storage.delete(key: 'jwt_token');
      Navigator.of(context).pushReplacementNamed('/login');
      throw Exception('Session expired. Please log in again.');
    } else {
      throw Exception('Failed to delete saving');
    }
  }
} 