function loadDashboard() {
    fetch("/dashboard-data")
        .then(response => response.json())
        .then(data => {
            // Today's appointments
            document.getElementById("todayAppointments").textContent = data.today_appointments;

            // Next appointment
            if (data.next_appointment.patient_id) {
            const next = data.next_appointment;
            document.getElementById("nextAppointment").innerHTML = `
                <strong>Patient ID:</strong> ${next.patient_id}<br>
                <strong>Queue Number:</strong> ${next.queue_number || "N/A"}<br>
                <strong>Scan Time:</strong> ${next.scan_time || "Not set"}
             `;
}      
else {
    document.getElementById("nextAppointment").textContent = "No upcoming appointments";
}

            // Completed appointments
            document.getElementById("completedAppointments").textContent = data.completed_appointments;

            // Hospital updates
            //document.getElementById("hospitalUpdates").textContent = data.hospital_update;
        })
        .catch(error => console.error("Error loading dashboard:", error));
}

// Load when page starts
document.addEventListener("DOMContentLoaded", loadDashboard);

function loadHospitalUpdates() {
    fetch("/hospital-updates")
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById("hospitalUpdates");
            if (data.updates && data.updates.length > 0) {
                // Combine updates into HTML, each update on a new line
                container.innerHTML = data.updates.map(u => `<p>${u}</p>`).join('');
            } else {
                container.textContent = "No updates today";
            }
        })
        .catch(error => console.error("Error loading hospital updates:", error));
}

// Call it when page loads
document.addEventListener("DOMContentLoaded", loadHospitalUpdates);

