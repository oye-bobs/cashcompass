import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/ai_advisor.dart';

class AIAdvisorService {
  static const _baseUrl = 'http://10.0.2.2:5000/api/ai_advisor';
  static final _storage = FlutterSecureStorage();

  static Future<AIAdvisor> sendMessage(String message) async {
    final token = await _storage.read(key: 'jwt');
    final response = await http.post(
      Uri.parse(_baseUrl),
      headers: {'Authorization': 'Bearer $token', 'Content-Type': 'application/json'},
      body: jsonEncode({'message': message}),
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return AIAdvisor.fromJson(data);
    } else {
      throw Exception('Failed to get AI response');
    }
  }
} 