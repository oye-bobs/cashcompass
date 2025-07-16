class Saving {
  final int id;
  final double amount;
  final String goal;
  final double targetAmount;

  Saving({required this.id, required this.amount, required this.goal, required this.targetAmount});

  factory Saving.fromJson(Map<String, dynamic> json) {
    double parseDouble(dynamic value) {
      if (value is num) return value.toDouble();
      if (value is String) return double.tryParse(value) ?? 0.0;
      return 0.0;
    }
    return Saving(
      id: json['id'],
      amount: parseDouble(json['amount']),
      goal: json['goal'],
      targetAmount: parseDouble(json['target_amount']),
    );
  }
} 