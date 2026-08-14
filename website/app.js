/* ARRAY-7 observation terminal — present & download only, no analysis */

const catalogUrl = "data/catalog.json";

const els = {
  select: document.getElementById("obs-select"),
  status: document.getElementById("status-badge"),
  play: document.getElementById("play-btn"),
  download: document.getElementById("download-btn"),
  title: document.getElementById("obs-title"),
  meta: document.getElementById("obs-meta"),
  canvas: document.getElementById("wave"),
  clock: document.getElementById("utc-clock"),
};

let catalog = null;
let drawToken = 0;
let currentSamples = null;
let currentFs = 8000;
let audioCtx = null;
let audioSource = null;
let audioGain = null;
let playT0 = 0;
let playRaf = 0;

function tickClock() {
  const now = new Date();
  els.clock.textContent = now.toISOString().slice(11, 19) + "Z";
}

/** Minimal NumPy .npy reader (C-order float32/float64 1-D or flat). */
async function loadNpy(url) {
  const buf = await fetch(url).then((r) => {
    if (!r.ok) throw new Error(`Failed to fetch ${url}`);
    return r.arrayBuffer();
  });
  const view = new DataView(buf);
  const magic = String.fromCharCode(view.getUint8(0), view.getUint8(1), view.getUint8(2), view.getUint8(3), view.getUint8(4), view.getUint8(5));
  if (magic !== "\x93NUMPY") throw new Error("Not a .npy file");

  const major = view.getUint8(6);
  let headerLen;
  let offset;
  if (major === 1) {
    headerLen = view.getUint16(8, true);
    offset = 10 + headerLen;
  } else {
    headerLen = view.getUint32(8, true);
    offset = 12 + headerLen;
  }
  const header = new TextDecoder().decode(new Uint8Array(buf, major === 1 ? 10 : 12, headerLen));
  const descr = /'descr':\s*'([^']+)'/.exec(header)?.[1];
  const fortran = /'fortran_order':\s*(True|False)/.exec(header)?.[1] === "True";
  if (fortran) throw new Error("Fortran-order arrays not supported");

  const little = descr?.startsWith("<") || descr?.startsWith("|");
  const dtype = descr?.slice(1);
  const n = (buf.byteLength - offset) / (dtype === "f8" ? 8 : 4);
  const out = new Float64Array(n);
  if (dtype === "f8") {
    for (let i = 0; i < n; i++) out[i] = view.getFloat64(offset + i * 8, little);
  } else if (dtype === "f4") {
    for (let i = 0; i < n; i++) out[i] = view.getFloat32(offset + i * 4, little);
  } else {
    throw new Error(`Unsupported dtype ${descr}`);
  }
  return out;
}

function downsample(arr, maxPoints) {
  if (arr.length <= maxPoints) return arr;
  const out = new Float64Array(maxPoints);
  const step = arr.length / maxPoints;
  for (let i = 0; i < maxPoints; i++) {
    const start = Math.floor(i * step);
    const end = Math.floor((i + 1) * step);
    let min = Infinity;
    let max = -Infinity;
    for (let j = start; j < end; j++) {
      const v = arr[j];
      if (v < min) min = v;
      if (v > max) max = v;
    }
    // alternate min/max to preserve envelope
    out[i] = i % 2 === 0 ? min : max;
  }
  return out;
}

