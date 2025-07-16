class Budget {
  final int id;
  final double amount;
  final String category;
  final String date;

  Budget({required this.id, required this.amount, required this.category, required this.date});

  factory Budget.fromJson(Map<String, dynamic> json) {
    final rawAmount = json['amount'];
    double parsedAmount;
    if (rawAmount is num) {
      parsedAmount = rawAmount.toDouble();
    } else if (rawAmount is String) {
      parsedAmount = double.tryParse(rawAmount) ?? 0.0;
    } else {
      parsedAmount = 0.0;
    }
    return Budget(
      id: json['id'],
      amount: parsedAmount,
      category: json['category'],
      date: json['date'],
    );
  }
} 