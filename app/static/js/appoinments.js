document.addEventListener("DOMContentLoaded", () => {
  fetch("/doctor/past-appointments")
    .then(res => {
      if (!res.ok) {
        if (res.status === 401) {
          window.location.href = loginUrl; // redirect if not logged in
        }
        throw new Error(`HTTP error! Status: ${res.status}`);
      }
      return res.json();
    })
    .then(data => {
      const tbody = document.querySelector("#pastAppointmentsTable tbody");
      tbody.innerHTML = "";

      if (!Array.isArray(data) || data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center">No past appointments found</td></tr>`;
        return;
      }

      data.forEach(appt => {
        const row = `
          <tr>
            <td>${appt.start_time}</td>
            <td>${appt.end_time}</td>
            <td>${appt.patient_name}</td>
            <td>${appt.disease}</td>
            <td>${appt.treatment_status}</td>
            <td>${appt.room_no}</td>
            <td>${appt.status}</td>
            <td>${appt.notes}</td>
          </tr>
        `;
        tbody.innerHTML += row;
      });
    })
    .catch(err => {
      console.error("Error loading past appointments:", err);
      const tbody = document.querySelector("#pastAppointmentsTable tbody");
      tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Failed to load past appointments</td></tr>`;
    });
});

document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("searchInput");
  const startDate = document.getElementById("startDate");
  const endDate = document.getElementById("endDate");
  const filterBtn = document.getElementById("filterBtn");
  const table = document.getElementById("pastAppointmentsTable").getElementsByTagName("tbody")[0];

  // 🔍 Search Function
  searchInput.addEventListener("keyup", function () {
    const searchText = this.value.toLowerCase();
    const rows = table.getElementsByTagName("tr");

    Array.from(rows).forEach(row => {
      const cells = row.getElementsByTagName("td");
      const rowText = Array.from(cells).map(cell => cell.textContent.toLowerCase()).join(" ");
      row.style.display = rowText.includes(searchText) ? "" : "none";
    });
  });

  // 📅 Date Range Filter
  filterBtn.addEventListener("click", function () {
    const from = new Date(startDate.value);
    const to = new Date(endDate.value);
    const rows = table.getElementsByTagName("tr");

    Array.from(rows).forEach(row => {
      const startTimeCell = row.cells[0]?.textContent; // Assuming Start Time is column[0]
      if (!startTimeCell) return;

      const appointmentDate = new Date(startTimeCell);

      if ((isNaN(from) || appointmentDate >= from) &&
          (isNaN(to) || appointmentDate <= to)) {
        row.style.display = "";
      } else {
        row.style.display = "none";
      }
    });
  });
});

