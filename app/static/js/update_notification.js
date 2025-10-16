document.addEventListener("DOMContentLoaded", function () {
    const typeSelect = document.getElementById("type");
    const patientField = document.getElementById("patientField");

    // Only run if elements exist
    if (typeSelect && patientField) {
        typeSelect.addEventListener("change", function () {
            if (this.value === "patient") {
                patientField.classList.remove("hidden");
            } else {
                patientField.classList.add("hidden");
            }
        });
    }

    // Notification search
    const searchInput = document.querySelector(".notification-search input");
    const notificationList = document.getElementById("notificationList");

    if (searchInput && notificationList) {
        searchInput.addEventListener("input", function() {
            const filter = searchInput.value.toLowerCase();
            const items = notificationList.querySelectorAll(".notification-item");

            items.forEach(item => {
                const text = item.querySelector("p").textContent.toLowerCase();
                item.style.display = text.includes(filter) ? "flex" : "none";
            });
        });
    }
});
