document.addEventListener("DOMContentLoaded", () => {
  const fetchAppointments = () => {
    let start = document.querySelector("#startDate").value;
    let end = document.querySelector("#endDate").value;
    let search = document.querySelector("#searchInput").value.trim();

    let url = `/patient/past-appointments?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}&search=${encodeURIComponent(search)}`;

    fetch(url)
      .then(res => res.json())
      .then(data => {
        let tbody = document.querySelector("#pastAppointmentsTable tbody");
        tbody.innerHTML = "";

        if (!data || data.length === 0) {
          tbody.innerHTML = `<tr><td colspan="8" class="text-center">No past appointments found</td></tr>`;
          return;
        }

        data.forEach(appt => {
          let row = `
            <tr>
              <td>${appt.start_time || "-"}</td>
              <td>${appt.end_time || "-"}</td>
              <td>${appt.doctor_name || "-"}</td>           
              <td>${appt.treatment_status || "-"}</td>
              <td>${appt.room_no || "-"}</td>
              <td>${appt.status || "-"}</td>
              <td>${appt.notes || "-"}</td>
            </tr>`;
          tbody.innerHTML += row;
        });
      })
      .catch(err => {
        console.error("Error loading patient past appointments:", err);
      });
  };

  // Initial load
  fetchAppointments();

  // Trigger on filter button
  document.querySelector("#filterBtn").addEventListener("click", fetchAppointments);

  // Optional: live search while typing
  document.querySelector("#searchInput").addEventListener("input", fetchAppointments);
});
