class Expense {
  final int id;
  final double amount;
  final String category;
  final String date;

  Expense({required this.id, required this.amount, required this.category, required this.date});

  factory Expense.fromJson(Map<String, dynamic> json) {
    return Expense(
      id: json['id'] ?? 0,
      amount: json['amount'] is num
          ? (json['amount'] as num).toDouble()
          : double.tryParse(json['amount'].toString()) ?? 0.0,
      category: json['category'] ?? '',
      date: json['date'] ?? '',
    );
  }
} 