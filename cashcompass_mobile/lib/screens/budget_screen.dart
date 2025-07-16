import 'package:flutter/material.dart';
import '../models/budget.dart';
import '../services/budget_service.dart';
import 'package:month_picker_dialog/month_picker_dialog.dart';
import 'package:intl/intl.dart';

class BudgetScreen extends StatefulWidget {
  const BudgetScreen({Key? key}) : super(key: key);

  @override
  State<BudgetScreen> createState() => _BudgetScreenState();
}

class _BudgetScreenState extends State<BudgetScreen> {
  List<Budget> _budgets = [];
  bool _loading = true;
  String? _error;
  DateTime _selectedMonth = DateTime.now();

  @override
  void initState() {
    super.initState();
    _fetchBudgets();
  }

  Future<void> _fetchBudgets() async {
    setState(() { _loading = true; _error = null; });
    try {
      final budgets = await BudgetService.fetchBudgets(
        context,
        month: _selectedMonth.month,
        year: _selectedMonth.year,
      );
      setState(() { _budgets = budgets; _loading = false; });
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  void _pickMonth() async {
    final picked = await showMonthPicker(
      context: context,
      initialDate: _selectedMonth,
    );
    if (picked != null) {
      setState(() {
        _selectedMonth = picked;
      });
      _fetchBudgets();
    }
  }

  // Helper function to extract raw date in yyyy-MM-dd format
  String _extractRawDate(String dateStr) {
    try {
      final inputFormat = DateFormat("EEE, d MMM yyyy HH:mm:ss 'GMT'");
      final dateObj = inputFormat.parse(dateStr, true).toLocal();
      return DateFormat('yyyy-MM-dd').format(dateObj);
    } catch (e) {
      return dateStr.length >= 10 ? dateStr.substring(0, 10) : dateStr;
    }
  }

  Future<void> _showBudgetDialog({Budget? budget}) async {
    final amountController = TextEditingController(text: budget?.amount.toString() ?? '');
    final categoryController = TextEditingController(text: budget?.category ?? '');
    final dateController = TextEditingController(
      text: budget != null
          ? _extractRawDate(budget.date)
          : DateFormat('yyyy-MM-dd').format(DateTime(_selectedMonth.year, _selectedMonth.month, 1))
    );
    final isEdit = budget != null;
    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(isEdit ? 'Edit Budget' : 'Add Budget'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: amountController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Amount'),
            ),
            TextField(
              controller: categoryController,
              decoration: const InputDecoration(labelText: 'Category'),
            ),
            TextField(
              controller: dateController,
              decoration: const InputDecoration(labelText: 'Date (YYYY-MM-DD)'),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () async {
              final amount = double.tryParse(amountController.text) ?? 0.0;
              final category = categoryController.text;
              final date = dateController.text.length >= 10 ? dateController.text.substring(0, 10) : dateController.text;
              try {
                if (isEdit) {
                  await BudgetService.updateBudget(context, budget!.id, amount, category, date);
                } else {
                  await BudgetService.addBudget(context, amount, category, date);
                }
                Navigator.pop(context, true);
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
              }
            },
            child: Text(isEdit ? 'Update' : 'Add'),
          ),
        ],
      ),
    );
    if (result == true) _fetchBudgets();
  }

  Future<void> _deleteBudget(int id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Budget'),
        content: const Text('Are you sure you want to delete this budget item?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          ElevatedButton(onPressed: () => Navigator.pop(context, true), child: const Text('Delete')),
        ],
      ),
    );
    if (confirm == true) {
      try {
        await BudgetService.deleteBudget(context, id);
        _fetchBudgets();
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return Center(child: Text(_error!, style: const TextStyle(color: Colors.red)));
    return Scaffold(
      appBar: AppBar(
        title: Text('Budget Overview for ' + DateFormat.yMMMM().format(_selectedMonth)),
        actions: [
          IconButton(
            icon: Icon(Icons.calendar_today),
            onPressed: _pickMonth,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _fetchBudgets,
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Column(
            children: [
              DataTable(
                headingRowColor: MaterialStateProperty.resolveWith<Color?>((states) => Colors.teal[200]),
                columns: const [
                  DataColumn(label: Text('Category', style: TextStyle(fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Amount', style: TextStyle(fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Date', style: TextStyle(fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Actions', style: TextStyle(fontWeight: FontWeight.bold))),
                ],
                rows: _budgets.map((budget) {
                  return DataRow(
                    cells: [
                      DataCell(Text(budget.category)),
                      DataCell(Text('\$${NumberFormat('#,##0.00').format(budget.amount)}')),
                      DataCell(Text(
                        () {
                          try {
                            final dateObj = DateTime.parse(budget.date.substring(0, 10));
                            return DateFormat('EEE, d MMM yyyy').format(dateObj);
                          } catch (e) {
                            return budget.date;
                          }
                        }()
                      )),
                      DataCell(Row(
                        children: [
                          IconButton(
                            icon: const Icon(Icons.edit),
                            onPressed: () => _showBudgetDialog(budget: budget),
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete),
                            onPressed: () => _deleteBudget(budget.id),
                          ),
                        ],
                      )),
                    ],
                  );
                }).toList(),
              ),
              // Total row
              Padding(
                padding: const EdgeInsets.all(16.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    Text(
                      'Total Budget for ${DateFormat.yMMMM().format(_selectedMonth)}: ',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    Text(
                      '\$${NumberFormat('#,##0.00').format(_budgets.fold(0.0, (sum, item) => sum + item.amount))}',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.teal),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showBudgetDialog(),
        child: const Icon(Icons.add),
      ),
    );
  }
} 