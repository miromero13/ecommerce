class ApiResponse<T> {
  const ApiResponse({
    required this.statusCode,
    required this.message,
    this.data,
    this.error,
    this.countData,
  });

  final int statusCode;
  final String message;
  final T? data;
  final dynamic error;
  final int? countData;

  factory ApiResponse.fromJson(
    Map<String, dynamic> json, {
    T Function(dynamic value)? parser,
  }) {
    final rawData = json['data'];

    return ApiResponse(
      statusCode: (json['statusCode'] as num?)?.toInt() ?? 0,
      message: json['message']?.toString() ?? '',
      data: rawData == null
          ? null
          : parser == null
          ? rawData as T
          : parser(rawData),
      error: json['error'],
      countData: (json['countData'] as num?)?.toInt(),
    );
  }
}
