import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import 'dart:math';

// --- Modular Widgets ---
class TopListItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final String percent;
  final Color color;
  const TopListItem({required this.icon, required this.label, required this.value, required this.percent, required this.color, Key? key}) : super(key: key);
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2.0),
      child: Row(
        children: [
          Icon(icon, color: color, size: 18),
          const SizedBox(width: 8),
          Expanded(child: Text(label, style: const TextStyle(color: Colors.white, fontSize: 14))),
          Text(value, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          const SizedBox(width: 8),
          Text(percent, style: const TextStyle(color: Colors.white70, fontSize: 12)),
        ],
      ),
    );
  }
}

class TrendIndicator extends StatelessWidget {
  final double change;
  final bool isPositive;
  const TrendIndicator({required this.change, Key? key}) : isPositive = change >= 0, super(key: key);
  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(isPositive ? Icons.arrow_upward : Icons.arrow_downward, color: isPositive ? Colors.greenAccent : Colors.redAccent, size: 18),
        Text('${isPositive ? '+' : ''}${change.toStringAsFixed(1)}%', style: TextStyle(color: isPositive ? Colors.greenAccent : Colors.redAccent, fontWeight: FontWeight.bold)),
      ],
    );
  }
}

class ProgressBar extends StatelessWidget {
  final double percent;
  final Color color;
  const ProgressBar({required this.percent, required this.color, Key? key}) : super(key: key);
  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(8),
      child: LinearProgressIndicator(
        value: percent.clamp(0, 1),
        minHeight: 10,
        backgroundColor: color.withOpacity(0.2),
        valueColor: AlwaysStoppedAnimation<Color>(color),
      ),
    );
  }
}

class ExpandableSummaryCard extends StatefulWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;
  final Widget? details;
  final bool expanded;
  final VoidCallback onTap;
  ExpandableSummaryCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
    this.details,
    required this.expanded,
    required this.onTap,
    Key? key,
  }) : super(key: key);

  @override
  State<ExpandableSummaryCard> createState() => _ExpandableSummaryCardState();
}

class _ExpandableSummaryCardState extends State<ExpandableSummaryCard> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _expandAnim;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: const Duration(milliseconds: 250));
    _expandAnim = CurvedAnimation(parent: _controller, curve: Curves.easeInOut);
    if (widget.expanded) _controller.value = 1.0;
  }

  @override
  void didUpdateWidget(covariant ExpandableSummaryCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.expanded) {
      _controller.forward();
    } else {
      _controller.reverse();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: widget.onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        width: 160,
        margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
        decoration: BoxDecoration(
          gradient: LinearGradient(colors: [widget.color.withOpacity(0.85), widget.color.withOpacity(0.65)]),
          borderRadius: BorderRadius.circular(24),
          boxShadow: [BoxShadow(color: widget.color.withOpacity(0.15), blurRadius: 8, offset: Offset(0, 4))],
        ),
        padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            FaIcon(widget.icon, size: 32, color: Colors.white),
            const SizedBox(height: 12),
            Text(widget.value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white)),
            const SizedBox(height: 6),
            Text(widget.label, style: const TextStyle(fontSize: 14, color: Colors.white70)),
            SizeTransition(
              sizeFactor: _expandAnim,
              axisAlignment: -1.0,
              child: widget.details != null
                  ? Padding(
                      padding: const EdgeInsets.only(top: 12.0),
                      child: widget.details,
                    )
                  : const SizedBox.shrink(),
            ),
          ],
        ),
      ),
    );
  }
}

class EnhancedDashboardContent extends StatefulWidget {
  final Map<String, dynamic>? data;
  final VoidCallback onRefresh;
  final List<String> availableMonths;
  final String selectedMonth;
  final ValueChanged<String> onMonthChanged;
  final VoidCallback onNavigateToHealthOverview;

  const EnhancedDashboardContent({
    Key? key,
    required this.data,
    required this.onRefresh,
    required this.availableMonths,
    required this.selectedMonth,
    required this.onMonthChanged,
    required this.onNavigateToHealthOverview,
  }) : super(key: key);

  @override
  State<EnhancedDashboardContent> createState() => _EnhancedDashboardContentState();
}

class _EnhancedDashboardContentState extends State<EnhancedDashboardContent> {
  int? expandedCardIndex;

