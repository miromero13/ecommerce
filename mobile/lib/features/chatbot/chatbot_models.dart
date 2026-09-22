enum ChatbotMessageRole { user, assistant }

enum ChatbotMessageState { normal, sending, error }

class ChatbotRecommendation {
  const ChatbotRecommendation({
    required this.variantId,
    required this.productId,
    required this.name,
    this.description,
    this.imageUrl,
    this.sku,
    this.price,
    this.sizeName,
    this.colorName,
    this.availableQuantity,
  });

  final String variantId;
  final String productId;
  final String name;
  final String? description;
  final String? imageUrl;
  final String? sku;
  final String? price;
  final String? sizeName;
  final String? colorName;
  final int? availableQuantity;

  factory ChatbotRecommendation.fromJson(Map<String, dynamic> json) {
    return ChatbotRecommendation(
      variantId: _requiredString(json, 'variant_id'),
      productId: _requiredString(json, 'product_id'),
      name: _requiredString(json, 'name'),
      description: json['description']?.toString(),
      imageUrl: json['image_url']?.toString(),
      sku: json['sku']?.toString(),
      price: json['price']?.toString(),
      sizeName: json['size_name']?.toString(),
      colorName: json['color_name']?.toString(),
      availableQuantity: _optionalInt(json['available_quantity']),
    );
  }
}

class ChatbotMessage {
  const ChatbotMessage({
    required this.id,
    required this.role,
    required this.content,
    required this.createdAt,
    this.metadata = const [],
  });

  final String id;
  final ChatbotMessageRole role;
  final String content;
  final DateTime createdAt;
  final List<ChatbotRecommendation> metadata;

  factory ChatbotMessage.fromJson(Map<String, dynamic> json) {
    final rawMetadata = json['metadata'];
    return ChatbotMessage(
      id: _requiredString(json, 'id'),
      role: _roleFromJson(json['role']),
      content: _requiredString(json, 'content'),
      createdAt: DateTime.parse(_requiredString(json, 'created_at')),
      metadata: rawMetadata == null
          ? const []
          : _parseList(rawMetadata, ChatbotRecommendation.fromJson),
    );
  }
}

String _requiredString(Map<String, dynamic> json, String key) {
  final value = json[key];
  if (value == null || value.toString().trim().isEmpty) {
    throw FormatException('$key inválido');
  }
  return value.toString();
}

ChatbotMessageRole _roleFromJson(Object? value) {
  return switch (value?.toString()) {
    'user' => ChatbotMessageRole.user,
    'assistant' => ChatbotMessageRole.assistant,
    _ => throw FormatException('role inválido: $value'),
  };
}

int? _optionalInt(Object? value) {
  if (value is num) return value.toInt();
  return value == null ? null : int.tryParse(value.toString());
}

List<T> _parseList<T>(dynamic value, T Function(Map<String, dynamic>) parser) {
  if (value is! List) {
    throw const FormatException('La respuesta del chatbot es inválida');
  }
  return value
      .map((item) {
        if (item is! Map) {
          throw const FormatException('Un mensaje del chatbot es inválido');
        }
        return parser(Map<String, dynamic>.from(item));
      })
      .toList(growable: false);
}
