class Profile {
  final int id;
  final String username;
  final String email;
  final String createdAt;

  Profile({required this.id, required this.username, required this.email, required this.createdAt});

  factory Profile.fromJson(Map<String, dynamic> json) {
    return Profile(
      id: json['id'],
      username: json['username'],
      email: json['email'],
      createdAt: json['created_at'],
    );
  }
} 