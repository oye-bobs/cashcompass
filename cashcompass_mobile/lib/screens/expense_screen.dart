import 'package:flutter/material.dart';
import '../models/expense.dart';
import '../services/expense_service.dart';
import 'package:month_picker_dialog/month_picker_dialog.dart';
import 'package:intl/intl.dart';

class ExpenseScreen extends StatefulWidget {
  const ExpenseScreen({Key? key}) : super(key: key);

  @override
  State<ExpenseScreen> createState() => _ExpenseScreenState();
}

class _ExpenseScreenState extends State<ExpenseScreen> {
  List<Expense> _expenses = [];
  bool _loading = true;
  String? _error;
  DateTime _selectedMonth = DateTime.now();

  @override
  void initState() {
    super.initState();
    _fetchExpenses();
  }

  Future<void> _fetchExpenses() async {
    setState(() { _loading = true; _error = null; });
    try {
      final expenses = await ExpenseService.fetchExpenses(
        context,
        month: _selectedMonth.month,
        year: _selectedMonth.year,
      );
      setState(() { _expenses = expenses; _loading = false; });
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
      _fetchExpenses();
    }
  }

  Future<void> _showExpenseDialog({Expense? expense}) async {
    final amountController = TextEditingController(text: expense?.amount.toString() ?? '');
    final categoryController = TextEditingController(text: expense?.category ?? '');
    final dateController = TextEditingController(text: expense?.date ?? '');
    final isEdit = expense != null;
    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(isEdit ? 'Edit Expense' : 'Add Expense'),
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
              final date = dateController.text;
              try {
                if (isEdit) {
                  await ExpenseService.updateExpense(context, expense!.id, amount, category, date);
                } else {
                  await ExpenseService.addExpense(context, amount, category, date);
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
    if (result == true) _fetchExpenses();
  }

  Future<void> _deleteExpense(int id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Expense'),
        content: const Text('Are you sure you want to delete this expense item?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          ElevatedButton(onPressed: () => Navigator.pop(context, true), child: const Text('Delete')),
        ],
      ),
    );
    if (confirm == true) {
      try {
        await ExpenseService.deleteExpense(context, id);
        _fetchExpenses();
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
        title: Text('Expense Overview for ' + DateFormat.yMMMM().format(_selectedMonth)),
        actions: [
          IconButton(
            icon: Icon(Icons.calendar_today),
            onPressed: _pickMonth,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _fetchExpenses,
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
                rows: _expenses.map((expense) {
                  return DataRow(
                    cells: [
                      DataCell(Text(expense.category)),
                      DataCell(Text(' 24${NumberFormat('#,##0.00').format(expense.amount)}')),
                      DataCell(Text(
                        expense.date.length >= 10
                            ? DateFormat('EEE, d MMM yyyy').format(DateTime.tryParse(expense.date) ?? DateTime.now())
                            : expense.date,
                      )),
                      DataCell(Row(
                        children: [
                          IconButton(
                            icon: const Icon(Icons.edit),
                            onPressed: () => _showExpenseDialog(expense: expense),
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete),
                            onPressed: () => _deleteExpense(expense.id),
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
                      'Total Expenses for ${DateFormat.yMMMM().format(_selectedMonth)}: ',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    Text(
                      ' 24${NumberFormat('#,##0.00').format(_expenses.fold(0.0, (sum, item) => sum + item.amount))}',
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
        onPressed: () => _showExpenseDialog(),
        child: const Icon(Icons.add),
      ),
    );
  }
} 