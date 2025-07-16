import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'screens/dashboard_screen.dart';
import 'screens/settings_screen.dart';

// Global dark mode notifier
final ValueNotifier<bool> darkModeNotifier = ValueNotifier(false);

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<bool>(
      valueListenable: darkModeNotifier,
      builder: (context, isDark, _) {
        return MaterialApp(
          title: 'CashCompass',
          theme: isDark ? ThemeData.dark() : ThemeData.light().copyWith(
            scaffoldBackgroundColor: const Color(0xFFe0f7fa),
            inputDecorationTheme: InputDecorationTheme(
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(30),
              ),
            ),
            elevatedButtonTheme: ElevatedButtonThemeData(
              style: ElevatedButton.styleFrom(
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(30),
                ),
                padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 32),
                backgroundColor: Colors.teal,
              ),
            ),
          ),
          home: LoginScreen(),
        );
      },
    );
  }
}

class LoginScreen extends StatefulWidget {
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _storage = const FlutterSecureStorage();
  String _error = '';
  bool _loading = false;

  Future<void> _login() async {
    setState(() => _loading = true);
    final url = Uri.parse('http://10.0.2.2:5000/api/login');
    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'username': _usernameController.text,
        'password': _passwordController.text,
      }),
    );
    setState(() => _loading = false);
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      await _storage.write(key: 'jwt_token', value: data['access_token']);
      setState(() => _error = '');
      // Navigate to dashboard
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => DashboardScreen(
          darkMode: darkModeNotifier.value,
          onToggleDarkMode: (val) => darkModeNotifier.value = val,
        )),
      );
    } else {
      setState(() => _error = 'Login failed: \n${jsonDecode(response.body)['msg']}');
    }
  }

  void _goToRegister() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => RegisterScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardColor = isDark ? const Color(0xFF23272F) : Colors.white;
    final textColor = isDark ? Colors.white : Colors.teal[900]!;
    final accentColor = Colors.teal;
    final linkColor = isDark ? Colors.teal[200]! : Colors.teal;
    final copyrightColor = isDark ? Colors.white : Colors.teal;
    final inputFill = isDark ? Colors.grey[900] : Colors.white;
    final inputTextColor = isDark ? Colors.white : Colors.black87;
    final inputIconColor = isDark ? Colors.teal[200]! : Colors.teal;
    final borderColor = isDark ? Colors.teal[700]! : Colors.teal[200]!;
    return Stack(
      children: [
        Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [Color(0xFFe0f7fa), Color(0xFF80cbc4)],
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
            ),
          ),
        ),
        Scaffold(
          backgroundColor: Colors.transparent,
          body: Center(
            child: SingleChildScrollView(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Card(
                  color: cardColor,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(24),
                  ),
                  elevation: 12,
                  shadowColor: Colors.teal.withOpacity(0.2),
                  child: Padding(
                    padding: const EdgeInsets.all(28),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        FaIcon(FontAwesomeIcons.compass, size: 64, color: accentColor),
                        const SizedBox(height: 16),
                        Text(
                          'CashCompass',
                          style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: accentColor),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Your Financial Navigator',
                          style: TextStyle(fontSize: 16, color: accentColor, fontWeight: FontWeight.w500),
                        ),
                        const SizedBox(height: 32),
                        TextField(
                          controller: _usernameController,
                          style: TextStyle(color: inputTextColor),
                          decoration: InputDecoration(
                            labelText: 'Username',
                            labelStyle: TextStyle(color: textColor.withOpacity(0.8)),
                            prefixIcon: Icon(Icons.person, color: inputIconColor),
                            filled: true,
                            fillColor: inputFill,
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: BorderSide(color: borderColor),
                            ),
                            enabledBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: BorderSide(color: borderColor),
                            ),
                            focusedBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: BorderSide(color: accentColor, width: 2),
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        TextField(
                          controller: _passwordController,
                          style: TextStyle(color: inputTextColor),
                          decoration: InputDecoration(
                            labelText: 'Password',
                            labelStyle: TextStyle(color: textColor.withOpacity(0.8)),
                            prefixIcon: Icon(Icons.lock, color: inputIconColor),
                            filled: true,
                            fillColor: inputFill,
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: BorderSide(color: borderColor),
                            ),
                            enabledBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: BorderSide(color: borderColor),
                            ),
                            focusedBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: BorderSide(color: accentColor, width: 2),
                            ),
                          ),
                          obscureText: true,
                        ),
                        const SizedBox(height: 24),
                        _loading
                            ? const CircularProgressIndicator()
                            : SizedBox(
                                width: double.infinity,
                                child: ElevatedButton(
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: accentColor,
                                    foregroundColor: Colors.white,
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(30),
                                    ),
                                    padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 32),
                                  ),
                                  onPressed: _login,
                                  child: const Text('Log In', style: TextStyle(fontSize: 18)),
                                ),
                              ),
                        if (_error.isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 16),
                            child: Text(_error, style: const TextStyle(color: Colors.red)),
                          ),
                        const SizedBox(height: 16),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text("New to CashCompass? ", style: TextStyle(color: textColor)),
                            GestureDetector(
                              onTap: _goToRegister,
                              child: Text(
                                'Join now',
                                style: TextStyle(
                                  color: linkColor,
                                  fontWeight: FontWeight.bold,
                                  decoration: TextDecoration.underline,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '© 2024 CashCompass',
                          style: TextStyle(fontSize: 12, color: copyrightColor),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
        if (_loading)
          Container(
            color: Colors.black.withOpacity(0.1),
            child: const Center(child: CircularProgressIndicator()),
          ),
      ],
    );
  }
}

