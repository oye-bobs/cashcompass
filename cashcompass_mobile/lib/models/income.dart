class Income {
  final int id;
  final double amount;
  final String source;
  final String date;

  Income({required this.id, required this.amount, required this.source, required this.date});

  factory Income.fromJson(Map<String, dynamic> json) {
    return Income(
      id: json['id'] ?? 0,
      amount: json['amount'] is num
          ? (json['amount'] as num).toDouble()
          : double.tryParse(json['amount'].toString()) ?? 0.0,
      source: json['source'] ?? '',
      date: json['date'] ?? '',
    );
  }
} 