import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const SecurityCamApp());
}

class SecurityCamApp extends StatelessWidget {
  const SecurityCamApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SecureEye',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFFF4444),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFF0A0A0F),
      ),
      home: const HomeScreen(),
    );
  }
}