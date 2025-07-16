import 'package:flutter/material.dart';
import '../models/profile.dart';
import '../services/profile_service.dart';
import 'edit_profile_screen.dart';
import 'change_password_screen.dart';
import 'delete_account_screen.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardColor = Theme.of(context).cardColor;
    final textColor = Theme.of(context).textTheme.bodyLarge?.color ?? (isDark ? Colors.white : Colors.black);
    final labelColor = isDark ? Colors.grey[300] : Colors.grey[800];
    final accentColor = isDark ? Colors.teal[200] : Colors.teal;

    // Replace with your actual user data
    final user = {
      'username': 'adeoye',
      'email': 'adeoyeayan@gmail.com',
      'memberSince': 'Wed, 11 Jun 2025 15:22:36',
    };

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Center(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Card(
              color: isDark ? const Color(0xFF181A20) : Colors.white,
              elevation: 8,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Gradient header
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(vertical: 32),
                    decoration: const BoxDecoration(
                      borderRadius: BorderRadius.only(
                        topLeft: Radius.circular(24),
                        topRight: Radius.circular(24),
                      ),
                      gradient: LinearGradient(
                        colors: [Color(0xFF43e97b), Color(0xFF38f9d7)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                    ),
                    child: Column(
                      children: const [
                        Icon(Icons.account_circle, size: 64, color: Colors.white),
                        SizedBox(height: 12),
                        Text(
                          'adeoye',
                          style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.white),
                        ),
                        SizedBox(height: 6),
                        Text(
                          'Manage Your Personal Details and Account Settings',
                          style: TextStyle(fontSize: 14, color: Colors.white70),
                        ),
                      ],
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 8),
                        _profileInfoRow('Username', user['username']!, textColor, labelColor),
                        const SizedBox(height: 8),
                        _profileInfoRow('Email', user['email']!, textColor, labelColor),
                        const SizedBox(height: 8),
                        _profileInfoRow('Member Since', user['memberSince']!, textColor, labelColor),
                        const SizedBox(height: 20),
                        Divider(color: accentColor, thickness: 1.2),
                        const SizedBox(height: 10),
                        Center(
                          child: Text('Account Actions', style: TextStyle(color: accentColor, fontWeight: FontWeight.bold, fontSize: 18)),
                        ),
                        const SizedBox(height: 16),
                        _actionButton(context, 'Edit Profile', Icons.edit, Colors.blue, () {
                          Navigator.push(context, MaterialPageRoute(builder: (_) => EditProfileScreen(
                            profile: Profile(
                              id: 1,
                              username: user['username']!,
                              email: user['email']!,
                              createdAt: user['memberSince']!,
                            ),
                          )));
                        }),
                        const SizedBox(height: 12),
                        _actionButton(context, 'Change Password', Icons.vpn_key, Colors.grey, () {
                          Navigator.push(context, MaterialPageRoute(builder: (_) => ChangePasswordScreen()));
                        }),
                        const SizedBox(height: 12),
                        _actionButton(context, 'Delete Account', Icons.delete, Colors.red, () {
                          Navigator.push(context, MaterialPageRoute(builder: (_) => DeleteAccountScreen()));
                        }),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _profileInfoRow(String label, String value, Color valueColor, Color? labelColor) {
    return Row(
      children: [
        Text('$label:', style: TextStyle(fontWeight: FontWeight.bold, color: labelColor)),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            value,
            style: TextStyle(color: valueColor),
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }

  Widget _actionButton(BuildContext context, String text, IconData icon, Color color, VoidCallback onTap) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        icon: Icon(icon, color: Colors.white),
        label: Text(text, style: const TextStyle(color: Colors.white)),
        style: ElevatedButton.styleFrom(
          backgroundColor: color,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
          padding: const EdgeInsets.symmetric(vertical: 16),
        ),
        onPressed: onTap,
      ),
    );
  }
} 