import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/alert_model.dart';

class AlertCard extends StatelessWidget {
  final SecurityAlert alert;
  final VoidCallback onTap;

  const AlertCard({super.key, required this.alert, required this.onTap});

  Color get _threatColor => switch (alert.threatLevel) {
    'HIGH' => const Color(0xFFFF4444),
    'MEDIUM' => const Color(0xFFFF9800),
    _ => const Color(0xFFFFEB3B),
  };

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: const Color(0xFF12121A),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: _threatColor.withOpacity(0.3)),
        ),
        child: Column(
          children: [
            Container(
              height: 3,
              decoration: BoxDecoration(
                color: _threatColor,
                borderRadius:
                const BorderRadius.vertical(top: Radius.circular(16)),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Container(
                    width: 60,
                    height: 60,
                    decoration: BoxDecoration(
                      color: _threatColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(10),
                      border:
                      Border.all(color: _threatColor.withOpacity(0.4)),
                    ),
                    child: Icon(Icons.videocam_rounded,
                        color: _threatColor, size: 28),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: _threatColor.withOpacity(0.15),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(alert.threatLevel,
                                  style: TextStyle(
                                      color: _threatColor,
                                      fontSize: 10,
                                      fontWeight: FontWeight.bold,
                                      letterSpacing: 1)),
                            ),
                            const Spacer(),
                            Text(
                              DateFormat('HH:mm').format(alert.timestamp),
                              style: TextStyle(
                                  color: Colors.white.withOpacity(0.4),
                                  fontSize: 12),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Text(alert.location,
                            style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w600)),
                        const SizedBox(height: 4),
                        Text(alert.description,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                                color: Colors.white.withOpacity(0.5),
                                fontSize: 12)),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  Icon(Icons.chevron_right,
                      color: Colors.white.withOpacity(0.3)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}