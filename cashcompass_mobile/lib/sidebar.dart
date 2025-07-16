import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';

class Sidebar extends StatelessWidget {
  final void Function(String route) onNavigate;
  final bool darkMode;
  final void Function(bool) onToggleDarkMode;
  const Sidebar({required this.onNavigate, required this.darkMode, required this.onToggleDarkMode, Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 240,
      color: darkMode ? const Color(0xFF263238) : const Color(0xFFe0f7fa),
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          DrawerHeader(
            decoration: BoxDecoration(
              color: darkMode ? Colors.teal[800] : Colors.teal,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                FaIcon(FontAwesomeIcons.compass, size: 40, color: Colors.white),
                SizedBox(height: 8),
                Text(
                  'CashCompass',
                  style: TextStyle(fontSize: 24, color: Colors.white, fontWeight: FontWeight.bold),
                ),
                Text(
                  'Your Financial Navigator',
                  style: TextStyle(fontSize: 14, color: Colors.white70),
                ),
              ],
            ),
          ),
          _SidebarItem(
            icon: FontAwesomeIcons.piggyBank,
            text: 'Savings',
            onTap: () => onNavigate('savings'),
            color: darkMode ? Colors.white : Colors.teal[900],
          ),
          _SidebarItem(
            icon: FontAwesomeIcons.handHoldingUsd,
            text: 'Debt',
            onTap: () => onNavigate('debt'),
            color: darkMode ? Colors.white : Colors.teal[900],
          ),
          _SidebarItem(
            icon: FontAwesomeIcons.brain,
            text: 'AI Financial Advisor',
            onTap: () => onNavigate('advisor'),
            color: darkMode ? Colors.white : Colors.teal[900],
          ),
          _SidebarItem(
            icon: FontAwesomeIcons.userCircle,
            text: 'Profile',
            onTap: () => onNavigate('profile'),
            color: darkMode ? Colors.white : Colors.teal[900],
          ),
          _SidebarItem(
            icon: FontAwesomeIcons.cog,
            text: 'Settings',
            onTap: () => onNavigate('settings'),
            color: darkMode ? Colors.white : Colors.teal[900],
          ),
          SwitchListTile(
            secondary: Icon(Icons.dark_mode, color: darkMode ? Colors.white : Colors.teal),
            title: Text('Dark Mode', style: TextStyle(color: darkMode ? Colors.white : Color(0xFF00695c), fontWeight: FontWeight.w600)),
            value: darkMode,
            onChanged: onToggleDarkMode,
          ),
          const Divider(),
          _SidebarItem(
            icon: FontAwesomeIcons.signOutAlt,
            text: 'Logout',
            onTap: () => onNavigate('logout'),
            color: Colors.red,
          ),
        ],
      ),
    );
  }
}

class _SidebarItem extends StatelessWidget {
  final IconData icon;
  final String text;
  final VoidCallback onTap;
  final Color? color;

  const _SidebarItem({
    required this.icon,
    required this.text,
    required this.onTap,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: FaIcon(icon, color: color ?? Colors.teal),
      title: Text(
        text,
        style: TextStyle(
          color: color ?? Colors.teal[900],
          fontWeight: FontWeight.w600,
        ),
      ),
      onTap: onTap,
    );
  }
} 