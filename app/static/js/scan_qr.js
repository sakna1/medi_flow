document.addEventListener("DOMContentLoaded", function () {
    const scanButton = document.getElementById("start-scan");
    const qrRegion = document.getElementById("qr-reader");

    let html5QrCode;

    scanButton.addEventListener("click", function () {
        if (!html5QrCode) {
            html5QrCode = new Html5Qrcode("qr-reader");
        }

        html5QrCode.start(
            { facingMode: "environment" }, // Rear camera
            { fps: 10, qrbox: 250 },
            (decodedText, decodedResult) => {
                console.log(`Scanned code: ${decodedText}`);
                // Send to Flask backend
                fetch("/nurse/scan", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ qr_data: decodedText })
                }).then(res => res.json())
                  .then(data => alert(data.message))
                  .catch(err => console.error(err));

                html5QrCode.stop().then(() => {
                    console.log("QR scanning stopped.");
                });
            },
            (errorMessage) => {
                // Ignore scan errors
            }
        ).catch(err => {
            console.error("Unable to start scanning:", err);
        });
    });
});