import { Observable, firstValueFrom } from 'rxjs';

import { toast } from '@spartan-ng/brain/sonner';

import { getErrorMessage } from './http-error.util';

export interface RequestToastMessages {
  loading: string;
  success: string;
  error: string;
}

export function requestWithToast<T>(operation: Observable<T>, messages: RequestToastMessages): Promise<T> {
  const request = firstValueFrom(operation);
  toast.promise(request, {
    loading: messages.loading,
    success: messages.success,
    error: (error) => getErrorMessage(error, messages.error),
  });
  return request;
}