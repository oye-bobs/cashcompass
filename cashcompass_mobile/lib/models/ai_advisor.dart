class AIAdvisor {
  final String advice;

  AIAdvisor({required this.advice});

  factory AIAdvisor.fromJson(Map<String, dynamic> json) {
    return AIAdvisor(
      advice: json['advice'],
    );
  }
} 