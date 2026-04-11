from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv
import socket, os

load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()

PHONE_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CampusGuard Camera</title>
  <style>
    body { margin:0; background:#111; display:flex; flex-direction:column;
           align-items:center; justify-content:center; height:100vh; font-family:sans-serif; }
    h2 { color:#fff; }
    video { width:100%; max-width:480px; border-radius:8px; }
    #status { color:lime; margin-top:12px; font-size:1em; }
  </style>
</head>
<body>
  <h2>CampusGuard Camera</h2>
  <video id="video" autoplay playsinline muted></video>
  <p id="status">Waiting...</p>
  <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
  <script>
    const socket = io({ transports: ['websocket'] });
    const status = document.getElementById('status');
    const video  = document.getElementById('video');
    const pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] });

    navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: 1280, height: 720 }, audio: false
    }).then(stream => {
      video.srcObject = stream;
      stream.getTracks().forEach(track => pc.addTrack(track, stream));
      status.textContent = 'Camera ready. Waiting for viewer...';
    }).catch(err => { status.textContent = 'Camera error: ' + err; status.style.color='red'; });

    socket.on('viewer_ready', async () => {
      status.textContent = 'Viewer connected!';
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      socket.emit('offer', offer);
    });

    socket.on('answer', async (answer) => {
      await pc.setRemoteDescription(new RTCSessionDescription(answer));
      status.textContent = 'Streaming live!';
    });

    socket.on('ice_candidate', async ({ candidate }) => {
      try { await pc.addIceCandidate(new RTCIceCandidate(candidate)); } catch(e) {}
    });

    pc.onicecandidate = ({ candidate }) => {
      if (candidate) socket.emit('phone_ice', { candidate });
    };
  </script>
</body>
</html>
"""

VIEW_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>CampusGuard Live Feed</title>
  <style>
    * { box-sizing: border-box; margin:0; padding:0; }
    body { background:#000; display:flex; flex-direction:column;
           align-items:center; justify-content:center; height:100vh; font-family:monospace; }

    .cam-wrapper { position:relative; width:100%; max-width:900px; }

    video { width:100%; display:block; }

    /* Top bar */
    .overlay-top {
      position:absolute; top:0; left:0; right:0;
      padding:8px 14px;
      background:linear-gradient(to bottom, rgba(0,0,0,0.75), transparent);
      display:flex; justify-content:space-between; align-items:center;
    }
    .cam-name { color:#fff; font-size:0.95em; font-weight:bold; letter-spacing:1px; }
    .cam-location { color:#bbb; font-size:0.8em; }

    /* Bottom bar */
    .overlay-bottom {
      position:absolute; bottom:0; left:0; right:0;
      padding:8px 14px;
      background:linear-gradient(to top, rgba(0,0,0,0.75), transparent);
      display:flex; justify-content:space-between; align-items:center;
    }
    .timestamp { color:#fff; font-size:0.9em; letter-spacing:1px; }
    .persons   { color:#00ff00; font-size:0.85em; }

    /* REC dot */
    .rec { display:flex; align-items:center; gap:6px; color:#ff3333; font-size:0.85em; font-weight:bold; }
    .rec-dot { width:10px; height:10px; border-radius:50%; background:#ff3333;
               animation: blink 1s infinite; }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

    #conn-status { color:gray; font-size:0.8em; margin-top:8px; }
  </style>
</head>
<body>
  <div class="cam-wrapper">
    <video id="feed" autoplay playsinline muted></video>

    <div class="overlay-top">
      <div>
        <div class="cam-name">CAM 03 — HALLWAY B</div>
        <div class="cam-location">John Abbott College — Building H</div>
      </div>
      <div class="rec"><div class="rec-dot"></div>REC</div>
    </div>

    <div class="overlay-bottom">
      <div class="timestamp" id="timestamp">--:--:--</div>
      <div class="persons" id="persons">LIVE</div>
    </div>
  </div>
  <p id="conn-status">Connecting...</p>

  <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
  <script>
    // Live timestamp
    function updateTime() {
      const now = new Date();
      const date = now.toLocaleDateString('en-CA'); // YYYY-MM-DD
      const time = now.toTimeString().split(' ')[0];
      document.getElementById('timestamp').textContent = date + '  ' + time;
    }
    setInterval(updateTime, 1000);
    updateTime();

    // WebRTC
    const socket = io({ transports: ['websocket'] });
    const feed   = document.getElementById('feed');
    const conn   = document.getElementById('conn-status');
    const pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] });

    pc.ontrack = (e) => {
      feed.srcObject = e.streams[0];
      conn.textContent = '';
      document.getElementById('persons').textContent = 'LIVE';
    };

    pc.onicecandidate = ({ candidate }) => {
      if (candidate) socket.emit('viewer_ice', { candidate });
    };

    socket.on('connect', () => {
      conn.textContent = 'Connected. Waiting for phone...';
      socket.emit('viewer_ready');
    });

    socket.on('offer', async (offer) => {
      await pc.setRemoteDescription(new RTCSessionDescription(offer));
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);
      socket.emit('answer', answer);
    });

    socket.on('ice_candidate', async ({ candidate }) => {
      try { await pc.addIceCandidate(new RTCIceCandidate(candidate)); } catch(e) {}
    });
  </script>
</body>
</html>
"""

@socketio.on('viewer_ready')
def on_viewer_ready():
    socketio.emit('viewer_ready')

@socketio.on('offer')
def on_offer(data):
    socketio.emit('offer', data)

@socketio.on('answer')
def on_answer(data):
    socketio.emit('answer', data)

@socketio.on('phone_ice')
def on_phone_ice(data):
    socketio.emit('ice_candidate', data)

@socketio.on('viewer_ice')
def on_viewer_ice(data):
    socketio.emit('ice_candidate', data)

@app.route('/')
def index():
    return PHONE_PAGE

@app.route('/view')
def view():
    return VIEW_PAGE

if __name__ == '__main__':
    print(f"\n CampusGuard — Live Camera")
    print(f" Phone  → open ngrok HTTPS URL in phone browser")
    print(f" Viewer → http://localhost:5000/view\n")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
