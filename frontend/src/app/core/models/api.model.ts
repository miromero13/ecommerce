export interface ApiResponse<T> {
  statusCode: number;
  message: string;
  data?: T;
  countData?: number;
  error?: unknown;
}
