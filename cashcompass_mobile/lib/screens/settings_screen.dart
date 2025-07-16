import 'package:flutter/material.dart';
import '../services/setting_service.dart';
import '../models/setting.dart';
import '../models/profile.dart';
import '../services/profile_service.dart';
import '../main.dart'; // Import the global darkModeNotifier

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({Key? key}) : super(key: key);

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _showCurrentPassword = false;
  bool _showNewPassword = false;
  bool _showConfirmPassword = false;
  final _formKey = GlobalKey<FormState>();
  final _currentPasswordController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  bool _loading = true;
  String? _error;
  bool _settingsLoading = true;
  String? _settingsError;
  Profile? _profile;
  bool _darkMode = false;

  @override
  void initState() {
    super.initState();
    _fetchProfileAndSettings();
  }

  Future<void> _fetchProfileAndSettings() async {
    setState(() {
      _loading = true;
      _settingsLoading = true;
      _error = null;
      _settingsError = null;
    });
    try {
      final profile = await ProfileService.fetchProfile(context);
      setState(() {
        _profile = profile;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to load profile.';
        _loading = false;
      });
    }
    try {
      final settings = await SettingService.fetchSettings(context);
      final darkSetting = settings.firstWhere(
        (s) => s.key == 'dark_mode',
        orElse: () => Setting(key: 'dark_mode', value: 'false'),
      );
      _darkMode = darkSetting.value == 'true';
      darkModeNotifier.value = _darkMode;
      setState(() {
        _settingsLoading = false;
      });
    } catch (e) {
      setState(() {
        _settingsError = 'Failed to load settings.';
        _settingsLoading = false;
      });
    }
  }

  Future<void> _toggleDarkMode(bool value) async {
    setState(() {
      _darkMode = value;
    });
    darkModeNotifier.value = value;
    try {
      await SettingService.updateSettings(context, {'dark_mode': value.toString()});
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to update dark mode setting.')),
      );
    }
  }

  @override
  void dispose() {
    _currentPasswordController.dispose();
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: darkModeNotifier.value ? Colors.grey[900] : Colors.grey[100],
      body: _loading || _settingsLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null || _settingsError != null
              ? Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Center(
                    child: Text(_error ?? _settingsError!, style: const TextStyle(color: Colors.red)),
                  ),
                )
              : SingleChildScrollView(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // Gradient header
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(vertical: 40),
                        decoration: const BoxDecoration(
                          gradient: LinearGradient(
                            colors: [Color(0xFF00B4D8), Color(0xFF48CAE4)],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                        ),
                        child: Column(
                          children: [
                            const Icon(Icons.settings, size: 60, color: Colors.white),
                            const SizedBox(height: 10),
                            const Text('Settings', style: TextStyle(fontSize: 28, color: Colors.white, fontWeight: FontWeight.bold)),
                          ],
                        ),
                      ),
                      const SizedBox(height: 24),
                      // User info card
                      Card(
                        margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                        elevation: 4,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        child: Padding(
                          padding: const EdgeInsets.all(20.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  const Icon(Icons.account_circle, size: 40, color: Colors.teal),
                                  const SizedBox(width: 16),
                                  Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(_profile?.username ?? '', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                                      const SizedBox(height: 4),
                                      Text(_profile?.email ?? '', style: const TextStyle(fontSize: 16, color: Colors.grey)),
                                    ],
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      // Dark mode toggle
                      Card(
                        margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                        elevation: 2,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        child: SwitchListTile(
                          title: const Text('Dark Mode'),
                          value: _darkMode,
                          onChanged: _toggleDarkMode,
                          secondary: const Icon(Icons.nightlight_round),
                        ),
                      ),
                      const SizedBox(height: 12),
                      // Creative: Notification toggle (placeholder)
                      Card(
                        margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                        elevation: 2,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Row(
                                children: const [
                                  Icon(Icons.notifications_active, color: Colors.teal),
                                  SizedBox(width: 8),
                                  Text('Notifications', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                                ],
                              ),
                              Switch(
                                value: true,
                                onChanged: (val) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text('Notifications setting coming soon!')),
                                  );
                                },
                                activeColor: Colors.teal,
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),
                      // Change password form
                      Card(
                        margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                        elevation: 2,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        child: Padding(
                          padding: const EdgeInsets.all(20.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('Change Password', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.blueAccent)),
                              const SizedBox(height: 12),
                              Form(
                                key: _formKey,
                                child: Column(
                                  children: [
                                    _passwordField(
                                      controller: _currentPasswordController,
                                      label: 'Current Password',
                                      show: _showCurrentPassword,
                                      toggle: () => setState(() => _showCurrentPassword = !_showCurrentPassword),
                                    ),
                                    const SizedBox(height: 12),
                                    _passwordField(
                                      controller: _newPasswordController,
                                      label: 'New Password',
                                      show: _showNewPassword,
                                      toggle: () => setState(() => _showNewPassword = !_showNewPassword),
                                    ),
                                    const SizedBox(height: 12),
                                    _passwordField(
                                      controller: _confirmPasswordController,
                                      label: 'Confirm New Password',
                                      show: _showConfirmPassword,
                                      toggle: () => setState(() => _showConfirmPassword = !_showConfirmPassword),
                                    ),
                                    const SizedBox(height: 20),
                                    ElevatedButton.icon(
                                      icon: const Icon(Icons.save),
                                      label: const Text('Save Changes', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: Colors.blueAccent,
                                        foregroundColor: Colors.white,
                                        minimumSize: const Size.fromHeight(48),
                                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
                                        elevation: 2,
                                      ),
                                      onPressed: () {
                                        ScaffoldMessenger.of(context).showSnackBar(
                                          const SnackBar(content: Text('Password change coming soon!')),
                                        );
                                      },
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),
                    ],
                  ),
                ),
    );
  }

  Widget _infoItem(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        Flexible(
          child: Text(value, style: const TextStyle(fontSize: 16, color: Colors.black87), textAlign: TextAlign.right, overflow: TextOverflow.ellipsis),
        ),
      ],
    );
  }

  Widget _passwordField({required TextEditingController controller, required String label, required bool show, required VoidCallback toggle}) {
    return TextFormField(
      controller: controller,
      obscureText: !show,
      decoration: InputDecoration(
        labelText: label,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        suffixIcon: IconButton(
          icon: Icon(show ? Icons.visibility : Icons.visibility_off),
          onPressed: toggle,
        ),
      ),
      validator: (value) {
        if (value == null || value.isEmpty) return 'Please enter $label.';
        return null;
      },
    );
  }
} 