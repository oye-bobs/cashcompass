import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../services/financial_health_service.dart';
import 'package:intl/intl.dart';

class FinancialHealthOverviewScreen extends StatefulWidget {
  const FinancialHealthOverviewScreen({super.key});

  @override
  State<FinancialHealthOverviewScreen> createState() => _FinancialHealthOverviewScreenState();
}

class _FinancialHealthOverviewScreenState extends State<FinancialHealthOverviewScreen> {
  Map<String, dynamic>? _data;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchData();
  }

  Future<void> _fetchData() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await FinancialHealthService.fetchFinancialHealth();
      if (data == null) {
        setState(() {
          _error = 'Failed to load financial health data.';
          _loading = false;
        });
      } else {
        setState(() {
          _data = data;
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

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final score = (_data?['financial_health_score'] ?? 0).toDouble();
    final netWorth = _data?['net_worth'] ?? 0.0;
    final cashFlow = _data?['cash_flow'] ?? 0.0;
    final totalSavings = _data?['total_assets'] ?? 0.0;
    final totalLiabilities = _data?['total_liabilities'] ?? 0.0;
    final allIncome = _data?['all_total_income'] ?? 0.0;
    final allExpenses = _data?['all_total_expenses'] ?? 0.0;
    final scoreDetails = List<String>.from(_data?['score_details'] ?? []);
    final savingsGoals = List<Map<String, dynamic>>.from(_data?['savings_goals'] ?? []);

    Color scoreColor() {
      if (score >= 70) return Colors.green;
      if (score >= 40) return Colors.orange;
      return Colors.red;
    }
    String scoreEmoji() {
      if (score >= 70) return '😊';
      if (score >= 40) return '😐';
      return '😟';
    }

    Widget gauge() {
      final isDark = Theme.of(context).brightness == Brightness.dark;
      final cardBg = isDark ? const Color(0xFF181A20) : Colors.white;
      final scoreGreen = Color(0xFF43e97b);
      final remainderColor = isDark ? Color(0xFF44474F) : Color(0xFFe0e0e0);
      final textColor = isDark ? Colors.white : Colors.teal[900]!;
      return Container(
        decoration: BoxDecoration(
          color: cardBg,
          borderRadius: BorderRadius.circular(28),
          boxShadow: [
            BoxShadow(
              color: isDark ? Colors.black.withOpacity(0.5) : Colors.teal.withOpacity(0.08),
              blurRadius: 16,
              offset: const Offset(0, 6),
            ),
          ],
        ),
        margin: const EdgeInsets.only(bottom: 12),
        child: Center(
          child: SizedBox(
            height: 120,
            child: LayoutBuilder(
              builder: (context, constraints) {
                final size = constraints.maxHeight < constraints.maxWidth
                    ? constraints.maxHeight
                    : constraints.maxWidth;
                return Stack(
                  alignment: Alignment.center,
                  children: [
                    PieChart(
                      PieChartData(
                        startDegreeOffset: 225,
                        sectionsSpace: 0,
                        centerSpaceRadius: size * 0.32,
                        sections: [
                          PieChartSectionData(
                            value: score.clamp(0, 100),
                            color: scoreGreen,
                            radius: size * 0.44,
                            showTitle: false,
                          ),
                          PieChartSectionData(
                            value: (100 - score.clamp(0, 100)).toDouble(),
                            color: remainderColor,
                            radius: size * 0.44,
                            showTitle: false,
                          ),
                        ],
                      ),
                    ),
                    Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text('${score.toStringAsFixed(0)}%', style: TextStyle(fontSize: size * 0.19, fontWeight: FontWeight.bold, color: textColor)),
                        Text(scoreEmoji(), style: TextStyle(fontSize: size * 0.15)),
                      ],
                    ),
                  ],
                );
              },
            ),
          ),
        ),
      );
    }

    Widget metricsGrid() {
      final currencyFmt = NumberFormat.currency(locale: 'en_US', symbol: '\$');
      final metrics = [
        {'label': 'Net Worth', 'value': netWorth, 'icon': Icons.account_balance_wallet, 'color': Color(0xFF43e97b)},
        {'label': 'Cash Flow', 'value': cashFlow, 'icon': Icons.sync_alt, 'color': Color(0xFF649ff0)},
        {'label': 'Savings', 'value': totalSavings, 'icon': Icons.savings, 'color': Color(0xFFFF3399)},
        {'label': 'Liabilities', 'value': totalLiabilities, 'icon': Icons.credit_card, 'color': Color(0xFFF58B55)},
        {'label': 'All Income', 'value': allIncome, 'icon': Icons.attach_money, 'color': Color(0xFFE75757)},
        {'label': 'All Expenses', 'value': allExpenses, 'icon': Icons.money_off, 'color': Color(0xFFD49EF2)},
      ];
      return SizedBox(
        height: 110,
        child: ListView.separated(
          scrollDirection: Axis.horizontal,
          itemCount: metrics.length,
          separatorBuilder: (_, __) => const SizedBox(width: 14),
          itemBuilder: (context, i) {
            final m = metrics[i];
            return Container(
              width: 140,
              decoration: BoxDecoration(
                color: m['color'],
                borderRadius: BorderRadius.circular(22),
                boxShadow: [
                  BoxShadow(
                    color: (m['color'] as Color).withOpacity(0.15),
                    blurRadius: 6,
                    offset: const Offset(0, 3),
                  ),
                ],
              ),
              padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Icon(m['icon'] as IconData, color: Colors.white, size: 26),
                  const SizedBox(height: 7),
                  Text(
                    currencyFmt.format(m['value'] as num),
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                      overflow: TextOverflow.ellipsis,
                    ),
                    maxLines: 1,
                  ),
                  const SizedBox(height: 5),
                  Text(
                    m['label'] as String,
                    style: const TextStyle(
                      fontSize: 13,
                      color: Colors.white70,
                      fontWeight: FontWeight.w500,
                      letterSpacing: 0.2,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            );
          },
        ),
      );
    }

    Widget scoreBreakdown() {
      return ExpansionTile(
        title: const Text('Score Breakdown', style: TextStyle(fontWeight: FontWeight.bold)),
        initiallyExpanded: true,
        children: scoreDetails.isNotEmpty
            ? scoreDetails.map((d) => ListTile(
                  leading: const Icon(Icons.check_circle, color: Colors.teal),
                  title: Text(d),
                )).toList()
            : [
                const ListTile(
                  title: Text('No detailed score information available. Add more financial data!'),
                ),
              ],
      );
    }

    Widget savingsGoalsList() {
      if (savingsGoals.isEmpty) {
        return const Center(child: Text('No savings goals yet. Add a goal to see your progress!'));
      }
      final currencyFmt = NumberFormat.currency(locale: 'en_US', symbol: '\$');
      final cardGradient = LinearGradient(colors: [Color(0xFF43e97b), Color(0xFF38f9d7)]);
      return SizedBox(
        height: 110,
        child: ListView.separated(
          scrollDirection: Axis.horizontal,
          itemCount: savingsGoals.length,
          separatorBuilder: (_, __) => const SizedBox(width: 12),
          itemBuilder: (context, i) {
            final goal = savingsGoals[i];
            final progress = ((goal['current_amount'] ?? 0) / (goal['target_amount'] ?? 1)).clamp(0.0, 1.0);
            final achieved = progress >= 1.0;
            return Container(
              width: 220,
              decoration: BoxDecoration(
                gradient: cardGradient,
                borderRadius: BorderRadius.circular(20),
                boxShadow: [BoxShadow(color: Colors.teal.withOpacity(0.08), blurRadius: 8, offset: const Offset(0, 4))],
              ),
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Row(
                    children: [
                      Icon(Icons.flag, color: Colors.white, size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(goal['goal'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white, fontSize: 15), overflow: TextOverflow.ellipsis, maxLines: 1),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  LinearProgressIndicator(
                    value: progress,
                    backgroundColor: Colors.white.withOpacity(0.3),
                    color: Colors.white,
                    minHeight: 9,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Flexible(
                        child: Text(
                          currencyFmt.format(goal['current_amount'] ?? 0),
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
                          overflow: TextOverflow.ellipsis,
                          maxLines: 1,
                        ),
                      ),
                      const Text(' / ', style: TextStyle(color: Colors.white, fontSize: 14)),
                      Flexible(
                        child: Text(
                          currencyFmt.format(goal['target_amount'] ?? 0),
                          style: const TextStyle(color: Colors.white, fontSize: 14),
                          overflow: TextOverflow.ellipsis,
                          maxLines: 1,
                        ),
                      ),
                    ],
                  ),
                  if (achieved)
                    const Padding(
                      padding: EdgeInsets.only(top: 4.0),
                      child: Text('Goal Achieved! 🎉', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13)),
                    ),
                ],
              ),
            );
          },
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Financial Health Overview'),
        backgroundColor: Colors.teal,
      ),
      body: RefreshIndicator(
        onRefresh: _fetchData,
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
                : ListView(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    children: [
                      // Hero section
                      Container(
                        decoration: BoxDecoration(
                          color: isDark ? const Color(0xFF181A20) : Colors.white,
                          borderRadius: BorderRadius.circular(24),
                        ),
                        padding: const EdgeInsets.symmetric(vertical: 24),
                        child: Column(
                          children: [
                            gauge(),
                          ],
                        ),
                      ),
                      const SizedBox(height: 20),
                      metricsGrid(),
                      const SizedBox(height: 20),
                      scoreBreakdown(),
                      const SizedBox(height: 20),
                      const Text('Your Savings Goals', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                      const SizedBox(height: 8),
                      savingsGoalsList(),
                      const SizedBox(height: 32),
                    ],
                  ),
      ),
    );
  }
} 