// Add task to the to-do list
function addTask() {
  const input = document.getElementById('new-task');
  const task = input.value.trim();
  if (task === '') return;

  const list = document.getElementById('todo-list');
  const li = document.createElement('li');
  li.innerHTML = `<input type="checkbox"> ${task}`;
  list.appendChild(li);

  input.value = '';
}

 const openBtn = document.getElementById('openFormBtn');
    const popupBox = document.getElementById('popupBox');
    const popupOverlay = document.getElementById('popupOverlay');

    openBtn.addEventListener('click', function(e) {
      e.preventDefault();
      popupBox.classList.add('active');
      popupOverlay.style.display = 'block';
    });

    popupOverlay.addEventListener('click', function() {
      popupBox.classList.remove('active');
      popupOverlay.style.display = 'none';
    });

    document.getElementById("saveNextAppointment").addEventListener("click", function() {
    const patientId = document.getElementById("patientid").value;
    const nextDate = document.getElementById("nextAppointmentDate").value;

    if (!nextDate) {
        alert("Please select a date!");
        return;
    }

    fetch(`/save_next_appointment/${patientId}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ next_appointment: nextDate })
    })
    .then(res => res.json())
    .then(data => {
        alert("Next appointment saved successfully!");
    })
    .catch(err => {
        console.error("Error saving appointment:", err);
    });
});

document.getElementById("startAppointment").addEventListener("click", function () {
    const patientId = document.getElementById("patientid").value;

    if (!patientId) {
        alert("Please search and load a patient first!");
        return;
    }

    fetch(`/start_appointment/${patientId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
    .then(res => res.json())
    .then(data => {
        console.log("Server Response:", data); // Debugging

        if (data.message) {
            alert(`${data.message}\nScan Time: ${data.scan_time}`);
        } else if (data.error) {
            alert(`Error: ${data.error}`);
        } else {
            alert("Unexpected response from server.");
        }
    })
    .catch(err => {
        console.error("Error starting appointment:", err);
        alert("Something went wrong. Please try again.");
    });
});

document.getElementById("completeAppointment").addEventListener("click", function () {
    const patientId = document.getElementById("patientid").value;

    if (!patientId) {
        alert("Please search and load a patient first!");
        return;
    }

    fetch(`/complete_appointment/${patientId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        location.reload();
    })
    .catch(err => console.error("Error completing appointment:", err));
});

function savePatient() {
  const patientId = document.getElementById("patientid").value; 
  const treatmentStatus = document.getElementById("treatmentstatus").value;
  const treatmentType = document.getElementById("treatmentype").value;

  if (!patientId) {
    alert("⚠️ No patient loaded!");
    return;
  }

  fetch(`/update_patient/${patientId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      treatment_status: treatmentStatus,
      treatment_type: treatmentType
    }),
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


