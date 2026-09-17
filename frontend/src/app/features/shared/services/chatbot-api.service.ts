import { Injectable, inject } from '@angular/core';

import { ApiResponse } from '../../../core/models/api.model';
import { ApiService } from '../../../core/services/api.service';

export type ChatbotMessageRole = 'user' | 'assistant';

export interface ChatbotRecommendation {
  variant_id: string;
  product_id: string;
  name: string;
  description?: string | null;
  image_url?: string | null;
  sku?: string | null;
  price?: string | number | null;
  size_name?: string | null;
  color_name?: string | null;
  available_quantity?: number | null;
}

export interface ChatbotMessage {
  id: string;
  role: ChatbotMessageRole;
  content: string;
  created_at: string;
  metadata: ChatbotRecommendation[] | null;
}

@Injectable({ providedIn: 'root' })
export class ChatbotApiService {
  private readonly api = inject(ApiService);

  sendMessage(message: string) {
    return this.api.post<ApiResponse<void>>('/chatbot/message', { message });
  }

  getMessages() {
    return this.api.get<ApiResponse<ChatbotMessage[]>>('/chatbot/messages');
  }

  resetConversation() {
    return this.api.delete<ApiResponse<void>>('/chatbot/conversation');
  }
}
