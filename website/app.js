/* ARRAY-7 observation terminal — present & download only, no analysis */

const catalogUrl = "data/catalog.json";

const els = {
  select: document.getElementById("obs-select"),
  status: document.getElementById("status-badge"),
  download: document.getElementById("download-btn"),
  title: document.getElementById("obs-title"),
  meta: document.getElementById("obs-meta"),
  canvas: document.getElementById("wave"),
  clock: document.getElementById("utc-clock"),
};

let catalog = null;
let drawToken = 0;

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

function drawWaveform(samples) {
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
}

async function showObservation(entry) {
  const token = ++drawToken;
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

  const fs = meta.fs ?? "—";
  const n = meta.n_samples ?? samples.length;
  const round = meta.round ?? entry.round ?? "—";
  els.status.textContent = meta.status || "UNCLASSIFIED";
  els.meta.textContent = `fs ${fs} Hz · n ${n} · round ${round}`;
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

  window.addEventListener("resize", () => {
    const entry = items.find((o) => o.id === els.select.value);
    if (entry) showObservation(entry);
  });

  await showObservation(items[0]);
}

init().catch((err) => {
  console.error(err);
  els.title.textContent = "TERMINAL FAULT";
  els.meta.textContent = String(err.message || err);
});
