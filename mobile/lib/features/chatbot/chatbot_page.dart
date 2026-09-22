import 'dart:async';

import 'package:flutter/material.dart';

import '../../shared/widgets/app_dialog.dart';
import '../../shared/widgets/product_image.dart';
import '../auth/auth_controller.dart';
import 'chatbot_api.dart';
import 'chatbot_models.dart';

class ChatbotAssistant extends StatelessWidget {
  const ChatbotAssistant({
    super.key,
    required this.authController,
    required this.onOpenProduct,
  });

  final AuthController authController;
  final Future<void> Function(String productId) onOpenProduct;

  @override
  Widget build(BuildContext context) {
    return Positioned(
      right: 20,
      bottom: 20,
      child: FloatingActionButton(
        heroTag: 'shopping-chatbot',
        tooltip: 'Abrir asistente de compras',
        onPressed: () => showModalBottomSheet<void>(
          context: context,
          isScrollControlled: true,
          useSafeArea: true,
          builder: (_) => FractionallySizedBox(
            heightFactor: .9,
            child: _ChatbotPanel(
              api: ChatbotApi(
                tokenProvider: () => authController.accessToken,
                onUnauthorized: authController.handleUnauthorized,
              ),
              onOpenProduct: onOpenProduct,
            ),
          ),
        ),
        child: const Icon(Icons.chat_bubble_outline),
      ),
    );
  }
}

class _ChatbotPanel extends StatefulWidget {
  const _ChatbotPanel({required this.api, required this.onOpenProduct});

  final ChatbotApi api;
  final Future<void> Function(String productId) onOpenProduct;

  @override
  State<_ChatbotPanel> createState() => _ChatbotPanelState();
}

class _ChatbotPanelState extends State<_ChatbotPanel> {
  final _inputController = TextEditingController();
  final _scrollController = ScrollController();
  List<_UiMessage> _messages = [];
  String? _error;
  bool _loading = false;
  bool _sending = false;
  bool _resetting = false;

  @override
  void initState() {
    super.initState();
    unawaited(_loadMessages());
  }

