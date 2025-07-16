class Setting {
  final String key;
  final String value;

  Setting({required this.key, required this.value});

  factory Setting.fromJson(Map<String, dynamic> json) {
    return Setting(
      key: json['key'],
      value: json['value'],
    );
  }
} 