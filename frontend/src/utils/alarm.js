let ctx = null;
let decodedBuffer = null;

function getContext() {
  if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
  return ctx;
}

// Decode on load — no gesture needed for this step
fetch(process.env.PUBLIC_URL + "/alarm.mp3")
  .then((r) => r.arrayBuffer())
  .then((buf) => getContext().decodeAudioData(buf))
  .then((decoded) => { decodedBuffer = decoded; })
  .catch((err) => console.warn("[Alarm] preload failed:", err));

export function unlockAudio() {
  try {
    const c = getContext();
    if (c.state !== "suspended") return;
    c.resume().then(() => {
      const buf = c.createBuffer(1, 1, 22050);
      const src = c.createBufferSource();
      src.buffer = buf;
      src.loop = true;
      src.connect(c.destination);
      src.start();
    });
  } catch (err) {}
}

export function playAlarm() {
  try {
    const c = getContext();
    const doPlay = () => {
      if (!decodedBuffer) return;
      const src = c.createBufferSource();
      src.buffer = decodedBuffer;
      src.connect(c.destination);
      src.start(0);
    };
    c.state === "suspended" ? c.resume().then(doPlay) : doPlay();
  } catch (err) {}
}

export function isUnlocked() {
  return ctx && ctx.state === "running";
}
