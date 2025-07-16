import 'package:flutter/material.dart';
import '../models/income.dart';
import '../services/income_service.dart';
import 'package:month_picker_dialog/month_picker_dialog.dart';
import 'package:intl/intl.dart';

class IncomeScreen extends StatefulWidget {
  const IncomeScreen({Key? key}) : super(key: key);

  @override
  State<IncomeScreen> createState() => _IncomeScreenState();
}

class _IncomeScreenState extends State<IncomeScreen> {
  List<Income> _incomes = [];
  bool _loading = true;
  String? _error;
  DateTime _selectedMonth = DateTime.now();

  @override
  void initState() {
    super.initState();
    _fetchIncomes();
  }

  Future<void> _fetchIncomes() async {
    setState(() { _loading = true; _error = null; });
    try {
      final incomes = await IncomeService.fetchIncomes(
        context,
        month: _selectedMonth.month,
        year: _selectedMonth.year,
      );
      setState(() { _incomes = incomes; _loading = false; });
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
      _fetchIncomes();
    }
  }

  Future<void> _showIncomeDialog({Income? income}) async {
    final amountController = TextEditingController(text: income?.amount.toString() ?? '');
    final sourceController = TextEditingController(text: income?.source ?? '');
    final dateController = TextEditingController(text: income?.date ?? '');
    final isEdit = income != null;
    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(isEdit ? 'Edit Income' : 'Add Income'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: amountController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Amount'),
            ),
            TextField(
              controller: sourceController,
              decoration: const InputDecoration(labelText: 'Source'),
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
              final source = sourceController.text;
              final date = dateController.text;
              try {
                if (isEdit) {
                  await IncomeService.updateIncome(context, income!.id, amount, source, date);
                } else {
                  await IncomeService.addIncome(context, amount, source, date);
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
    if (result == true) _fetchIncomes();
  }

  Future<void> _deleteIncome(int id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Income'),
        content: const Text('Are you sure you want to delete this income item?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          ElevatedButton(onPressed: () => Navigator.pop(context, true), child: const Text('Delete')),
        ],
      ),
    );
    if (confirm == true) {
      try {
        await IncomeService.deleteIncome(context, id);
        _fetchIncomes();
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
        title: Text('Income Overview for ' + DateFormat.yMMMM().format(_selectedMonth)),
        actions: [
          IconButton(
            icon: Icon(Icons.calendar_today),
            onPressed: _pickMonth,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _fetchIncomes,
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal, // Enables horizontal scrolling
          child: Column(
            children: [
              DataTable(
                headingRowColor: MaterialStateProperty.resolveWith<Color?>((states) => Colors.teal[200]),
                columns: const [
                  DataColumn(label: Text('Source', style: TextStyle(fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Amount', style: TextStyle(fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Date', style: TextStyle(fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Actions', style: TextStyle(fontWeight: FontWeight.bold))),
                ],
                rows: _incomes.map((income) {
                  return DataRow(
                    cells: [
                      DataCell(Text(income.source)),
                      DataCell(Text('\$${NumberFormat('#,##0.00').format(income.amount)}')),
                      DataCell(Text(
                        () {
                          try {
                            final inputFormat = DateFormat("EEE, d MMM yyyy HH:mm:ss 'GMT'");
                            final dateObj = inputFormat.parse(income.date, true).toLocal();
                            return DateFormat('EEE, d MMM yyyy').format(dateObj);
                          } catch (e) {
                            return income.date;
                          }
                        }()
                      )),
                      DataCell(Row(
                        children: [
                          IconButton(
                            icon: const Icon(Icons.edit),
                            onPressed: () => _showIncomeDialog(income: income),
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete),
                            onPressed: () => _deleteIncome(income.id),
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
                      'Total Income for ${DateFormat.yMMMM().format(_selectedMonth)}: ',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    Text(
                      '\$${NumberFormat('#,##0.00').format(_incomes.fold(0.0, (sum, item) => sum + item.amount))}',
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
        onPressed: () => _showIncomeDialog(),
        child: const Icon(Icons.add),
      ),
    );
  }
} 