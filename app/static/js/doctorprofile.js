function loadDashboard() {
    fetch("/dashboard-data")
        .then(response => response.json())
        .then(data => {
            // Today's appointments
            document.getElementById("todayAppointments").textContent = data.today_appointments;

            // Next appointment
            if (data.next_appointment.patient_id) {
                document.getElementById("nextAppointment").innerHTML = `
                    Patient Id - ${data.next_appointment.patient_id}<br>
                    Time - ${data.next_appointment.time || "Not set"}
                `;
            } else {
                document.getElementById("nextAppointment").textContent = "No upcoming appointments";
            }

            // Completed appointments
            document.getElementById("completedAppointments").textContent = data.completed_appointments;

            // Hospital updates
            document.getElementById("hospitalUpdates").textContent = data.hospital_update;
        })
        .catch(error => console.error("Error loading dashboard:", error));
}

// Load when page starts
document.addEventListener("DOMContentLoaded", loadDashboard);
document.addEventListener("DOMContentLoaded", loadDoctorSchedule);

// 🔄 Auto-refresh every 30s (optional)
setInterval(loadDashboard, 30000);

function loadDoctorSchedule() {
    fetch("/doctor/dash-schedule")
        .then(res => {
            if (!res.ok) throw new Error("Network response was not ok");
            return res.json();
        })
        .then(data => {
            const scheduleList = document.getElementById("doctorScheduleList");
            scheduleList.innerHTML = "";

            if (!data || data.length === 0) {
                scheduleList.innerHTML = "<li>No appointments scheduled for today</li>";
                return;
            }

            data.forEach(item => {
                const li = document.createElement("li");
                li.innerHTML = `
                    <strong>${item.time}</strong> – Patient ${item.patient_id} 
                    <span class="tag">${item.action_type}</span>
                    ${item.room && item.room !== "N/A" ? ` | Room: ${item.room}` : ""}
                `;
                scheduleList.appendChild(li);
            });
        })
        .catch(err => {
            console.error("Error loading doctor schedule:", err);
            const scheduleList = document.getElementById("doctorScheduleList");
            scheduleList.innerHTML = "<li>Error loading schedule</li>";
        });
}
