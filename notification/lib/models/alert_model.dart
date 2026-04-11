class SecurityAlert {
  final String id;
  final DateTime timestamp;
  final String location;
  final String threatLevel;
  final String description;
  final String? videoUrl;
  final double? latitude;
  final double? longitude;

  SecurityAlert({
    required this.id,
    required this.timestamp,
    required this.location,
    required this.threatLevel,
    required this.description,
    this.videoUrl,
    this.latitude,
    this.longitude,
  });

  factory SecurityAlert.fromMap(Map<String, dynamic> data) {
    return SecurityAlert(
      id: data['id'] ?? '',
      timestamp: data['timestamp'] != null
          ? DateTime.parse(data['timestamp'])
          : DateTime.now(),
      location: data['location'] ?? 'Unknown',
      threatLevel: data['threat_level'] ?? 'HIGH',
      description: data['description'] ?? '',
      videoUrl: data['video_url']?.isNotEmpty == true ? data['video_url'] : null,
      latitude: data['lat']?.isNotEmpty == true ? double.tryParse(data['lat']) : null,
      longitude: data['lng']?.isNotEmpty == true ? double.tryParse(data['lng']) : null,
    );
  }
}