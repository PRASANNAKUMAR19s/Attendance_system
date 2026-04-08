/**
 * camera.js — 13-angle face photo capture
 * =========================================
 * Provides live camera feed and one-click capture for each of the
 * 13 predefined face angles used to train the LBPH recognition model.
 *
 * Captured frames are stored as Blob objects in `capturedPhotos[]`
 * and also appended as hidden <input type="file"> entries on the
 * registration form so they are submitted with the form data.
 *
 * When a register number is known (field #reg_no is filled) photos
 * can also be POSTed immediately to the server via the upload endpoint.
 */

"use strict";

/* ── Configuration ────────────────────────────────────────────────── */
const ANGLE_LABELS = [
  "Front",
  "Left 15°",
  "Left 30°",
  "Left 45°",
  "Right 15°",
  "Right 30°",
  "Right 45°",
  "Up 15°",
  "Up 30°",
  "Down 15°",
  "Down 30°",
  "Up-Left",
  "Up-Right",
];

/* ── State ────────────────────────────────────────────────────────── */
let stream       = null;
let capturedPhotos = [];   // Array of { blob, angle }
const MAX_PHOTOS = typeof PHOTOS_REQUIRED !== "undefined" ? PHOTOS_REQUIRED : 13;

/* ── DOM references ───────────────────────────────────────────────── */
const video         = document.getElementById("cameraFeed");
const canvas        = document.getElementById("cameraCanvas");
const overlay       = document.getElementById("cameraOverlay");
const startBtn      = document.getElementById("startCameraBtn");
const captureBtn    = document.getElementById("captureBtn");
const stopBtn       = document.getElementById("stopCameraBtn");
const captureBadge  = document.getElementById("captureBadge");
const photoBadge    = document.getElementById("photoBadge");
const angleGuide    = document.getElementById("angleGuide");
const thumbnails    = document.getElementById("thumbnailStrip");
const hintEl        = document.getElementById("captureHint");
const photoCountEl  = document.getElementById("photo_count");

/* ── Build angle guide dots ───────────────────────────────────────── */
function buildAngleGuide() {
  if (!angleGuide) return;
  angleGuide.innerHTML = "";
  ANGLE_LABELS.forEach(function (label, i) {
    const dot = document.createElement("div");
    dot.className = "angle-dot";
    dot.id = "dot-" + i;
    dot.textContent = label.replace(/ /g, "\n");
    dot.title = label;
    angleGuide.appendChild(dot);
  });
}

/* ── Update UI after each capture ────────────────────────────────── */
function updateUI() {
  const count = capturedPhotos.length;
  if (captureBadge) captureBadge.textContent = count + " / " + MAX_PHOTOS;
  if (photoBadge)   photoBadge.textContent   = count + " / " + MAX_PHOTOS;
  if (photoCountEl) photoCountEl.value = count;

  // Highlight the completed dots
  ANGLE_LABELS.forEach(function (_, i) {
    const dot = document.getElementById("dot-" + i);
    if (!dot) return;
    if (i < count) {
      dot.classList.add("captured");
      dot.classList.remove("active");
    } else if (i === count) {
      dot.classList.add("active");
      dot.classList.remove("captured");
    } else {
      dot.classList.remove("captured", "active");
    }
  });

  if (hintEl) {
    if (count === 0) {
      hintEl.textContent = 'Click "Capture" to take the first photo — face the camera directly.';
    } else if (count < MAX_PHOTOS) {
      hintEl.textContent = "Turn your head to: " + ANGLE_LABELS[count] + " — then click Capture.";
    } else {
      hintEl.textContent = "✅ All " + MAX_PHOTOS + " photos captured! Fill in details and submit.";
      if (overlay) overlay.classList.add("detecting");
    }
  }
}

/* ── Start camera ─────────────────────────────────────────────────── */
async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
      audio: false,
    });
    if (video) {
      video.srcObject = stream;
      await video.play();
    }
    if (startBtn)   startBtn.classList.add("d-none");
    if (captureBtn) captureBtn.classList.remove("d-none");
    if (stopBtn)    stopBtn.classList.remove("d-none");
    updateUI();
  } catch (err) {
    console.error("Camera error:", err);
    showToast("Could not access camera: " + err.message, "danger");
  }
}

/* ── Capture frame ────────────────────────────────────────────────── */
function captureFrame() {
  if (!video || !canvas) return;
  if (capturedPhotos.length >= MAX_PHOTOS) {
    showToast("Already captured " + MAX_PHOTOS + " photos.", "warning");
    return;
  }

  canvas.width  = video.videoWidth  || 640;
  canvas.height = video.videoHeight || 480;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  canvas.toBlob(function (blob) {
    if (!blob) return;
    const angle = ANGLE_LABELS[capturedPhotos.length] || "Extra";
    capturedPhotos.push({ blob: blob, angle: angle });

    // Show thumbnail
    if (thumbnails) {
      const img = document.createElement("img");
      img.src = URL.createObjectURL(blob);
      img.title = angle;
      img.alt = angle;
      thumbnails.appendChild(img);
    }

    // Append blob to form as a file input (so it is submitted)
    appendBlobToForm(blob, capturedPhotos.length);

    updateUI();

    // Flash overlay to give visual feedback
    if (overlay) {
      overlay.classList.add("detecting");
      setTimeout(function () { overlay.classList.remove("detecting"); }, 300);
    }

    if (capturedPhotos.length >= MAX_PHOTOS) {
      if (captureBtn) captureBtn.disabled = true;
      showToast("All " + MAX_PHOTOS + " photos captured!", "success");
    }
  }, "image/jpeg", 0.9);
}

/* ── Append blob as hidden file to the form ───────────────────────── */
function appendBlobToForm(blob, idx) {
  const form = document.getElementById("registerForm");
  if (!form) return;

  // Create a DataTransfer to wrap the blob as a File
  const file = new File([blob], "capture_" + idx + ".jpg", { type: "image/jpeg" });
  const dt = new DataTransfer();

  // Gather any existing files from the file input
  const existingInput = document.getElementById("photoFiles");
  if (existingInput && existingInput.files) {
    for (let i = 0; i < existingInput.files.length; i++) {
      dt.items.add(existingInput.files[i]);
    }
  }
  dt.items.add(file);

  if (existingInput) {
    existingInput.files = dt.files;
  }
}

/* ── Stop camera ──────────────────────────────────────────────────── */
function stopCamera() {
  if (stream) {
    stream.getTracks().forEach(function (t) { t.stop(); });
    stream = null;
  }
  if (video) video.srcObject = null;
  if (startBtn)   startBtn.classList.remove("d-none");
  if (captureBtn) captureBtn.classList.add("d-none");
  if (stopBtn)    stopBtn.classList.add("d-none");
}

/* ── Wire events ──────────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", function () {
  buildAngleGuide();
  updateUI();

  if (startBtn)   startBtn.addEventListener("click", startCamera);
  if (captureBtn) captureBtn.addEventListener("click", captureFrame);
  if (stopBtn)    stopBtn.addEventListener("click", stopCamera);

  // Handle file input change (manual upload path)
  const fileInput = document.getElementById("photoFiles");
  if (fileInput) {
    fileInput.addEventListener("change", function () {
      const count = fileInput.files.length;
      if (photoBadge) photoBadge.textContent = count + " / " + MAX_PHOTOS;
      if (photoCountEl) photoCountEl.value = count;
    });
  }
});
