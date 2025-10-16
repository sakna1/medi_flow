// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {

  // Notification search (optional)
  const notificationSearch = document.querySelector('.notification-search input');
  if (notificationSearch) {
    const notifications = document.querySelectorAll('.notification-item');
    notificationSearch.addEventListener('input', function() {
      const query = this.value.toLowerCase();
      notifications.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(query) ? 'block' : 'none';
      });
    });
  }

  // Search button click
  document.getElementById("search-btn").addEventListener("click", function() {
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

      // Fill patient personal info
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

      // Fill medical info
      document.getElementById("disease_name").value = data.disease_name || ""; 
      document.getElementById("description").value = data.description;
      document.getElementById("treatmentstatus").value = data.treatment_status;
      document.getElementById("bloodtype").value = data.blood_type;
      document.getElementById("treatmentype").value = data.treatment_type;

      // Fetch visit history
      fetchVisitHistory(data.id);
      fetchReports(data.id);
    })
    .catch(err => console.error(err));
  });

  // fetchVisitHistory - updated
function fetchVisitHistory(patientId) {
  if (!patientId) return;

  fetch(`/visit-history/${patientId}`)
    .then(res => res.json())
    .then(data => {
      console.log("visit-history:", data); // debug output

      const tbody = document.querySelector(".visit-table tbody");
      if (!tbody) return;
      tbody.innerHTML = ""; // clear old rows

      const today = new Date(data.today);

      data.logs.forEach(log => {
        const tr = document.createElement("tr");

        // parse datetime safely
        const scanDate = log.scan_time ? new Date(log.scan_time) : null;
        const scanDisplay = scanDate ? scanDate.toLocaleString() : "-";
        const isToday = scanDate
          ? scanDate.toDateString() === today.toDateString()
          : false;

        // --- Condition ---
        if (isToday && (!log.end_time || log.end_time === null)) {
            tr.innerHTML = `
              <td>${scanDisplay}</td>
              <td>${log.room_no || '-'}</td>
              <td>${log.doctor_name || '-'}</td>
              <td>
                <textarea data-id="${log.id}">${log.notes || ''}</textarea>
                <button type="button" class="save-note-btn" data-id="${log.id}">Save</button>
              </td>
            `;
          } else {
            tr.innerHTML = `
              <td>${scanDisplay}</td>
              <td>${log.room_no || '-'}</td>
              <td>${log.doctor_name || '-'}</td>
              <td>${log.notes || '-'}</td>
            `;
          }

        tbody.appendChild(tr);
      });
    })
    .catch(err => {
      console.error("fetchVisitHistory error:", err);
    });
}

function fetchReports(patientId) {
    fetch(`/get_patient_reports/${patientId}`)
        .then(res => {
            if (!res.ok) {
                return res.text().then(text => { 
                    throw new Error("Server error: " + text);
                });
            }
            return res.json();
        })
        .then(data => {
            let reportList = document.querySelector(".report-list");
            reportList.innerHTML = "";

            if (!data.reports || data.reports.length === 0) {
                reportList.innerHTML = "<p>No reports found</p>";
                return;
            }

            data.reports.forEach(report => {
                let newRow = document.createElement("div");
                newRow.classList.add("report-item");

                newRow.innerHTML = `
                    <i class="bi bi-file-earmark-text"></i> ${report.report_name}
                    <a href="/view_report/${report.id}" target="_blank">
                        <i class="bi bi-eye"></i>
                    </a>
                    <a href="${report.file_path}" download>
                        <i class="bi bi-download"></i>
                    </a>
                `;
                reportList.appendChild(newRow);
            });
        })
        .catch(err => {
            console.error("Error fetching reports:", err);
        });
}



// Save note button click (delegated)
document.addEventListener("click", function (e) {
  if (e.target.classList.contains("save-note-btn")) {
    const logId = e.target.dataset.id;
    const textarea = document.querySelector(`textarea[data-id="${logId}"]`);
    const notes = textarea.value;

    fetch("/save-note", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ log_id: logId, notes: notes })
    })
      .then(res => res.json())
      .then(data => {
        if (data.log) {
          const log = data.log;
          const tr = e.target.closest("tr");

          // re-render this row as plain text (non-editable)
          const scanDisplay = log.scan_time
            ? new Date(log.scan_time).toLocaleString()
            : "-";

          tr.innerHTML = `
            <td>${scanDisplay}</td>
            <td>${log.room_no || "-"}</td>
            <td>${log.doctor_name || "-"}</td>
            <td>${log.notes || "-"}</td>
          `;
        }

        alert(data.message);
      })
      .catch(err => console.error("save-note error:", err));
  }
});

});


