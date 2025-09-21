

    // -------------------------
    // Upload Report
    // -------------------------
    const reportFileInput = document.getElementById("reportFile");
    if (reportFileInput) {
        reportFileInput.addEventListener("change", function () {
            const file = this.files[0];
            if (!file) return;

            const patientId = document.getElementById("patientid")?.value;
            if (!patientId) {
                alert("⚠️ Please search and select a patient first!");
                return;
            }

            const formData = new FormData();
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
            const name = document.getElementById("patient_name")?.value || "";
            const patientIdInput = document.getElementById("patient_id")?.value || "";

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

                // Map backend keys to input IDs
                const fieldMap = {
                    patientid: "id",
                    firstname: "first_name",
                    lastname: "last_name",
                    maritalstatus: "marital_status",
                    email: "email",
                    phone: "phone",
                    dob: "dob",
                    gender: "gender",
                    address: "address",
                    nic: "nic"
                };

                Object.keys(fieldMap).forEach(inputId => {
                    const el = document.getElementById(inputId);
                    if (el) el.value = data[fieldMap[inputId]] ?? "";
                });

                // Load patient reports
                fetchReports(data.id);
            })
            .catch(err => console.error("❌ Search error:", err));
        });
    }

    // -------------------------
    // Fetch Reports
    // -------------------------
    function fetchReports(patientId) {
        fetch(`/get_patient_data/${patientId}`)
            .then(res => res.json())
            .then(data => {
                const reportList = document.querySelector(".report-list");
                if (!reportList) return;

                reportList.innerHTML = "";
                const reports = data.reports || [];

                if (reports.length === 0) {
                    reportList.innerHTML = "<p>No reports uploaded yet.</p>";
                    return;
                }

                reports.forEach(report => {
                    const newRow = document.createElement("div");
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

    // -------------------------
    // Update Registered Count
    // -------------------------
    function updateRegisteredCount() {
        fetch("/get_registered_count")
            .then(res => res.json())
            .then(data => {
                const el = document.getElementById("registeredCount");
                if (el) el.innerText = data.count ?? 0;
            })
            .catch(err => console.error("Error fetching count:", err));
    }

    updateRegisteredCount();
    // Optional: refresh every 6 seconds
    // setInterval(updateRegisteredCount, 6000);

    // -------------------------
    // Save Patient
    // -------------------------
  function savePatient() {
  const patientId = document.getElementById("patientid").value;

  if (!patientId) {
    alert("⚠️ No patient loaded!");
    return;
  }

  // Collect values from form  
  const firstName = document.getElementById("firstname").value;
  const lastName = document.getElementById("lastname").value;
  const maritalStatus = document.getElementById("maritalstatus").value;
  const email = document.getElementById("email").value;
  const gender = document.getElementById("gender").value;
  const address = document.getElementById("address").value;
  const nic = document.getElementById("nic").value;
  const phone = document.getElementById("phone").value;

  // Prepare payload
  const updatedData = {   
    first_name: firstName,
    last_name: lastName,
    marital_status: maritalStatus,
    email: email,
    gender: gender,
    address: address,
    nic: nic,
    phone: phone,
  };

  console.log("Sending update for patientId:", patientId, updatedData);

  fetch(`/update_patients/${patientId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updatedData),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        alert("❌ " + data.error);
      } else {
        alert("✅ Patient updated successfully!");
      }
    })
    .catch((err) => {
      console.error("Update failed:", err);
      alert("⚠️ Something went wrong while updating patient.");
    });
}




