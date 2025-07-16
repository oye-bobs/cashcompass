import 'package:flutter/material.dart';
import '../models/saving.dart';
import '../services/saving_service.dart';
import 'package:intl/intl.dart';

class SavingsScreen extends StatefulWidget {
  const SavingsScreen({Key? key}) : super(key: key);

  @override
  State<SavingsScreen> createState() => _SavingsScreenState();
}

class _SavingsScreenState extends State<SavingsScreen> {
  List<Saving> _savings = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchSavings();
  }

  Future<void> _fetchSavings() async {
    setState(() { _loading = true; _error = null; });
    try {
      final savings = await SavingService.fetchSavings(context);
      setState(() { _savings = savings; _loading = false; });
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  Future<void> _showSavingDialog({Saving? saving}) async {
    final amountController = TextEditingController(text: saving?.amount.toString() ?? '');
    final goalController = TextEditingController(text: saving?.goal ?? '');
    final targetAmountController = TextEditingController(text: saving?.targetAmount.toString() ?? '');
    final isEdit = saving != null;
    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(
              isEdit ? Icons.edit : Icons.add,
              color: Colors.teal,
            ),
            const SizedBox(width: 8),
            Text(isEdit ? 'Edit Savings Goal' : 'Add Savings Goal'),
          ],
        ),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: goalController,
                decoration: const InputDecoration(
                  labelText: 'Savings Goal',
                  hintText: 'e.g., Emergency Fund, New Car',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.flag),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: amountController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Current Amount Saved',
                  hintText: '0.00',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.attach_money),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: targetAmountController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Target Amount',
                  hintText: '10000.00',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.track_changes),
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.teal,
              foregroundColor: Colors.white,
            ),
            onPressed: () async {
              final amount = double.tryParse(amountController.text) ?? 0.0;
              final goal = goalController.text.trim();
              final targetAmount = double.tryParse(targetAmountController.text) ?? 0.0;
              
              if (goal.isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Please enter a savings goal')),
                );
                return;
              }
              
              if (targetAmount <= 0) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Target amount must be greater than 0')),
                );
                return;
              }
              
              try {
                if (isEdit) {
                  await SavingService.updateSaving(context, saving!.id, amount, goal, targetAmount);
                } else {
                  await SavingService.addSaving(context, amount, goal, targetAmount);
                }
                Navigator.pop(context, true);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(isEdit ? 'Savings goal updated successfully!' : 'Savings goal added successfully!'),
                    backgroundColor: Colors.green,
                  ),
                );
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Error: $e'),
                    backgroundColor: Colors.red,
                  ),
                );
              }
            },
            child: Text(isEdit ? 'Update' : 'Add'),
          ),
        ],
      ),
    );
    if (result == true) _fetchSavings();
  }

  Future<void> _deleteSaving(int id) async {
    final saving = _savings.firstWhere((s) => s.id == id);
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            const Icon(Icons.delete, color: Colors.red),
            const SizedBox(width: 8),
            const Text('Delete Savings Goal'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Are you sure you want to delete this savings goal?'),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Goal: ${saving.goal}', style: const TextStyle(fontWeight: FontWeight.bold)),
                  Text('Current Amount: \$${NumberFormat('#,##0.00').format(saving.amount)}'),
                  Text('Target Amount: \$${NumberFormat('#,##0.00').format(saving.targetAmount)}'),
                ],
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'This action cannot be undone.',
              style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              foregroundColor: Colors.white,
            ),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirm == true) {
      try {
        await SavingService.deleteSaving(context, id);
        _fetchSavings();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Savings goal deleted successfully!'),
            backgroundColor: Colors.green,
          ),
        );
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return Center(child: Text(_error!, style: const TextStyle(color: Colors.red)));
    final totalCurrent = _savings.fold(0.0, (sum, item) => sum + item.amount);
    return Scaffold(
      appBar: AppBar(title: const Text('Savings Overview')),
      body: RefreshIndicator(
        onRefresh: _fetchSavings,
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Column(
            children: [
              DataTable(
                headingRowColor: MaterialStateProperty.resolveWith<Color?>((states) => Colors.teal[200]),
                columns: const [
                  DataColumn(label: Text('Goal', style: TextStyle(fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Current (\$)', style: TextStyle(fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Target (\$)', style: TextStyle(fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Actions', style: TextStyle(fontWeight: FontWeight.bold))),
                ],
                rows: _savings.map((saving) {
                  return DataRow(
                    cells: [
                      DataCell(Text(saving.goal)),
                      DataCell(Text('\$${NumberFormat('#,##0.00').format(saving.amount)}')),
                      DataCell(Text('\$${NumberFormat('#,##0.00').format(saving.targetAmount)}')),
                      DataCell(Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            icon: const Icon(Icons.edit, color: Colors.blue),
                            onPressed: () => _showSavingDialog(saving: saving),
                            tooltip: 'Edit',
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete, color: Colors.red),
                            onPressed: () => _deleteSaving(saving.id),
                            tooltip: 'Delete',
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
                      'Total Current Savings: ',
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    Text(
                      '\$${NumberFormat('#,##0.00').format(totalCurrent)}',
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
        onPressed: () => _showSavingDialog(),
        child: const Icon(Icons.add),
      ),
    );
  }
} 