  @override
  Widget build(BuildContext context) {
    final data = widget.data;
    final totalIncome = data?['total_income'] ?? 0.0;
    final totalExpenses = data?['total_expenses'] ?? 0.0;
    final netBalance = data?['net_balance'] ?? 0.0;
    final totalSavings = data?['total_savings'] ?? 0.0;
    final budgetBarLabels = List<String>.from(data?['budget_bar_labels'] ?? []);
    final budgetedData = List<double>.from(data?['budgeted_data']?.map((e) => (e as num).toDouble()) ?? []);
    final spentData = List<double>.from(data?['spent_data']?.map((e) => (e as num).toDouble()) ?? []);
    final pieChartLabels = List<String>.from(data?['pie_chart_labels'] ?? []);
    final pieChartData = List<double>.from(data?['pie_chart_data']?.map((e) => (e as num).toDouble()) ?? []);
    final lineChartLabels = List<String>.from(data?['line_chart_labels'] ?? []);
    final lineChartIncomeData = List<double>.from(data?['line_chart_income_data']?.map((e) => (e as num).toDouble()) ?? []);
    final lineChartExpensesData = List<double>.from(data?['line_chart_expenses_data']?.map((e) => (e as num).toDouble()) ?? []);
    // Data extraction
    final currencyFmt = NumberFormat.currency(locale: 'en_US', symbol: '\$');
    // --- Income Details ---
    List<Map<String, dynamic>> topIncomeSources = List<Map<String, dynamic>>.from(data?['top_income_sources'] ?? []);
    double lastMonthIncome = data?['last_month_income'] ?? 0.0;
    double incomeChange = lastMonthIncome > 0 ? ((totalIncome - lastMonthIncome) / lastMonthIncome) * 100 : 0.0;
    Widget incomeDetails = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Top Sources', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        if (topIncomeSources.isNotEmpty)
          ...topIncomeSources.take(3).map((src) => TopListItem(
            icon: FontAwesomeIcons.moneyBill,
            label: src['source'] ?? 'Source',
            value: currencyFmt.format(src['amount'] ?? 0.0),
            percent: totalIncome > 0 ? '${((src['amount'] ?? 0.0) / totalIncome * 100).toStringAsFixed(1)}%' : '-',
            color: Colors.teal,
          )),
        if (topIncomeSources.isEmpty)
          Text('No income sources recorded.', style: TextStyle(color: Colors.white70)),
        const SizedBox(height: 8),
        Row(
          children: [
            Text('This month: ', style: TextStyle(color: Colors.white70)),
            Text(currencyFmt.format(totalIncome), style: TextStyle(color: Colors.white)),
            const SizedBox(width: 12),
            TrendIndicator(change: incomeChange),
          ],
        ),
      ],
    );
    // --- Expenses Details ---
    List<Map<String, dynamic>> topExpenseCategories = List<Map<String, dynamic>>.from(data?['top_expense_categories'] ?? []);
    double lastMonthExpenses = data?['last_month_expenses'] ?? 0.0;
    double expensesChange = lastMonthExpenses > 0 ? ((totalExpenses - lastMonthExpenses) / lastMonthExpenses) * 100 : 0.0;
    Widget expensesDetails = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Top Categories', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        if (topExpenseCategories.isNotEmpty)
          ...topExpenseCategories.take(3).map((cat) => TopListItem(
            icon: FontAwesomeIcons.tags,
            label: cat['category'] ?? 'Category',
            value: currencyFmt.format(cat['amount'] ?? 0.0),
            percent: totalExpenses > 0 ? '${((cat['amount'] ?? 0.0) / totalExpenses * 100).toStringAsFixed(1)}%' : '-',
            color: Colors.redAccent,
          )),
        if (topExpenseCategories.isEmpty)
          Text('No expense categories recorded.', style: TextStyle(color: Colors.white70)),
        const SizedBox(height: 8),
        Row(
          children: [
            Text('This month: ', style: TextStyle(color: Colors.white70)),
            Text(currencyFmt.format(totalExpenses), style: TextStyle(color: Colors.white)),
            const SizedBox(width: 12),
            TrendIndicator(change: expensesChange),
          ],
        ),
      ],
    );
    // --- Net Balance Details ---
    double lastMonthNet = (lastMonthIncome - lastMonthExpenses);
    double netChange = lastMonthNet.abs() > 0 ? ((netBalance - lastMonthNet) / lastMonthNet.abs()) * 100 : 0.0;
    Widget netBalanceDetails = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Net Balance = Income - Expenses', style: TextStyle(color: Colors.white70)),
        Row(
          children: [
            Text('This month: ', style: TextStyle(color: Colors.white70)),
            Text(currencyFmt.format(netBalance), style: TextStyle(color: Colors.white)),
            const SizedBox(width: 12),
            TrendIndicator(change: netChange),
          ],
        ),
        Text('Last month: ${currencyFmt.format(lastMonthNet)}', style: TextStyle(color: Colors.white54)),
      ],
    );
    // --- Savings Details ---
    double savingsGoal = data?['savings_goal'] ?? 0.0;
    double lastMonthSavings = data?['last_month_savings'] ?? 0.0;
    double savingsChange = lastMonthSavings > 0 ? ((totalSavings - lastMonthSavings) / lastMonthSavings) * 100 : 0.0;
    double progress = (savingsGoal > 0) ? (totalSavings / savingsGoal) : 0.0;
    Widget savingsDetails = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Goal: ${currencyFmt.format(savingsGoal)}', style: TextStyle(color: Colors.white70)),
        const SizedBox(height: 4),
        ProgressBar(percent: progress, color: Colors.amber),
        const SizedBox(height: 8),
        Row(
          children: [
            Text('This month: ', style: TextStyle(color: Colors.white70)),
            Text(currencyFmt.format(totalSavings), style: TextStyle(color: Colors.white)),
            const SizedBox(width: 12),
            TrendIndicator(change: savingsChange),
          ],
        ),
        Text('Last month: ${currencyFmt.format(lastMonthSavings)}', style: TextStyle(color: Colors.white54)),
        if (progress >= 1.0)
          Text('🎉 Goal reached! Great job!', style: TextStyle(color: Colors.greenAccent, fontWeight: FontWeight.bold)),
        if (progress < 1.0 && savingsGoal > 0)
          Text('You are ${(progress * 100).toStringAsFixed(0)}% to your goal.', style: TextStyle(color: Colors.white70)),
        if (savingsGoal == 0)
          Text('Set a savings goal to track your progress.', style: TextStyle(color: Colors.white70)),
      ],
    );

    // Modern month selector with month names
    final monthMap = {for (var m in widget.availableMonths) m: DateFormat('MMMM yyyy').format(DateTime.parse(m + '-01'))};
    Widget monthSelector() {
      final isDark = Theme.of(context).brightness == Brightness.dark;
      final Color boxColor = isDark ? const Color(0xFF263238) : Colors.white;
      final Color borderColor = isDark ? Colors.teal[700]! : Colors.teal[200]!;
      final Color textColor = isDark ? Colors.white : Colors.teal[900]!;
      final Color dropdownBg = isDark ? const Color(0xFF37474F) : const Color(0xFFf8ffff);
      return Container(
        margin: const EdgeInsets.symmetric(vertical: 8),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        decoration: BoxDecoration(
          color: boxColor,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: borderColor, width: 1.5),
          boxShadow: [
            BoxShadow(
              color: isDark ? Colors.black.withOpacity(0.4) : Colors.teal.withOpacity(0.08),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: DropdownButtonHideUnderline(
          child: DropdownButton<String>(
            value: widget.selectedMonth,
            items: widget.availableMonths.map((m) => DropdownMenuItem(
              value: m,
              child: Text(
                monthMap[m] ?? m,
                style: TextStyle(fontSize: 15, color: textColor, fontWeight: FontWeight.w500),
              ),
            )).toList(),
            onChanged: (val) { if (val != null) widget.onMonthChanged(val); },
            style: TextStyle(fontSize: 15, color: textColor),
            icon: Icon(Icons.arrow_drop_down, color: textColor),
            dropdownColor: dropdownBg,
            borderRadius: BorderRadius.circular(18),
            menuMaxHeight: 320, // About 8 items tall
          ),
        ),
      );
    }

    // Chart widgets (bar, pie, line) with placeholders if no data
    Widget budgetBarChart() {
      if (budgetBarLabels.isEmpty || budgetedData.isEmpty || spentData.isEmpty) {
        return const Center(child: Text('No budget or expense data for this month.', style: TextStyle(color: Colors.grey)));
      }
      return SizedBox(
        height: 220,
        child: BarChart(
          BarChartData(
            alignment: BarChartAlignment.spaceAround,
            barGroups: List.generate(budgetBarLabels.length, (i) => BarChartGroupData(
              x: i,
              barRods: [
                BarChartRodData(toY: budgetedData[i], color: Colors.teal, width: 12, borderRadius: BorderRadius.circular(6)),
                BarChartRodData(toY: spentData[i], color: Colors.redAccent, width: 12, borderRadius: BorderRadius.circular(6)),
              ],
              showingTooltipIndicators: [0, 1],
            )),
            titlesData: FlTitlesData(
              leftTitles: AxisTitles(
                axisNameWidget: const SizedBox.shrink(),
                sideTitles: SideTitles(showTitles: true, getTitlesWidget: (value, meta) {
                  return Text(value.toStringAsFixed(0));
                }),
              ),
              bottomTitles: AxisTitles(
                axisNameWidget: const SizedBox.shrink(),
                sideTitles: SideTitles(showTitles: true, getTitlesWidget: (value, meta) {
                  int idx = value.toInt();
                  return idx >= 0 && idx < budgetBarLabels.length
                      ? Padding(
                          padding: const EdgeInsets.only(top: 8.0),
                          child: Text(budgetBarLabels[idx], style: const TextStyle(fontSize: 12)),
                        )
                      : const SizedBox();
                }),
              ),
              rightTitles: AxisTitles(
                axisNameWidget: const SizedBox.shrink(),
                sideTitles: SideTitles(showTitles: false),
              ),
              topTitles: AxisTitles(
                axisNameWidget: const SizedBox.shrink(),
                sideTitles: SideTitles(showTitles: false),
              ),
            ),
            gridData: FlGridData(show: true),
            borderData: FlBorderData(show: false),
          ),
        ),
      );
    }

    Widget pieChart() {
      if (pieChartLabels.isEmpty || pieChartData.isEmpty) {
        return const Center(child: Text('No expense category data.', style: TextStyle(color: Colors.grey)));
      }
      return SizedBox(
        height: 180,
        child: PieChart(
          PieChartData(
            sections: List.generate(pieChartLabels.length, (i) => PieChartSectionData(
              value: pieChartData[i],
              title: pieChartLabels[i],
              color: Colors.primaries[i % Colors.primaries.length],
              radius: 60,
              titleStyle: const TextStyle(fontSize: 12, color: Colors.white),
            )),
            sectionsSpace: 2,
            centerSpaceRadius: 30,
          ),
        ),
      );
    }

    Widget lineChart() {
      if (lineChartLabels.isEmpty || (lineChartIncomeData.isEmpty && lineChartExpensesData.isEmpty)) {
        return const Center(child: Text('No daily income/expense data.', style: TextStyle(color: Colors.grey)));
      }
      return SizedBox(
        height: 220,
        child: LineChart(
          LineChartData(
            lineBarsData: [
              if (lineChartIncomeData.isNotEmpty)
                LineChartBarData(
                  spots: List.generate(lineChartIncomeData.length, (i) => FlSpot(i.toDouble(), lineChartIncomeData[i])),
                  isCurved: true,
                  color: Colors.green,
                  barWidth: 3,
                  dotData: FlDotData(show: false),
                ),
              if (lineChartExpensesData.isNotEmpty)
                LineChartBarData(
                  spots: List.generate(lineChartExpensesData.length, (i) => FlSpot(i.toDouble(), lineChartExpensesData[i])),
                  isCurved: true,
                  color: Colors.redAccent,
                  barWidth: 3,
                  dotData: FlDotData(show: false),
                ),
            ],
            titlesData: FlTitlesData(
              leftTitles: AxisTitles(
                axisNameWidget: const Padding(
                  padding: EdgeInsets.only(right: 8.0),
                  child: Text('Amount', style: TextStyle(fontSize: 12)),
                ),
                sideTitles: SideTitles(showTitles: true, getTitlesWidget: (value, meta) {
                  return Text(value.toStringAsFixed(0));
                }),
              ),
              bottomTitles: AxisTitles(
                axisNameWidget: const Padding(
                  padding: EdgeInsets.only(top: 8.0),
                  child: Text('Day', style: TextStyle(fontSize: 12)),
                ),
                sideTitles: SideTitles(showTitles: true, getTitlesWidget: (value, meta) {
                  int idx = value.toInt();
                  return idx >= 0 && idx < lineChartLabels.length
                      ? Padding(
                          padding: const EdgeInsets.only(top: 8.0),
                          child: Text(lineChartLabels[idx], style: const TextStyle(fontSize: 10)),
                        )
                      : const SizedBox();
                }),
              ),
              rightTitles: AxisTitles(
                axisNameWidget: const SizedBox.shrink(),
                sideTitles: SideTitles(showTitles: false),
              ),
              topTitles: AxisTitles(
                axisNameWidget: const SizedBox.shrink(),
                sideTitles: SideTitles(showTitles: false),
              ),
            ),
            gridData: FlGridData(show: true),
            borderData: FlBorderData(show: false),
          ),
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () async => widget.onRefresh(),
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            monthSelector(),
            const SizedBox(height: 16),
            // Horizontally scrollable expandable summary cards
            SizedBox(
              height: 160,
              child: ListView(
                scrollDirection: Axis.horizontal,
                children: [
                  ExpandableSummaryCard(
                    label: 'Income',
                    value: currencyFmt.format(totalIncome),
                    icon: FontAwesomeIcons.moneyBillWave,
                    color: Colors.teal,
                    details: incomeDetails,
                    expanded: expandedCardIndex == 0,
                    onTap: () => setState(() => expandedCardIndex = expandedCardIndex == 0 ? null : 0),
                  ),
                  ExpandableSummaryCard(
                    label: 'Expenses',
                    value: currencyFmt.format(totalExpenses),
                    icon: FontAwesomeIcons.receipt,
                    color: Colors.redAccent,
                    details: expensesDetails,
                    expanded: expandedCardIndex == 1,
                    onTap: () => setState(() => expandedCardIndex = expandedCardIndex == 1 ? null : 1),
                  ),
                  ExpandableSummaryCard(
                    label: 'Net Balance',
                    value: currencyFmt.format(netBalance),
                    icon: FontAwesomeIcons.wallet,
                    color: Colors.green,
                    details: netBalanceDetails,
                    expanded: expandedCardIndex == 2,
                    onTap: () => setState(() => expandedCardIndex = expandedCardIndex == 2 ? null : 2),
                  ),
                  ExpandableSummaryCard(
                    label: 'Savings',
                    value: currencyFmt.format(totalSavings),
                    icon: FontAwesomeIcons.piggyBank,
                    color: Colors.amber,
                    details: savingsDetails,
                    expanded: expandedCardIndex == 3,
                    onTap: () => setState(() => expandedCardIndex = expandedCardIndex == 3 ? null : 3),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            // Charts
            CollapsibleBudgetChartCard(
              labels: budgetBarLabels,
              budgeted: budgetedData,
              spent: spentData,
              monthLabel: DateFormat('MMMM yyyy').format(DateTime.parse(widget.selectedMonth + '-01')),
              currencyFmt: currencyFmt,
              isDark: Theme.of(context).brightness == Brightness.dark,
            ),
            const SizedBox(height: 16),
            CollapsibleSpendingPieChartCard(
              labels: pieChartLabels,
              values: pieChartData,
              isDark: Theme.of(context).brightness == Brightness.dark,
              title: 'Top Spending Categories',
              currencyFmt: currencyFmt,
            ),
            const SizedBox(height: 16),
            CollapsibleIncomeExpenseLineChartCard(
              labels: lineChartLabels,
              incomeData: lineChartIncomeData,
              expensesData: lineChartExpensesData,
              isDark: Theme.of(context).brightness == Brightness.dark,
              title: 'Income vs. Expenses',
              currencyFmt: currencyFmt,
            ),
            const SizedBox(height: 24),
            Center(
              child: ElevatedButton.icon(
                onPressed: widget.onNavigateToHealthOverview,
                icon: const Icon(Icons.health_and_safety, color: Colors.white),
                label: const Text('View Financial Health Overview', style: TextStyle(color: Colors.white)),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 32),
                  backgroundColor: Colors.teal,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
                  textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                ),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}

class CollapsibleBudgetChartCard extends StatefulWidget {
  final List<String> labels;
  final List<double> budgeted;
  final List<double> spent;
  final String monthLabel;
  final NumberFormat currencyFmt;
  final bool isDark;

  const CollapsibleBudgetChartCard({
    required this.labels,
    required this.budgeted,
    required this.spent,
    required this.monthLabel,
    required this.currencyFmt,
    required this.isDark,
    Key? key,
  }) : super(key: key);

  @override
  State<CollapsibleBudgetChartCard> createState() => _CollapsibleBudgetChartCardState();
}

class _CollapsibleBudgetChartCardState extends State<CollapsibleBudgetChartCard> with SingleTickerProviderStateMixin {
  bool expanded = false;
  int? touchedGroupIndex;

  @override
  Widget build(BuildContext context) {
    final budgetedColor = Colors.teal;
    final spentColor = Colors.redAccent;
    final textColor = widget.isDark ? Colors.white : Colors.teal[900]!;
    final bgColor = widget.isDark ? const Color(0xFF23272F) : Colors.white;
    final borderColor = widget.isDark ? Colors.teal[700]! : Colors.teal[200]!;
    final shadow = [BoxShadow(color: Colors.black12, blurRadius: 8, offset: Offset(0, 2))];

    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
      margin: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
      padding: const EdgeInsets.all(0),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: borderColor, width: 1.2),
        boxShadow: shadow,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header
          InkWell(
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
            onTap: () => setState(() => expanded = !expanded),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              child: Row(
                children: [
                  Icon(Icons.bar_chart, color: budgetedColor),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Budget vs. Actual Spending for ${widget.monthLabel}',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: textColor),
                    ),
                  ),
                  Icon(expanded ? Icons.expand_less : Icons.expand_more, color: textColor),
                ],
              ),
            ),
          ),
          if (expanded)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Column(
                children: [
                  // Bar Chart
                  SizedBox(
                    height: 260,
                    child: BarChart(
                      BarChartData(
                        alignment: BarChartAlignment.spaceAround,
                        maxY: (widget.budgeted + widget.spent).fold<double>(0, (prev, e) => e > prev ? e : prev) * 1.2 + 1,
                        minY: 0,
                        groupsSpace: 18,
                        barTouchData: BarTouchData(
                          enabled: true,
                          touchTooltipData: BarTouchTooltipData(
                            getTooltipItem: (group, groupIndex, rod, rodIndex) {
                              if (touchedGroupIndex != groupIndex) return null;
                              final isBudgeted = rodIndex == 0;
                              return BarTooltipItem(
                                isBudgeted ? 'Budgeted: ' : 'Spent: ',
                                TextStyle(
                                  color: isBudgeted ? budgetedColor : spentColor,
                                  fontWeight: FontWeight.bold,
                                ),
                                children: [
                                  TextSpan(
                                    text: widget.currencyFmt.format(rod.toY),
                                    style: TextStyle(
                                      color: widget.isDark ? Colors.white : Colors.black,
                                      fontWeight: FontWeight.normal,
                                    ),
                                  ),
                                ],
                              );
                            },
                          ),
                          touchCallback: (event, response) {
                            setState(() {
                              if (response != null && response.spot != null && event.isInterestedForInteractions) {
                                touchedGroupIndex = response.spot!.touchedBarGroupIndex;
                              } else {
                                touchedGroupIndex = null;
                              }
                            });
                          },
                        ),
                        titlesData: FlTitlesData(
                          show: true,
                          leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          bottomTitles: AxisTitles(
                            sideTitles: SideTitles(
                              showTitles: true,
                              getTitlesWidget: (double value, TitleMeta meta) {
                                final idx = value.toInt();
                                if (idx < 0 || idx >= widget.labels.length) return const SizedBox.shrink();
                                return Transform.rotate(
                                  angle: -0.45,
                                  child: Padding(
                                    padding: const EdgeInsets.only(top: 8.0),
                                    child: Text(
                                      widget.labels[idx],
                                      style: TextStyle(fontSize: 12, color: textColor, fontWeight: FontWeight.w600),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                );
                              },
                              reservedSize: 44,
                            ),
                          ),
                        ),
                        gridData: FlGridData(show: false), // No gridlines
                        borderData: FlBorderData(show: false),
                        barGroups: List.generate(widget.labels.length, (i) {
                          return BarChartGroupData(
                            x: i,
                            barRods: [
                              BarChartRodData(
                                toY: widget.budgeted[i],
                                color: budgetedColor,
                                width: 14,
                                borderRadius: BorderRadius.circular(6),
                              ),
                              BarChartRodData(
                                toY: widget.spent[i],
                                color: spentColor,
                                width: 14,
                                borderRadius: BorderRadius.circular(6),
                              ),
                            ],
                          );
                        }),
                      ),
                    ),
                  ),
                  // Legend
                  Padding(
                    padding: const EdgeInsets.only(top: 12, bottom: 4),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        _LegendDot(color: budgetedColor),
                        const SizedBox(width: 6),
                        Text('Budgeted', style: TextStyle(color: textColor, fontWeight: FontWeight.w600)),
                        const SizedBox(width: 18),
                        _LegendDot(color: spentColor),
                        const SizedBox(width: 6),
                        Text('Spent', style: TextStyle(color: textColor, fontWeight: FontWeight.w600)),
                      ],
                    ),
                  ),
                  // Detailed Breakdown (only for selected category)
                  if (touchedGroupIndex != null && touchedGroupIndex! < widget.labels.length)
                    Padding(
                      padding: const EdgeInsets.only(top: 16.0),
                      child: _BreakdownCard(
                        category: widget.labels[touchedGroupIndex!],
                        budgeted: widget.budgeted[touchedGroupIndex!],
                        spent: widget.spent[touchedGroupIndex!],
                        currencyFmt: widget.currencyFmt,
                        isDark: widget.isDark,
                      ),
                    ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class CollapsibleSpendingPieChartCard extends StatefulWidget {
  final List<String> labels;
  final List<double> values;
  final bool isDark;
  final String title;
  final NumberFormat currencyFmt;

  const CollapsibleSpendingPieChartCard({
    required this.labels,
    required this.values,
    required this.isDark,
    required this.title,
    required this.currencyFmt,
    Key? key,
  }) : super(key: key);

  @override
  State<CollapsibleSpendingPieChartCard> createState() => _CollapsibleSpendingPieChartCardState();
}

class _CollapsibleSpendingPieChartCardState extends State<CollapsibleSpendingPieChartCard> {
  bool expanded = false;
  int? touchedIndex;

  static const List<Color> pieColors = [
    Color(0xFF43e97b), // Teal/Green
    Color(0xFF649ff0), // Blue
    Color(0xFFFF3399), // Pink
    Color(0xFFF58B55), // Orange
    Color(0xFFE75757), // Red
    Color(0xFFD49EF2), // Purple
    Color(0xFFEFF066), // Yellow
  ];

  @override
  Widget build(BuildContext context) {
    final bgColor = widget.isDark ? const Color(0xFF23272F) : Colors.white;
    final textColor = widget.isDark ? Colors.white : Colors.teal[900]!;
    final borderColor = widget.isDark ? Colors.teal[700]! : Colors.teal[200]!;
    final shadow = [BoxShadow(color: Colors.black12, blurRadius: 8, offset: Offset(0, 2))];

    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
      margin: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
      padding: const EdgeInsets.all(0),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: borderColor, width: 1.2),
        boxShadow: shadow,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          InkWell(
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
            onTap: () => setState(() => expanded = !expanded),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              child: Row(
                children: [
                  Icon(Icons.pie_chart, color: pieColors[0]), // Use the first gradient's first color
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      widget.title,
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: textColor),
                    ),
                  ),
                  Icon(expanded ? Icons.expand_less : Icons.expand_more, color: textColor),
                ],
              ),
            ),
          ),
          if (expanded)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Column(
                children: [
                  SizedBox(
                    height: 220,
                    child: PieChart(
                      PieChartData(
                        sectionsSpace: 2,
                        centerSpaceRadius: 48,
                        startDegreeOffset: -90,
                        pieTouchData: PieTouchData(
                          enabled: true,
                          touchCallback: (event, response) {
                            setState(() {
                              if (response != null && response.touchedSection != null && event.isInterestedForInteractions) {
                                touchedIndex = response.touchedSection!.touchedSectionIndex;
                              } else {
                                touchedIndex = null;
                              }
                            });
                          },
                        ),
                        sections: List.generate(widget.labels.length, (i) {
                          final isSelected = touchedIndex == i;
                          return PieChartSectionData(
                            value: widget.values[i],
                            radius: isSelected ? 70 : 60,
                            showTitle: false, // No text on chart
                            color: pieColors[i % pieColors.length],
                            borderSide: BorderSide(color: Colors.black.withOpacity(0.08), width: 2),
                          );
                        }),
                      ),
                    ),
                  ),
                  // Legend
                  Padding(
                    padding: const EdgeInsets.only(top: 12, bottom: 4),
                    child: Wrap(
                      alignment: WrapAlignment.center,
                      spacing: 18,
                      runSpacing: 8,
                      children: List.generate(widget.labels.length, (i) => Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          _LegendDot(color: pieColors[i % pieColors.length]),
                          const SizedBox(width: 6),
                          Text(widget.labels[i], style: TextStyle(color: textColor, fontWeight: FontWeight.w600)),
                        ],
                      )),
                    ),
                  ),
                  // Details for selected category
                  if (touchedIndex != null && touchedIndex! >= 0 && touchedIndex! < widget.labels.length)
                    Padding(
                      padding: const EdgeInsets.only(top: 16.0),
                      child: _PieBreakdownCard(
                        category: widget.labels[touchedIndex!],
                        value: widget.values[touchedIndex!],
                        color: pieColors[touchedIndex! % pieColors.length],
                        currencyFmt: widget.currencyFmt,
                        isDark: widget.isDark,
                      ),
                    ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class CollapsibleIncomeExpenseLineChartCard extends StatefulWidget {
  final List<String> labels;
  final List<double> incomeData;
  final List<double> expensesData;
  final bool isDark;
  final String title;
  final NumberFormat currencyFmt;

  const CollapsibleIncomeExpenseLineChartCard({
    required this.labels,
    required this.incomeData,
    required this.expensesData,
    required this.isDark,
    required this.title,
    required this.currencyFmt,
    Key? key,
  }) : super(key: key);

  @override
  State<CollapsibleIncomeExpenseLineChartCard> createState() => _CollapsibleIncomeExpenseLineChartCardState();
}

class _CollapsibleIncomeExpenseLineChartCardState extends State<CollapsibleIncomeExpenseLineChartCard> {
  bool expanded = false;
  FlSpot? touchedSpot;
  bool isIncomeTouched = false;

  static const Color incomeColor = Color(0xFF43e97b); // Vibrant green
  static const Color expensesColor = Color(0xFFfa709a); // Vibrant pink

  @override
  Widget build(BuildContext context) {
    final bgColor = widget.isDark ? const Color(0xFF23272F) : Colors.white;
    final textColor = widget.isDark ? Colors.white : Colors.teal[900]!;
    final borderColor = widget.isDark ? Colors.teal[700]! : Colors.teal[200]!;
    final shadow = [BoxShadow(color: Colors.black12, blurRadius: 8, offset: Offset(0, 2))];

    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeInOut,
      margin: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
      padding: const EdgeInsets.all(0),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: borderColor, width: 1.2),
        boxShadow: shadow,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          InkWell(
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
            onTap: () => setState(() => expanded = !expanded),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              child: Row(
                children: [
                  Icon(Icons.show_chart, color: incomeColor),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      widget.title,
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: textColor),
                    ),
                  ),
                  Icon(expanded ? Icons.expand_less : Icons.expand_more, color: textColor),
                ],
              ),
            ),
          ),
          if (expanded)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Column(
                children: [
                  SizedBox(
                    height: 220,
                    child: LineChart(
                      LineChartData(
                        minY: 0,
                        maxY: [
                          ...widget.incomeData,
                          ...widget.expensesData
                        ].fold<double>(0, (prev, e) => e > prev ? e : prev) * 1.2 + 1,
                        titlesData: FlTitlesData(
                          show: true,
                          leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          bottomTitles: AxisTitles(
                            sideTitles: SideTitles(
                              showTitles: true,
                              getTitlesWidget: (double value, TitleMeta meta) {
                                final idx = value.toInt();
                                if (idx < 0 || idx >= widget.labels.length) return const SizedBox.shrink();
                                return Padding(
                                  padding: const EdgeInsets.only(top: 8.0),
                                  child: Text(
                                    widget.labels[idx],
                                    style: TextStyle(fontSize: 11, color: textColor, fontWeight: FontWeight.w600),
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                );
                              },
                              reservedSize: 40,
                            ),
                          ),
                        ),
                        gridData: FlGridData(show: false), // No gridlines
                        borderData: FlBorderData(show: false),
                        lineBarsData: [
                          if (widget.incomeData.isNotEmpty)
                            LineChartBarData(
                              spots: List.generate(widget.incomeData.length, (i) => FlSpot(i.toDouble(), widget.incomeData[i])),
                              isCurved: true,
                              color: incomeColor,
                              barWidth: 3,
                              dotData: FlDotData(show: true),
                              belowBarData: BarAreaData(show: false),
                              showingIndicators: touchedSpot != null && isIncomeTouched
                                ? [touchedSpot!.x.toInt()] : [],
                            ),
                          if (widget.expensesData.isNotEmpty)
                            LineChartBarData(
                              spots: List.generate(widget.expensesData.length, (i) => FlSpot(i.toDouble(), widget.expensesData[i])),
                              isCurved: true,
                              color: expensesColor,
                              barWidth: 3,
                              dotData: FlDotData(show: true),
                              belowBarData: BarAreaData(show: false),
                              showingIndicators: touchedSpot != null && !isIncomeTouched
                                ? [touchedSpot!.x.toInt()] : [],
                            ),
                        ],
                        lineTouchData: LineTouchData(
                          enabled: true,
                          touchTooltipData: LineTouchTooltipData(
                            getTooltipItems: (touchedSpots) {
                              return touchedSpots.map((spot) {
                                final isIncome = spot.barIndex == 0;
                                return LineTooltipItem(
                                  (isIncome ? 'Income: ' : 'Expenses: '),
                                  TextStyle(
                                    color: isIncome ? incomeColor : expensesColor,
                                    fontWeight: FontWeight.bold,
                                  ),
                                  children: [
                                    TextSpan(
                                      text: widget.currencyFmt.format(spot.y),
                                      style: TextStyle(
                                        color: widget.isDark ? Colors.white : Colors.black,
                                        fontWeight: FontWeight.normal,
                                      ),
                                    ),
                                  ],
                                );
                              }).toList();
                            },
                          ),
                          touchCallback: (event, response) {
                            setState(() {
                              if (response != null && response.lineBarSpots != null && response.lineBarSpots!.isNotEmpty) {
                                touchedSpot = response.lineBarSpots!.first;
                                isIncomeTouched = response.lineBarSpots!.first.barIndex == 0;
                              } else {
                                touchedSpot = null;
                              }
                            });
                          },
                        ),
                      ),
                    ),
                  ),
                  // Legend
                  Padding(
                    padding: const EdgeInsets.only(top: 12, bottom: 4),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        _LegendDot(color: incomeColor),
                        const SizedBox(width: 6),
                        Text('Income', style: TextStyle(color: textColor, fontWeight: FontWeight.w600)),
                        const SizedBox(width: 18),
                        _LegendDot(color: expensesColor),
                        const SizedBox(width: 6),
                        Text('Expenses', style: TextStyle(color: textColor, fontWeight: FontWeight.w600)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _LegendDot extends StatelessWidget {
  final Color color;
  const _LegendDot({required this.color});
  @override
  Widget build(BuildContext context) {
    return Container(
      width: 14,
      height: 14,
      decoration: BoxDecoration(
        color: color,
        shape: BoxShape.circle,
      ),
    );
  }
}

class _BreakdownCard extends StatelessWidget {
  final String category;
  final double budgeted;
  final double spent;
  final NumberFormat currencyFmt;
  final bool isDark;
  const _BreakdownCard({required this.category, required this.budgeted, required this.spent, required this.currencyFmt, required this.isDark});
  @override
  Widget build(BuildContext context) {
    final remaining = budgeted - spent;
    final textColor = isDark ? Colors.white : Colors.teal[900]!;
    final spentColor = Colors.redAccent;
    final budgetedColor = Colors.teal;
    final remainingColor = remaining >= 0 ? Colors.teal : spentColor;
    final bgColor = isDark ? Color(0xFF263238) : Color(0xFFF8FFFF);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: budgetedColor.withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(category, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: textColor)),
          const SizedBox(height: 6),
          Row(
            children: [
              Text('Budgeted: ', style: TextStyle(color: budgetedColor, fontWeight: FontWeight.w600)),
              Text(currencyFmt.format(budgeted), style: TextStyle(color: textColor)),
            ],
          ),
          Row(
            children: [
              Text('Spent: ', style: TextStyle(color: spentColor, fontWeight: FontWeight.w600)),
              Text(currencyFmt.format(spent), style: TextStyle(color: spentColor)),
            ],
          ),
          Row(
            children: [
              Text('Remaining: ', style: TextStyle(color: remainingColor, fontWeight: FontWeight.w600)),
              Text(currencyFmt.format(remaining), style: TextStyle(color: remainingColor)),
            ],
          ),
        ],
      ),
    );
  }
}

class _PieBreakdownCard extends StatelessWidget {
  final String category;
  final double value;
  final Color color;
  final NumberFormat currencyFmt;
  final bool isDark;
  const _PieBreakdownCard({required this.category, required this.value, required this.color, required this.currencyFmt, required this.isDark});
  @override
  Widget build(BuildContext context) {
    final textColor = isDark ? Colors.white : Colors.teal[900]!;
    final bgColor = isDark ? Color(0xFF263238) : Color(0xFFF8FFFF);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Row(
        children: [
          Container(
            width: 18,
            height: 18,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              '$category: ${currencyFmt.format(value)}',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: textColor),
            ),
          ),
        ],
      ),
    );
  }
} 