  @override
  void dispose() {
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      child: Column(
        children: [
          _header(context),
          Expanded(child: _conversation()),
          _composer(),
        ],
      ),
    );
  }

  Widget _header(BuildContext context) {
    return ListTile(
      title: const Text('Asistente de compras'),
      subtitle: const Text('Pregúntame sobre productos y pedidos.'),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          IconButton(
            tooltip: 'Borrar conversación',
            onPressed: _sending || _resetting ? null : _confirmReset,
            icon: const Icon(Icons.delete_outline),
          ),
          IconButton(
            tooltip: 'Cerrar asistente',
            onPressed: _sending || _resetting
                ? null
                : () => Navigator.of(context).pop(),
            icon: const Icon(Icons.close),
          ),
        ],
      ),
    );
  }

  Widget _conversation() {
    if (_loading && _messages.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    return ListView(
      controller: _scrollController,
      padding: const EdgeInsets.all(16),
      children: [
        if (_messages.isEmpty && _error == null)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 32),
            child: Center(
              child: Text('Todavía no hay mensajes. ¿En qué puedo ayudarte?'),
            ),
          ),
        for (final message in _messages) _messageBubble(message),
        if (_error != null)
          Padding(
            padding: const EdgeInsets.only(top: 12),
            child: Text(
              _error!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ),
      ],
    );
  }

  Widget _messageBubble(_UiMessage message) {
    final isUser = message.message.role == ChatbotMessageRole.user;
    final colorScheme = Theme.of(context).colorScheme;
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 360),
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: message.state == ChatbotMessageState.error
              ? colorScheme.errorContainer
              : isUser
              ? colorScheme.primary
              : colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              message.message.content,
              style: TextStyle(
                color: isUser && message.state != ChatbotMessageState.error
                    ? colorScheme.onPrimary
                    : null,
              ),
            ),
            if (!isUser && message.message.metadata.isNotEmpty) ...[
              const SizedBox(height: 12),
              SizedBox(
                height: 150,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: message.message.metadata.length,
                  separatorBuilder: (_, _) => const SizedBox(width: 8),
                  itemBuilder: (_, index) {
                    final recommendation = message.message.metadata[index];
                    return SizedBox(
                      width: 140,
                      child: InkWell(
                        onTap: () =>
                            _openRecommendation(recommendation.productId),
                        borderRadius: BorderRadius.circular(10),
                        child: Card(
                          margin: EdgeInsets.zero,
                          clipBehavior: Clip.antiAlias,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              SizedBox(
                                height: 92,
                                width: double.infinity,
                                child: ProductImage(
                                  imageUrl: recommendation.imageUrl,
                                  borderRadius: BorderRadius.zero,
                                ),
                              ),
                              Padding(
                                padding: const EdgeInsets.all(8),
                                child: Text(
                                  recommendation.name,
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],
            if (message.state == ChatbotMessageState.sending)
              const Padding(
                padding: EdgeInsets.only(top: 4),
                child: Text('Enviando...', style: TextStyle(fontSize: 12)),
              ),
            if (message.state == ChatbotMessageState.error)
              TextButton(
                onPressed: _sending ? null : () => _retry(message),
                child: const Text('Reintentar'),
              ),
          ],
        ),
      ),
    );
  }

  Widget _composer() {
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: TextField(
                controller: _inputController,
                minLines: 1,
                maxLines: 4,
                enabled: !_sending && !_resetting,
                textInputAction: TextInputAction.newline,
                decoration: const InputDecoration(
                  hintText: 'Escribe tu mensaje...',
                ),
              ),
            ),
            IconButton(
              tooltip: 'Enviar mensaje',
              onPressed: _sending || _resetting
                  ? null
                  : () => unawaited(_send()),
              icon: _sending
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.send),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _loadMessages() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final messages = await widget.api.getMessages();
      messages.sort((a, b) => a.createdAt.compareTo(b.createdAt));
      if (!mounted) return;
      setState(() => _messages = messages.map(_UiMessage.normal).toList());
      _scrollToLatest();
    } catch (_) {
      if (mounted)
        setState(() => _error = 'No se pudo cargar la conversación.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _send([String? retryContent]) async {
    final content = (retryContent ?? _inputController.text).trim();
    if (content.isEmpty || _sending || _resetting) return;

    final optimistic = _UiMessage(
      message: ChatbotMessage(
        id: 'pending-${DateTime.now().microsecondsSinceEpoch}',
        role: ChatbotMessageRole.user,
        content: content,
        createdAt: DateTime.now().toUtc(),
      ),
      state: ChatbotMessageState.sending,
    );
    setState(() {
      _messages = [..._messages, optimistic];
      _inputController.clear();
      _error = null;
      _sending = true;
    });
    _scrollToLatest();

    try {
      final messages = await widget.api.sendMessage(content);
      messages.sort((a, b) => a.createdAt.compareTo(b.createdAt));
      if (mounted)
        setState(() => _messages = messages.map(_UiMessage.normal).toList());
    } catch (_) {
      if (mounted) {
        setState(() {
          _messages = _messages
              .map(
                (item) => item.message.id == optimistic.message.id
                    ? item.copyWith(state: ChatbotMessageState.error)
                    : item,
              )
              .toList();
          _error = 'No se pudo enviar el mensaje. Intenta de nuevo.';
        });
      }
    } finally {
      if (mounted) {
        setState(() => _sending = false);
        _scrollToLatest();
      }
    }
  }

  void _retry(_UiMessage message) {
    setState(() {
      _messages = _messages
          .where((item) => item.message.id != message.message.id)
          .toList();
    });
    unawaited(_send(message.message.content));
  }

  Future<void> _confirmReset() async {
    final confirmed = await AppDialog.show<bool>(
      context: context,
      title: '¿Borrar conversación?',
      content: const Text(
        'Se eliminarán todos los mensajes de este asistente.',
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(false),
          child: const Text('Cancelar'),
        ),
        FilledButton(
          onPressed: () => Navigator.of(context).pop(true),
          child: const Text('Borrar'),
        ),
      ],
    );
    if (confirmed != true || !mounted || _sending || _resetting) return;

    setState(() {
      _resetting = true;
      _error = null;
    });
    try {
      await widget.api.deleteConversation();
      if (mounted) setState(() => _messages = []);
    } catch (_) {
      if (mounted)
        setState(() => _error = 'No se pudo borrar la conversación.');
    } finally {
      if (mounted) setState(() => _resetting = false);
    }
  }

  Future<void> _openRecommendation(String productId) async {
    Navigator.of(context).pop();
    await widget.onOpenProduct(productId);
  }

  void _scrollToLatest() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 180),
        curve: Curves.easeOut,
      );
    });
  }
}

class _UiMessage {
  const _UiMessage({required this.message, required this.state});

  _UiMessage.normal(ChatbotMessage message)
    : this(message: message, state: ChatbotMessageState.normal);

  final ChatbotMessage message;
  final ChatbotMessageState state;

  _UiMessage copyWith({ChatbotMessageState? state}) {
    return _UiMessage(message: message, state: state ?? this.state);
  }
}
