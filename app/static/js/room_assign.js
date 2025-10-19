async function loadAssignedRoom() {
  const statusMsg = document.getElementById("statusMsg");
  const roomSelect = document.getElementById("roomSelect");
  const assignBtn = document.getElementById("assignBtn");

  try {
    const res = await fetch("/get-assigned-room");
    const data = await res.json();

    if (data.success && data.room_no) {
      roomSelect.value = data.room_no;
      roomSelect.disabled = true;
      assignBtn.disabled = true;
      statusMsg.textContent = `✅ You already assigned Room ${data.room_no}`;
      statusMsg.style.color = "green";
    } else {
      statusMsg.textContent = "🟢 Please select a room to assign.";
      statusMsg.style.color = "black";
    }
  } catch (err) {
    console.error(err);
    statusMsg.textContent = "⚠️ Could not load room assignment.";
    statusMsg.style.color = "red";
  }
}

document.getElementById("assignBtn").addEventListener("click", async () => {
  const room_no = document.getElementById("roomSelect").value;
  const statusMsg = document.getElementById("statusMsg");

  if (!room_no) {
    statusMsg.textContent = "⚠️ Please select a room first!";
    statusMsg.style.color = "red";
    return;
  }

  try {
    const res = await fetch("/assign-room", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ room_no }),
    });
    const data = await res.json();

    if (data.success) {
      statusMsg.textContent = "✅ " + data.message;
      statusMsg.style.color = "green";
      document.getElementById("roomSelect").disabled = true;
      document.getElementById("assignBtn").disabled = true;
    } else {
      statusMsg.textContent = "❌ " + data.message;
      statusMsg.style.color = "red";
    }
  } catch (err) {
    console.error(err);
    statusMsg.textContent = "⚠️ Something went wrong!";
    statusMsg.style.color = "red";
  }
});

// Run when page loads
window.onload = loadAssignedRoom;

document.addEventListener("DOMContentLoaded", () => {
  const updatesEl = document.getElementById("hospitalUpdates");

  fetch("/hospital-updates")
    .then(res => res.json())
    .then(data => {
      if (data.updates.length > 0) {
        // Replace <li> with actual updates
        updatesEl.innerHTML = data.updates.map(u => `<li>${u}</li>`).join("");
      } else {
        updatesEl.innerHTML = "<li>No hospital updates for today.</li>";
      }
    })
    .catch(err => {
      console.error("Error loading updates:", err);
      updatesEl.innerHTML = "<li>Failed to load updates.</li>";
    });
});


