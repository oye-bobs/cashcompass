import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/debt.dart';
import 'package:flutter/material.dart';

class DebtService {
  static const _baseUrl = 'http://10.0.2.2:5000/api/debt';
  static final _storage = FlutterSecureStorage();

  static Future<List<Debt>> fetchDebts(BuildContext context) async {
    final token = await _storage.read(key: 'jwt_token');
    final response = await http.get(
      Uri.parse(_baseUrl),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode == 200) {
      final List data = jsonDecode(response.body)['debt'];
      return data.map((e) => Debt.fromJson(e)).toList();
    } else if (response.statusCode == 401) {
      await _storage.delete(key: 'jwt');
      Navigator.of(context).pushReplacementNamed('/login');
      throw Exception('Session expired. Please log in again.');
    } else {
      throw Exception('Failed to load debts');
    }
  }

  static Future<void> addDebt(BuildContext context, double currentBalance, String debtName, String debtType, String dueDate) async {
    final token = await _storage.read(key: 'jwt_token');
    final response = await http.post(
      Uri.parse(_baseUrl),
      headers: {'Authorization': 'Bearer $token', 'Content-Type': 'application/json'},
      body: jsonEncode({'current_balance': currentBalance, 'debt_name': debtName, 'debt_type': debtType, 'due_date': dueDate}),
    );
    if (response.statusCode == 201) {
      return;
    } else if (response.statusCode == 401) {
      await _storage.delete(key: 'jwt');
      Navigator.of(context).pushReplacementNamed('/login');
      throw Exception('Session expired. Please log in again.');
    } else {
      throw Exception('Failed to add debt');
    }
  }

  static Future<void> updateDebt(BuildContext context, int id, double currentBalance, String debtName, String debtType, String dueDate) async {
    final token = await _storage.read(key: 'jwt_token');
    final response = await http.put(
      Uri.parse('$_baseUrl/$id'),
      headers: {'Authorization': 'Bearer $token', 'Content-Type': 'application/json'},
      body: jsonEncode({'current_balance': currentBalance, 'debt_name': debtName, 'debt_type': debtType, 'due_date': dueDate}),
    );
    if (response.statusCode == 200) {
      return;
    } else if (response.statusCode == 401) {
      await _storage.delete(key: 'jwt');
      Navigator.of(context).pushReplacementNamed('/login');
      throw Exception('Session expired. Please log in again.');
    } else {
      throw Exception('Failed to update debt');
    }
  }

  static Future<void> deleteDebt(BuildContext context, int id) async {
    final token = await _storage.read(key: 'jwt_token');
    final response = await http.delete(
      Uri.parse('$_baseUrl/$id'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode == 200) {
      return;
    } else if (response.statusCode == 401) {
      await _storage.delete(key: 'jwt');
      Navigator.of(context).pushReplacementNamed('/login');
      throw Exception('Session expired. Please log in again.');
    } else {
      throw Exception('Failed to delete debt');
    }
  }
} 