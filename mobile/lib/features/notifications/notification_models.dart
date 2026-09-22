class NotificationItem {
  const NotificationItem({
    required this.id,
    required this.title,
    required this.body,
    required this.data,
    required this.createdAt,
    this.readAt,
  });

  final String id;
  final String title;
  final String body;
  final Map<String, dynamic> data;
  final DateTime createdAt;
  final DateTime? readAt;

  bool get isRead => readAt != null;

  factory NotificationItem.fromJson(Map<String, dynamic> json) {
    final rawData = json['data'];
    final createdAt = DateTime.tryParse(json['created_at']?.toString() ?? '');
    if (createdAt == null || rawData is! Map) {
      throw const FormatException('La notificación es inválida');
    }
    return NotificationItem(
      id: _requiredString(json, 'id'),
      title: _requiredString(json, 'title'),
      body: _requiredString(json, 'body'),
      data: Map<String, dynamic>.from(rawData),
      createdAt: createdAt,
      readAt: json['read_at'] == null
          ? null
          : DateTime.tryParse(json['read_at'].toString()),
    );
  }
}

String _requiredString(Map<String, dynamic> json, String key) {
  final value = json[key]?.toString().trim();
  if (value == null || value.isEmpty) {
    throw FormatException('$key inválido');
  }
  return value;
}