class RegisterScreen extends StatefulWidget {
  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  String _error = '';
  bool _loading = false;

  Future<void> _register() async {
    if (_passwordController.text != _confirmPasswordController.text) {
      setState(() => _error = 'Passwords do not match');
      return;
    }

    setState(() => _loading = true);
    final url = Uri.parse('http://10.0.2.2:5000/api/register');
    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'username': _usernameController.text,
        'password': _passwordController.text,
      }),
    );
    setState(() => _loading = false);
    if (response.statusCode == 200) {
      setState(() => _error = '');
      Navigator.pop(context); // Go back to login
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Registration successful! Please log in.')),
      );
    } else {
      setState(() => _error = 'Registration failed: \n${jsonDecode(response.body)['msg']}');
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardColor = isDark ? const Color(0xFF23272F) : Colors.white;
    final textColor = isDark ? Colors.white : Colors.teal[900]!;
    final accentColor = Colors.teal;
    final linkColor = isDark ? Colors.teal[200]! : Colors.teal;
    final inputFill = isDark ? Colors.grey[900] : Colors.white;
    final inputTextColor = isDark ? Colors.white : Colors.black87;
    final inputIconColor = isDark ? Colors.teal[200]! : Colors.teal;
    final borderColor = isDark ? Colors.teal[700]! : Colors.teal[200]!;
    final copyrightColor = isDark ? Colors.white : Colors.teal;
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: Stack(
        children: [
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFFe0f7fa), Color(0xFF80cbc4)],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              ),
            ),
          ),
          Center(
            child: SingleChildScrollView(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Card(
                  color: cardColor,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(24),
                  ),
                  elevation: 12,
                  shadowColor: Colors.teal.withOpacity(0.2),
                  child: Padding(
                    padding: const EdgeInsets.all(28),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        FaIcon(FontAwesomeIcons.compass, size: 64, color: accentColor),
                        const SizedBox(height: 16),
                        Text(
                          'Join CashCompass',
                          style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: accentColor),
                        ),
                        const SizedBox(height: 32),
                        TextField(
                          controller: _usernameController,
                          style: TextStyle(color: inputTextColor),
                          decoration: InputDecoration(
                            labelText: 'Username',
                            labelStyle: TextStyle(color: textColor.withOpacity(0.8)),
                            prefixIcon: Icon(Icons.person, color: inputIconColor),
                            filled: true,
                            fillColor: inputFill,
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: BorderSide(color: borderColor),
                            ),
                            enabledBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: BorderSide(color: borderColor),
                            ),
                            focusedBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: BorderSide(color: accentColor, width: 2),
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        TextField(
                          controller: _passwordController,
                          style: TextStyle(color: inputTextColor),
                          decoration: InputDecoration(
                            labelText: 'Password',
                            labelStyle: TextStyle(color: textColor.withOpacity(0.8)),
                            prefixIcon: Icon(Icons.lock, color: inputIconColor),
                            filled: true,
                            fillColor: inputFill,
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: BorderSide(color: borderColor),
                            ),
                            enabledBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: BorderSide(color: borderColor),
                            ),
                            focusedBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: BorderSide(color: accentColor, width: 2),
                            ),
                          ),
                          obscureText: true,
                        ),
                        const SizedBox(height: 16),
                        TextField(
                          controller: _confirmPasswordController,
                          style: TextStyle(color: inputTextColor),
                          decoration: InputDecoration(
                            labelText: 'Confirm Password',
                            labelStyle: TextStyle(color: textColor.withOpacity(0.8)),
                            prefixIcon: Icon(Icons.lock, color: inputIconColor),
                            filled: true,
                            fillColor: inputFill,
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: BorderSide(color: borderColor),
                            ),
                            enabledBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: BorderSide(color: borderColor),
                            ),
                            focusedBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: BorderSide(color: accentColor, width: 2),
                            ),
                          ),
                          obscureText: true,
                        ),
                        const SizedBox(height: 24),
                        _loading
                            ? const CircularProgressIndicator()
                            : SizedBox(
                                width: double.infinity,
                                child: ElevatedButton(
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: accentColor,
                                    foregroundColor: Colors.white,
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(30),
                                    ),
                                    padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 32),
                                  ),
                                  onPressed: _register,
                                  child: const Text('Register', style: TextStyle(fontSize: 18)),
                                ),
                              ),
                        if (_error.isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 16),
                            child: Text(_error, style: const TextStyle(color: Colors.red)),
                          ),
                        const SizedBox(height: 16),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text("Already have an account? ", style: TextStyle(color: textColor)),
                            GestureDetector(
                              onTap: () => Navigator.pop(context),
                              child: Text(
                                'Log in',
                                style: TextStyle(
                                  color: linkColor,
                                  fontWeight: FontWeight.bold,
                                  decoration: TextDecoration.underline,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '© 2024 CashCompass',
                          style: TextStyle(fontSize: 12, color: copyrightColor),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
          if (_loading)
            Container(
              color: Colors.black.withOpacity(0.1),
              child: const Center(child: CircularProgressIndicator()),
            ),
        ],
      ),
    );
  }
}