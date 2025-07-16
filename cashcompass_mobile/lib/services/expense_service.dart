import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/expense.dart';
import 'package:flutter/material.dart';

class ExpenseService {
  static const _baseUrl = 'http://10.0.2.2:5000/api/expenses';
  static final _storage = FlutterSecureStorage();

  static Future<List<Expense>> fetchExpenses(BuildContext context, {int? month, int? year}) async {
    final token = await _storage.read(key: 'jwt_token');
    String url = _baseUrl;
    if (month != null || year != null) {
      List<String> params = [];
      if (month != null) params.add('month=${month.toString().padLeft(2, '0')}');
      if (year != null) params.add('year=$year');
      url += '?${params.join('&')}';
    }
    final response = await http.get(
      Uri.parse(url),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (response.statusCode == 200) {
      final List data = jsonDecode(response.body)['expenses'];
      return data.map((e) => Expense.fromJson(e)).toList();
    } else if (response.statusCode == 401) {
      await _storage.delete(key: 'jwt_token');
      Navigator.of(context).pushReplacementNamed('/login');
      throw Exception('Session expired. Please log in again.');
    } else {
      throw Exception('Failed to load expenses');
    }
  }

  static Future<void> addExpense(BuildContext context, double amount, String category, String date) async {
    final token = await _storage.read(key: 'jwt_token');
    final response = await http.post(
      Uri.parse(_baseUrl),
      headers: {'Authorization': 'Bearer $token', 'Content-Type': 'application/json'},
      body: jsonEncode({'amount': amount, 'category': category, 'date': date}),
    );
    if (response.statusCode == 201) {
      return;
    } else if (response.statusCode == 401) {
      await _storage.delete(key: 'jwt_token');
      Navigator.of(context).pushReplacementNamed('/login');
      throw Exception('Session expired. Please log in again.');
    } else {
      throw Exception('Failed to add expense');
    }
  }

  static Future<void> updateExpense(BuildContext context, int id, double amount, String category, String date) async {
    final token = await _storage.read(key: 'jwt_token');
    final response = await http.put(
      Uri.parse('$_baseUrl/$id'),
      headers: {'Authorization': 'Bearer $token', 'Content-Type': 'application/json'},
      body: jsonEncode({'amount': amount, 'category': category, 'date': date}),
    );
    if (response.statusCode == 200) {
      return;
    } else if (response.statusCode == 401) {
      await _storage.delete(key: 'jwt_token');
      Navigator.of(context).pushReplacementNamed('/login');
      throw Exception('Session expired. Please log in again.');
    } else {
      throw Exception('Failed to update expense');
    }
  }

  static Future<void> deleteExpense(BuildContext context, int id) async {
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
      throw Exception('Failed to delete expense');
    }
  }
} 