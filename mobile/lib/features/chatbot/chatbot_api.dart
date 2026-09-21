import '../../core/network/api_client.dart';
import 'chatbot_models.dart';

class ChatbotApi {
  ChatbotApi({
    ApiClient? client,
    TokenProvider? tokenProvider,
    UnauthorizedHandler? onUnauthorized,
  }) : _client =
           client ??
           ApiClient(
             tokenProvider: tokenProvider,
             onUnauthorized: onUnauthorized,
           );

  final ApiClient _client;

  Future<List<ChatbotMessage>> getMessages() async {
    final response = await _client.get<List<ChatbotMessage>>(
      'chatbot/messages',
      parser: (value) => _parseMessages(value),
    );
    return List<ChatbotMessage>.of(response.data ?? const []);
  }

  Future<List<ChatbotMessage>> sendMessage(String content) async {
    await _client.post<void>('chatbot/message', data: {'message': content});
    return getMessages();
  }

  Future<void> deleteConversation() async {
    await _client.delete<void>('chatbot/conversation');
  }

  static List<ChatbotMessage> _parseMessages(dynamic value) {
    if (value is! List) {
      throw const FormatException('La respuesta del chatbot es inválida');
    }
    return value
        .map((item) {
          if (item is! Map) {
            throw const FormatException('Un mensaje del chatbot es inválido');
          }
          return ChatbotMessage.fromJson(Map<String, dynamic>.from(item));
        })
        .toList(growable: true);
  }
}
