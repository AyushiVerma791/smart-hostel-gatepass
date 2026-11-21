/**
 * GatePass — Smart Girls' Hostel Outpass Management System
 * Frontend UI & Verification Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Auto-dismiss flash alerts after 6 seconds
  const alerts = document.querySelectorAll(".alert-dismissible");
  alerts.forEach((alert) => {
    setTimeout(() => {
      try {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        if (bsAlert) bsAlert.close();
      } catch (e) {
        // Fallback
        alert.style.display = "none";
      }
    }, 6000);
  });

  // 2. Notification counter periodic check (every 30 seconds)
  function checkUnreadNotifications() {
    const badge = document.getElementById("notification-badge");
    if (!badge) return;

    fetch("/api/notifications/unread-count")
      .then((res) => {
        if (!res.ok) throw new Error("Network error");
        return res.json();
      })
      .then((data) => {
        if (data.unread_count > 0) {
          badge.textContent = data.unread_count;
          badge.classList.remove("d-none");
        } else {
          badge.classList.add("d-none");
        }
      })
      .catch(() => {
        // Silent fail on network error
      });
  }

  // Periodic poll if user is logged in
  if (document.getElementById("notification-badge")) {
    setInterval(checkUnreadNotifications, 30000);
  }
});

/**
 * QR Code Camera Scanner Controller
 * Uses html5-qrcode library
 */
let html5QrCodeScanner = null;

function initQrCameraScanner(targetElementId, onScanSuccessCallback) {
  const readerElement = document.getElementById(targetElementId);
  if (!readerElement) return;

  if (typeof Html5Qrcode === "undefined") {
    console.warn("Html5Qrcode library not loaded. Ensure script is included.");
    const statusMsg = document.getElementById("scanner-status-message");
    if (statusMsg) {
      statusMsg.innerHTML =
        '<div class="alert alert-warning"><i class="bi bi-exclamation-triangle"></i> Camera library not loaded. Please use manual code entry.</div>';
    }
    return;
  }

  const html5QrCode = new Html5Qrcode(targetElementId);
  const config = { fps: 10, qrbox: { width: 250, height: 250 } };

  const startScanner = (cameraId) => {
    html5QrCode
      .start(
        cameraId,
        config,
        (decodedText, decodedResult) => {
          // Play a gentle beep audio or flash
          console.log(`Scan result: ${decodedText}`);
          html5QrCode.stop().then(() => {
            onScanSuccessCallback(decodedText);
          });
        },
        (errorMessage) => {
          // Scanning in progress...
        }
      )
      .catch((err) => {
        console.error("Unable to start scanner", err);
        const statusMsg = document.getElementById("scanner-status-message");
        if (statusMsg) {
          statusMsg.innerHTML = `
            <div class="alert alert-info py-2 small">
              <i class="bi bi-camera-video-off me-1"></i> Camera access unavailable (${err.name || "Permission Required"}). 
              Use the manual entry input below or ensure HTTPS / localhost camera permission.
            </div>`;
        }
      });
  };

  Html5Qrcode.getCameras()
    .then((cameras) => {
      if (cameras && cameras.length) {
        // Prefer rear camera on mobile
        let selectedCamera = cameras[0].id;
        for (const cam of cameras) {
          if (cam.label.toLowerCase().includes("back") || cam.label.toLowerCase().includes("rear") || cam.label.toLowerCase().includes("environment")) {
            selectedCamera = cam.id;
            break;
          }
        }
        startScanner(selectedCamera);
      } else {
        const statusMsg = document.getElementById("scanner-status-message");
        if (statusMsg) {
          statusMsg.innerHTML = '<div class="alert alert-secondary py-2 small">No camera detected on this device. Please use manual entry.</div>';
        }
      }
    })
    .catch((err) => {
      const statusMsg = document.getElementById("scanner-status-message");
      if (statusMsg) {
        statusMsg.innerHTML = `
          <div class="alert alert-secondary py-2 small">
            <i class="bi bi-shield-lock me-1"></i> Camera permission prompt dismissed or unavailable. 
            Quick manual code entry is ready below.
          </div>`;
      }
    });
}
