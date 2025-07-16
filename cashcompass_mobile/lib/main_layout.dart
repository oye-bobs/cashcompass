import 'package:flutter/material.dart';
import 'sidebar.dart';

class AppScaffold extends StatefulWidget {
  final Widget child;
  final int currentIndex;
  final void Function(int) onBottomNavTap;
  final void Function(String) onSidebarNavigate;
  final String? title;
  final bool darkMode;
  final void Function(bool) onToggleDarkMode;
  const AppScaffold({
    required this.child,
    required this.currentIndex,
    required this.onBottomNavTap,
    required this.onSidebarNavigate,
    this.title,
    required this.darkMode,
    required this.onToggleDarkMode,
    Key? key,
  }) : super(key: key);

  @override
  State<AppScaffold> createState() => _AppScaffoldState();
}

class _AppScaffoldState extends State<AppScaffold> {
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: _scaffoldKey,
      drawer: Sidebar(
        onNavigate: widget.onSidebarNavigate,
        darkMode: widget.darkMode,
        onToggleDarkMode: widget.onToggleDarkMode,
      ),
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.menu),
          onPressed: () => _scaffoldKey.currentState?.openDrawer(),
        ),
        title: Text(widget.title ?? 'CashCompass'),
        backgroundColor: Colors.teal,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: widget.child,
      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        currentIndex: widget.currentIndex,
        onTap: widget.onBottomNavTap,
        selectedItemColor: Colors.teal,
        unselectedItemColor: Colors.grey,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: 'Dashboard'),
          BottomNavigationBarItem(icon: Icon(Icons.account_balance_wallet), label: 'Budget'),
          BottomNavigationBarItem(icon: Icon(Icons.money_off), label: 'Expenses'),
          BottomNavigationBarItem(icon: Icon(Icons.money), label: 'Income'),
        ],
      ),
    );
  }
} 