function drawWaveform(samples, playhead) {
  const canvas = els.canvas;
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const cssW = canvas.clientWidth || 1200;
  const cssH = 360;
  canvas.width = Math.floor(cssW * dpr);
  canvas.height = Math.floor(cssH * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  ctx.clearRect(0, 0, cssW, cssH);
  ctx.fillStyle = "#040a0d";
  ctx.fillRect(0, 0, cssW, cssH);

  const data = downsample(samples, Math.min(1800, Math.floor(cssW)));
  let min = Infinity;
  let max = -Infinity;
  for (let i = 0; i < data.length; i++) {
    if (data[i] < min) min = data[i];
    if (data[i] > max) max = data[i];
  }
  const pad = (max - min) * 0.08 || 1;
  min -= pad;
  max += pad;

  const mid = cssH / 2;
  ctx.strokeStyle = "rgba(61,255,168,0.15)";
  ctx.beginPath();
  ctx.moveTo(0, mid);
  ctx.lineTo(cssW, mid);
  ctx.stroke();

  ctx.strokeStyle = "#3dffa8";
  ctx.lineWidth = 1.25;
  ctx.beginPath();
  for (let i = 0; i < data.length; i++) {
    const x = (i / (data.length - 1)) * cssW;
    const y = cssH - ((data[i] - min) / (max - min)) * cssH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();

  if (playhead != null) {
    const x = playhead * cssW;
    ctx.strokeStyle = "#e8b84a";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, cssH);
    ctx.stroke();
  }
}

function setPlayUi(playing) {
  if (!els.play) return;
  els.play.textContent = playing ? "Stop listen" : "Listen to source";
  els.play.classList.toggle("is-playing", playing);
  els.play.setAttribute("aria-pressed", playing ? "true" : "false");
}

function stopAudio() {
  if (playRaf) {
    cancelAnimationFrame(playRaf);
    playRaf = 0;
  }
  if (audioSource) {
    try {
      audioSource.stop();
    } catch {
      /* already stopped */
    }
    audioSource.disconnect();
    audioSource = null;
  }
  if (audioGain) {
    audioGain.disconnect();
    audioGain = null;
  }
  setPlayUi(false);
}

function resampleLinear(src, srcRate, dstRate) {
  if (Math.abs(srcRate - dstRate) < 1e-6) return src;
  const nOut = Math.max(1, Math.round((src.length * dstRate) / srcRate));
  const out = new Float32Array(nOut);
  const ratio = (src.length - 1) / Math.max(1, nOut - 1);
  for (let i = 0; i < nOut; i++) {
    const x = i * ratio;
    const i0 = Math.min(src.length - 1, Math.floor(x));
    const i1 = Math.min(src.length - 1, i0 + 1);
    const t = x - i0;
    out[i] = src[i0] * (1 - t) + src[i1] * t;
  }
  return out;
}

function prepareAudio(samples, srcRate, dstRate) {
  let mean = 0;
  for (let i = 0; i < samples.length; i++) mean += samples[i];
  mean /= samples.length || 1;
  const centered = new Float32Array(samples.length);
  let peak = 0;
  for (let i = 0; i < samples.length; i++) {
    const v = samples[i] - mean;
    centered[i] = v;
    const a = Math.abs(v);
    if (a > peak) peak = a;
  }
  const g = peak > 1e-9 ? 0.85 / peak : 0;
  for (let i = 0; i < centered.length; i++) centered[i] *= g;
  return resampleLinear(centered, srcRate, dstRate);
}

function tickPlayhead() {
  if (!audioSource || !audioCtx || !currentSamples) return;
  const dur = currentSamples.length / (Number(currentFs) || 8000);
  const t = ((audioCtx.currentTime - playT0) % dur) / dur;
  drawWaveform(currentSamples, t);
  playRaf = requestAnimationFrame(tickPlayhead);
}

async function togglePlay() {
  if (audioSource) {
    stopAudio();
    if (currentSamples) drawWaveform(currentSamples);
    return;
  }
  if (!currentSamples || !currentSamples.length) return;

  const Ctx = window.AudioContext || window.webkitAudioContext;
  if (!Ctx) {
    els.play.disabled = true;
    els.play.textContent = "Audio unavailable";
    return;
  }
  if (!audioCtx) audioCtx = new Ctx();
  if (audioCtx.state === "suspended") await audioCtx.resume();

  const srcRate = Number(currentFs) || 8000;
  const data = prepareAudio(currentSamples, srcRate, audioCtx.sampleRate);
  const buffer = audioCtx.createBuffer(1, data.length, audioCtx.sampleRate);
  buffer.getChannelData(0).set(data);

  const gain = audioCtx.createGain();
  gain.gain.value = 0.55;
  const source = audioCtx.createBufferSource();
  source.buffer = buffer;
  source.loop = true;
  source.connect(gain);
  gain.connect(audioCtx.destination);

  audioGain = gain;
  audioSource = source;
  playT0 = audioCtx.currentTime;
  setPlayUi(true);
  source.start();
  tickPlayhead();
}

async function showObservation(entry) {
  const token = ++drawToken;
  stopAudio();
  currentSamples = null;
  els.play.disabled = true;
  setPlayUi(false);
  els.title.textContent = entry.label || entry.id;
  els.meta.textContent = "loading…";
  els.status.textContent = "UNCLASSIFIED";
  els.download.href = entry.npy;
  els.download.setAttribute("download", `${entry.id}.npy`);
  els.download.classList.remove("is-disabled");

  const [meta, samples] = await Promise.all([
    fetch(entry.meta).then((r) => r.json()),
    loadNpy(entry.npy),
  ]);
  if (token !== drawToken) return;

  const fs = meta.fs ?? 8000;
  const n = meta.n_samples ?? samples.length;
  const round = meta.round ?? entry.round ?? "—";
  els.status.textContent = meta.status || "UNCLASSIFIED";
  els.meta.textContent = `fs ${fs} Hz · n ${n} · round ${round}`;
  currentSamples = samples;
  currentFs = fs;
  els.play.disabled = false;
  drawWaveform(samples);
}

function releasedOnly(list) {
  const params = new URLSearchParams(location.search);
  if (params.get("all") === "1") return list;
  return list.filter((o) => o.released !== false);
}

async function init() {
  tickClock();
  setInterval(tickClock, 1000);

  catalog = await fetch(catalogUrl).then((r) => r.json());
  const items = releasedOnly(catalog.observations || []).sort((a, b) => a.round - b.round);

  els.select.innerHTML = "";
  if (!items.length) {
    els.title.textContent = "NO RELEASED OBSERVATIONS";
    els.meta.textContent = "Awaiting desk release";
    els.download.classList.add("is-disabled");
    els.play.disabled = true;
    return;
  }

  for (const o of items) {
    const opt = document.createElement("option");
    opt.value = o.id;
    opt.textContent = `${o.label || o.id}  ·  round ${o.round}`;
    els.select.appendChild(opt);
  }

  els.select.addEventListener("change", () => {
    const entry = items.find((o) => o.id === els.select.value);
    if (entry) showObservation(entry);
  });

  els.play.addEventListener("click", () => {
    togglePlay().catch((err) => {
      console.error(err);
      stopAudio();
      els.meta.textContent = String(err.message || err);
    });
  });

  window.addEventListener("resize", () => {
    if (currentSamples) drawWaveform(currentSamples);
  });

  await showObservation(items[0]);
}

init().catch((err) => {
  console.error(err);
  els.title.textContent = "TERMINAL FAULT";
  els.meta.textContent = String(err.message || err);
});
