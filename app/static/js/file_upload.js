document.getElementById("reportFile").addEventListener("change", function() {
    let file = this.files[0];
    if (!file) return;

    let patientId = document.getElementById("patientid").value;
    if (!patientId) {
        alert("⚠️ Please enter Patient Id first!");
        return;
    }

    let formData = new FormData();
    formData.append("file", file);

    fetch(`/upload_report/${patientId}`, {   // ✅ now sending patientId in URL
        method: "POST",
        body: formData
    })
    .then(res => res.text())
    .then(data => {
        alert("✅ " + data);

        // Optionally add uploaded file to the report list dynamically
        let reportList = document.querySelector(".report-list");
        let newRow = document.createElement("div");
        newRow.classList.add("report-row");
        newRow.innerHTML = `<i class="bi bi-file-earmark-text"></i> ${file.name}
                            <i class="bi bi-download"></i>`;
        reportList.prepend(newRow); // add to top
    })
    .catch(err => console.error(err));
});

document.getElementById("search-btn").addEventListener("click", function () {
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

        // ✅ Fill personal info
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
        
        // ✅ Load reports if backend sends them
        if (data.reports && Array.isArray(data.reports)) {
            let reportList = document.querySelector(".report-list");
            reportList.innerHTML = ""; // clear old list

            data.reports.forEach(report => {
                let newRow = document.createElement("div");
                newRow.classList.add("report-row");

                newRow.innerHTML = `
                    <i class="bi bi-file-earmark-text"></i> ${report.file_name}
                    <a href="${report.file_url}" target="_blank">
                        <i class="bi bi-eye"></i>
                    </a>
                    <a href="${report.file_url}" download>
                        <i class="bi bi-download"></i>
                    </a>
                `;

                reportList.appendChild(newRow);
            });
        }

    })
    .catch(err => console.error("❌ Fetch error:", err));
});
