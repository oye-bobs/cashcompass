import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../main_layout.dart';
import 'settings_screen.dart';
import 'profile_screen.dart';
import 'budget_screen.dart';
import 'expenses_screen.dart';
import 'income_screen.dart';
import 'savings_screen.dart';
import 'debt_screen.dart';
import 'ai_advisor_screen.dart';
import 'enhanced_dashboard_content.dart';
import '../services/dashboard_service.dart';
import 'financial_health_overview_screen.dart';
import '../main.dart'; // For LoginScreen

class DashboardScreen extends StatefulWidget {
  final bool darkMode;
  final void Function(bool) onToggleDarkMode;
  const DashboardScreen({super.key, required this.darkMode, required this.onToggleDarkMode});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _selectedIndex = 0;
  static const List<String> _bottomRoutes = [
    'dashboard',
    'budget',
    'expenses',
    'income',
  ];
  static const Map<String, String> _titles = {
    'dashboard': 'CashCompass Dashboard',
    'budget': 'Budget',
    'expenses': 'Expenses',
    'income': 'Income',
    'savings': 'Savings',
    'debt': 'Debt',
    'advisor': 'AI Financial Advisor',
    'profile': 'Profile',
    'settings': 'Settings',
  };

  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  Widget _getScreen(String route) {
    switch (route) {
      case 'dashboard':
        return DashboardHome();
      case 'budget':
        return const BudgetScreen();
      case 'expenses':
        return const ExpenseScreen();
      case 'income':
        return const IncomeScreen();
      case 'savings':
        return const SavingsScreen();
      case 'debt':
        return const DebtScreen();
      case 'advisor':
        return const AIAdvisorScreen();
      case 'profile':
        return const ProfileScreen();
      case 'settings':
        return const SettingsScreen();
      default:
        return DashboardHome();
    }
  }

  String _currentRoute = 'dashboard';

  void _onBottomNavTap(int index) {
    setState(() {
      _selectedIndex = index;
      _currentRoute = _bottomRoutes[index];
    });
  }

  void _onSidebarNavigate(String route) async {
    if (route == 'logout') {
      await _storage.delete(key: 'jwt_token');
      if (!mounted) return;
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (context) => LoginScreen()),
        (route) => false,
      );
      return;
    }
    setState(() {
      _currentRoute = route;
      final idx = _bottomRoutes.indexOf(route);
      if (idx != -1) {
        _selectedIndex = idx;
      }
    });
    Navigator.of(context).maybePop(); // Close drawer if open
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      child: _getScreen(_currentRoute),
      currentIndex: _selectedIndex,
      onBottomNavTap: _onBottomNavTap,
      onSidebarNavigate: _onSidebarNavigate,
      title: _titles[_currentRoute] ?? 'CashCompass',
      darkMode: widget.darkMode,
      onToggleDarkMode: widget.onToggleDarkMode,
    );
  }
}

class DashboardHome extends StatefulWidget {
  const DashboardHome({super.key});

  @override
  State<DashboardHome> createState() => _DashboardHomeState();
}

class _DashboardHomeState extends State<DashboardHome> {
  Map<String, dynamic>? _data;
  bool _loading = true;
  String? _error;
  List<String> _availableMonths = [];
  String _selectedMonth = '';

  @override
  void initState() {
    super.initState();
    _fetchDashboard();
  }

  Future<void> _fetchDashboard({String? month}) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await DashboardService.fetchDashboardData(month: month ?? _selectedMonth);
      if (data == null) {
        setState(() {
          _error = 'Failed to load dashboard data.';
          _loading = false;
        });
      } else {
        final months = List<String>.from(data['available_months'] ?? []);
        final selected = data['selected_month'] ?? (months.isNotEmpty ? months.last : '');
        setState(() {
          _data = data;
          _availableMonths = months;
          _selectedMonth = selected;
          _loading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Error: $e';
        _loading = false;
      });
    }
  }

  void _onMonthChanged(String month) {
    setState(() {
      _selectedMonth = month;
    });
    _fetchDashboard(month: month);
  }

  void _navigateToHealthOverview() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const FinancialHealthOverviewScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return _loading
        ? const Center(child: CircularProgressIndicator())
        : _error != null
            ? Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.error_outline, size: 64, color: Colors.red),
                    const SizedBox(height: 16),
                    Text(_error!, style: const TextStyle(color: Colors.red), textAlign: TextAlign.center),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: _fetchDashboard,
                      child: const Text('Retry'),
                    ),
                  ],
                ),
              )
            : EnhancedDashboardContent(
                data: _data,
                onRefresh: () => _fetchDashboard(month: _selectedMonth),
                availableMonths: _availableMonths,
                selectedMonth: _selectedMonth,
                onMonthChanged: _onMonthChanged,
                onNavigateToHealthOverview: _navigateToHealthOverview,
              );
  }
} 