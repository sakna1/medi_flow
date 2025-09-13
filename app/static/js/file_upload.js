// -------------------------
// Upload Report
// -------------------------
const reportFileInput = document.getElementById("reportFile");
if (reportFileInput) {
    reportFileInput.addEventListener("change", function () {
        let file = this.files[0];
        if (!file) return;

        let patientId = document.getElementById("patientid").value;
        if (!patientId) {
            alert("⚠️ Please search and select a patient first!");
            return;
        }

        let formData = new FormData();
        formData.append("file", file);

        fetch(`/upload_report/${patientId}`, {
            method: "POST",
            body: formData
        })
        .then(res => res.text())
        .then(msg => {
            alert("✅ " + msg);
            fetchReports(patientId);
        })
        .catch(err => console.error("❌ Upload error:", err));
    });
}

// -------------------------
// Search Patient
// -------------------------
const searchBtn = document.getElementById("search-btn");
if (searchBtn) {
    searchBtn.addEventListener("click", function () {
        const name = document.getElementById("patient_name").value;
        const patientIdInput = document.getElementById("patient_id").value;

        fetch("/search_patient", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams({ patient_name: name, patient_id: patientIdInput })
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }

            // ✅ Fill patient personal info
            document.getElementById("patientid").value = data.id;
            document.getElementById("firstname").value = data.first_name;
            document.getElementById("lastname").value = data.last_name;
            document.getElementById("email").value = data.email;
            document.getElementById("contact").value = data.phone;
            document.getElementById("dob").value = data.dob;
            document.getElementById("gender").value = data.gender;
            document.getElementById("address").value = data.address;
            document.getElementById("nic").value = data.nic;
            document.getElementById("maritalstatus").value = data.marital_status;

            // ✅ Load reports
            fetchReports(data.id);
        })
        .catch(err => console.error("❌ Search error:", err));
    });
}
// -------------------------
// Fetch Reports (helper)
// -------------------------
function fetchReports(patientId) {
    fetch(`/get_patient_data/${patientId}`)
        .then(res => res.json())
        .then(data => {
            let reportList = document.querySelector(".report-list");
            reportList.innerHTML = ""; // clear old list

            const reports = data.reports; // ✅ Extract reports array

            if (!reports || reports.length === 0) {
                reportList.innerHTML = "<p>No reports uploaded yet.</p>";
                return;
            }

                reports.forEach(report => {
                let newRow = document.createElement("div");
                newRow.classList.add("report-row");

                newRow.innerHTML = `
                    <i class="bi bi-file-earmark-text"></i> ${report.file_name}
                    <a href="/view_report/${report.id}" target="_blank">
                        <i class="bi bi-eye"></i>
                    </a>
                    <a href="${report.file_url}" download>
                        <i class="bi bi-download"></i>
                    </a>
                `;

                reportList.appendChild(newRow);
            });
        })
        .catch(err => console.error("❌ Report fetch error:", err));
}

function updateRegisteredCount() {
    fetch("/get_registered_count")
        .then(response => {
            if (!response.ok) {
                throw new Error("Server error: " + response.status);
            }
            return response.json();
        })
        .then(data => {
            document.getElementById("registeredCount").innerText = data.count ?? 0;
        })
        .catch(err => {
            console.error("Error fetching count:", err);
            document.getElementById("registeredCount").innerText = "0"; // fallback
        });
}


// Refresh every 1 second
//setInterval(updateRegisteredCount, 6000);

// Run once immediately when page loads
updateRegisteredCount();
