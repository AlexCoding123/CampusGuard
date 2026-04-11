import 'dart:async';
import 'package:flutter/material.dart';
import '../models/alert_model.dart';
import '../services/sse_service.dart';
import '../widgets/alert_card.dart';
import '../widgets/alert_detail_sheet.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with TickerProviderStateMixin {
  final List<SecurityAlert> _alerts = [];
  late AnimationController _pulseController;
  StreamSubscription? _alertSubscription;
  bool _connected = false;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);

    _connectSSE();
  }

  void _connectSSE() {
    SSEService.connect();
    setState(() => _connected = true);

    _alertSubscription = SSEService.alertStream.listen((alert) {
      setState(() => _alerts.insert(0, alert));
      _showInAppAlert(alert);
    });
  }

  void _showInAppAlert(SecurityAlert alert) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        content: GestureDetector(
          onTap: () {
            ScaffoldMessenger.of(context).hideCurrentSnackBar();
            _openAlertDetail(alert);
          },
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF1A0A0A),
              border: Border.all(color: const Color(0xFFFF4444), width: 1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                const Icon(Icons.warning_rounded, color: Color(0xFFFF4444)),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text('THREAT DETECTED',
                          style: TextStyle(
                              color: Color(0xFFFF4444),
                              fontWeight: FontWeight.bold,
                              fontSize: 11,
                              letterSpacing: 1.5)),
                      Text(alert.location,
                          style: const TextStyle(color: Colors.white)),
                    ],
                  ),
                ),
                const Text('VIEW',
                    style: TextStyle(
                        color: Color(0xFFFF4444),
                        fontWeight: FontWeight.bold,
                        fontSize: 11,
                        letterSpacing: 1)),
              ],
            ),
          ),
        ),
        duration: const Duration(seconds: 6),
      ),
    );
  }

  void _openAlertDetail(SecurityAlert alert) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => AlertDetailSheet(alert: alert),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 140,
            pinned: true,
            backgroundColor: const Color(0xFF0A0A0F),
            flexibleSpace: FlexibleSpaceBar(
              title: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  AnimatedBuilder(
                    animation: _pulseController,
                    builder: (_, __) => Container(
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Color.lerp(
                          _connected
                              ? const Color(0xFF44FF44)
                              : const Color(0xFFFF4444),
                          _connected
                              ? const Color(0xFF88FF88)
                              : const Color(0xFFFF8888),
                          _pulseController.value,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  const Text('SecureEye',
                      style: TextStyle(
                          fontWeight: FontWeight.bold, letterSpacing: 1)),
                ],
              ),
              background: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [Color(0xFF1A0010), Color(0xFF0A0A0F)],
                  ),
                ),
              ),
            ),
          ),
          if (_alerts.isEmpty)
            const SliverFillRemaining(child: _EmptyState())
          else
            SliverPadding(
              padding: const EdgeInsets.all(16),
              sliver: SliverList(
                delegate: SliverChildBuilderDelegate(
                      (context, i) => AlertCard(
                    alert: _alerts[i],
                    onTap: () => _openAlertDetail(_alerts[i]),
                  ),
                  childCount: _alerts.length,
                ),
              ),
            ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _alertSubscription?.cancel();
    SSEService.disconnect();
    super.dispose();
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.shield_outlined,
              size: 72, color: Colors.white.withOpacity(0.15)),
          const SizedBox(height: 16),
          Text('All clear',
              style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: Colors.white.withOpacity(0.4))),
          const SizedBox(height: 8),
          Text('Monitoring active',
              style: TextStyle(color: Colors.white.withOpacity(0.25))),
        ],
      ),
    );
  }
}