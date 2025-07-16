import 'package:flutter/material.dart';
import '../models/debt.dart';
import '../services/debt_service.dart';
import 'package:intl/intl.dart';

class DebtScreen extends StatefulWidget {
  const DebtScreen({Key? key}) : super(key: key);

  @override
  State<DebtScreen> createState() => _DebtScreenState();
}

class _DebtScreenState extends State<DebtScreen> {
  List<Debt> _debts = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchDebts();
  }

  Future<void> _fetchDebts() async {
    setState(() { _loading = true; _error = null; });
    try {
      final debts = await DebtService.fetchDebts(context);
      setState(() { _debts = debts; _loading = false; });
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  Future<void> _showDebtDialog({Debt? debt}) async {
    final currentBalanceController = TextEditingController(text: debt?.currentBalance.toString() ?? '');
    final debtNameController = TextEditingController(text: debt?.debtName ?? '');
    final debtTypeController = TextEditingController(text: debt?.debtType ?? '');
    final dueDateController = TextEditingController(text: debt?.dueDate ?? '');
    final isEdit = debt != null;
    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(isEdit ? 'Edit Debt' : 'Add Debt'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: currentBalanceController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Current Balance'),
            ),
            TextField(
              controller: debtNameController,
              decoration: const InputDecoration(labelText: 'Debt Name'),
            ),
            TextField(
              controller: debtTypeController,
              decoration: const InputDecoration(labelText: 'Debt Type'),
            ),
            TextField(
              controller: dueDateController,
              decoration: const InputDecoration(labelText: 'Due Date (YYYY-MM-DD)'),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () async {
              final currentBalance = double.tryParse(currentBalanceController.text) ?? 0.0;
              final debtName = debtNameController.text;
              final debtType = debtTypeController.text;
              final dueDate = dueDateController.text;
              try {
                if (isEdit) {
                  await DebtService.updateDebt(context, debt!.id, currentBalance, debtName, debtType, dueDate);
                } else {
                  await DebtService.addDebt(context, currentBalance, debtName, debtType, dueDate);
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
    if (result == true) _fetchDebts();
  }

  Future<void> _deleteDebt(int id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Debt'),
        content: const Text('Are you sure you want to delete this debt item?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          ElevatedButton(onPressed: () => Navigator.pop(context, true), child: const Text('Delete')),
        ],
      ),
    );
    if (confirm == true) {
      try {
        await DebtService.deleteDebt(context, id);
        _fetchDebts();
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
      appBar: AppBar(title: const Text('Debt Overview')),
      body: RefreshIndicator(
        onRefresh: _fetchDebts,
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Column(
            children: [
              DataTable(
                headingRowColor: MaterialStateProperty.resolveWith<Color?>((states) => Colors.teal[200]),
                columns: const [
                  DataColumn(label: Text('Name', style: TextStyle(fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Type', style: TextStyle(fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Balance', style: TextStyle(fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Due Date', style: TextStyle(fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Actions', style: TextStyle(fontWeight: FontWeight.bold))),
                ],
                rows: _debts.map((debt) {
                  return DataRow(
                    cells: [
                      DataCell(Text(debt.debtName)),
                      DataCell(Text(debt.debtType)),
                      DataCell(Text(NumberFormat.currency(locale: 'en_US', symbol: '\$').format(debt.currentBalance))),
                      DataCell(Text(debt.dueDate ?? 'N/A')),
                      DataCell(Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            icon: const Icon(Icons.edit, color: Colors.blue),
                            onPressed: () => _showDebtDialog(debt: debt),
                            tooltip: 'Edit',
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete, color: Colors.red),
                            onPressed: () => _deleteDebt(debt.id),
                            tooltip: 'Delete',
                          ),
                        ],
                      )),
                    ],
                  );
                }).toList(),
              ),
            ],
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showDebtDialog(),
        child: const Icon(Icons.add),
      ),
    );
  }
} 