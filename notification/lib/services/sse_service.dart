import 'dart:async';
import 'dart:convert';
import 'package:flutter_client_sse/flutter_client_sse.dart';
import 'package:flutter_client_sse/constants/sse_request_type_enum.dart';
import '../models/alert_model.dart';

class SSEService {
  static const String baseUrl = 'http://localhost:8000'; // your Mac's IP, no trailing slash

  static StreamController<SecurityAlert>? _controller;
  static StreamSubscription? _subscription;

  static Stream<SecurityAlert> get alertStream {
    _controller ??= StreamController<SecurityAlert>.broadcast();
    return _controller!.stream;
  }

  static void connect() {
    _subscription = SSEClient.subscribeToSSE(
      method: SSERequestType.GET,
      url: '$baseUrl/alerts/stream', // no double slash now
      header: {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
    ).listen(
          (event) {
        if (event.event == 'threat' && event.data != null) {
          try {
            final data = jsonDecode(event.data!);
            final alert = SecurityAlert.fromMap(data);
            _controller?.add(alert);
          } catch (e) {
            print('SSE parse error: $e');
          }
        }
      },
      onError: (error) {
        print('SSE error: $error — retrying in 5s');
        Future.delayed(const Duration(seconds: 5), connect);
      },
    );
  }

  static void disconnect() {
    _subscription?.cancel();
    _controller?.close();
    _controller = null;
  }
}