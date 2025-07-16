class Debt {
  final int id;
  final double currentBalance;
  final String debtName;
  final String debtType;
  final String dueDate;

  Debt({required this.id, required this.currentBalance, required this.debtName, required this.debtType, required this.dueDate});

  factory Debt.fromJson(Map<String, dynamic> json) {
    double parseDouble(dynamic value) {
      if (value is num) return value.toDouble();
      if (value is String) return double.tryParse(value) ?? 0.0;
      return 0.0;
    }
    return Debt(
      id: json['id'],
      currentBalance: parseDouble(json['current_balance']),
      debtName: json['debt_name'],
      debtType: json['debt_type'],
      dueDate: json['due_date'],
    );
  }
} 