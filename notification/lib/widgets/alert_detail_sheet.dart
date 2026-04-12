import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:video_player/video_player.dart';
import 'package:chewie/chewie.dart';
import '../models/alert_model.dart';

class AlertDetailSheet extends StatefulWidget {
  final SecurityAlert alert;
  const AlertDetailSheet({super.key, required this.alert});

  @override
  State<AlertDetailSheet> createState() => _AlertDetailSheetState();
}

class _AlertDetailSheetState extends State<AlertDetailSheet> {
  VideoPlayerController? _videoController;
  ChewieController? _chewieController;

  Color get _threatColor => switch (widget.alert.threatLevel) {
    'HIGH' => const Color(0xFFFF4444),
    'MEDIUM' => const Color(0xFFFF9800),
    _ => const Color(0xFFFFEB3B),
  };

  @override
  void initState() {
    super.initState();
    if (widget.alert.videoUrl != null) {
      _initVideo();
    }
  }

  Future<void> _initVideo() async {
    _videoController = VideoPlayerController.networkUrl(
        Uri.parse(widget.alert.videoUrl!));
    await _videoController!.initialize();
    _chewieController = ChewieController(
      videoPlayerController: _videoController!,
      aspectRatio: 16 / 9,
      autoPlay: true,
      looping: true,
      showControls: true,
    );
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.9,
      maxChildSize: 0.95,
      minChildSize: 0.5,
      builder: (_, scrollController) => Container(
        decoration: const BoxDecoration(
          color: Color(0xFF0E0E18),
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        child: ListView(
          controller: scrollController,
          padding: EdgeInsets.zero,
          children: [
            // Drag handle
            Center(
              child: Container(
                margin: const EdgeInsets.only(top: 12, bottom: 8),
                width: 36,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),

            // Header
            Padding(
              padding:
              const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 12, vertical: 5),
                    decoration: BoxDecoration(
                      color: _threatColor.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                          color: _threatColor.withOpacity(0.4)),
                    ),
                    child: Text('⚠ ${widget.alert.threatLevel} THREAT',
                        style: TextStyle(
                            color: _threatColor,
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                            letterSpacing: 1)),
                  ),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.close, color: Colors.white54),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
            ),

            // Video player
            if (_chewieController != null)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(16),
                  child: AspectRatio(
                    aspectRatio: 16 / 9,
                    child: Chewie(controller: _chewieController!),
                  ),
                ),
              )
            else if (widget.alert.videoUrl != null)
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 20),
                height: 200,
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Center(
                  child: CircularProgressIndicator(
                      color: Color(0xFFFF4444)),
                ),
              )
            else
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 20),
                height: 180,
                decoration: BoxDecoration(
                  color: const Color(0xFF1A1A2A),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Center(
                  child: Icon(Icons.videocam_off_rounded,
                      size: 48,
                      color: Colors.white.withOpacity(0.2)),
                ),
              ),

            const SizedBox(height: 24),

            // Info rows
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                children: [
                  _InfoRow(
                    icon: Icons.location_on_rounded,
                    label: 'Location',
                    value: widget.alert.location,
                    color: _threatColor,
                  ),
                  _InfoRow(
                    icon: Icons.access_time_rounded,
                    label: 'Detected at',
                    value: DateFormat('MMM dd, yyyy • HH:mm:ss')
                        .format(widget.alert.timestamp),
                    color: _threatColor,
                  ),
                  _InfoRow(
                    icon: Icons.description_rounded,
                    label: 'Description',
                    value: widget.alert.description,
                    color: _threatColor,
                  ),
                  if (widget.alert.latitude != null)
                    _InfoRow(
                      icon: Icons.my_location_rounded,
                      label: 'Coordinates',
                      value:
                      '${widget.alert.latitude!.toStringAsFixed(6)}, ${widget.alert.longitude!.toStringAsFixed(6)}',
                      color: _threatColor,
                    ),
                ],
              ),
            ),

            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _videoController?.dispose();
    _chewieController?.dispose();
    super.dispose();
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF16162A),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.06)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 18),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label,
                    style: TextStyle(
                        color: Colors.white.withOpacity(0.4),
                        fontSize: 11,
                        letterSpacing: 0.5)),
                const SizedBox(height: 3),
                Text(value,
                    style: const TextStyle(
                        color: Colors.white, fontSize: 14)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}