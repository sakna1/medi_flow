async function loadWaitingTime() {
  const queueText = document.getElementById("queueText");

  try {
    const response = await fetch("/get-waiting-time");
    const data = await response.json();

    if (data.waiting_time === null) {
      queueText.textContent = "No active queue found.";
    } else if (data.waiting_time <= 0) {
      queueText.textContent = "It's your turn! Please proceed to the room.";
    } else {
      queueText.textContent = `Estimated Waiting Time: ${data.waiting_time} minutes`;
    }
  } catch (error) {
    console.error("Error fetching waiting time:", error);
    queueText.textContent = "Error loading waiting time.";
  }
}

// Refresh every 15 seconds
setInterval(loadWaitingTime, 15000);

// Initial load
loadWaitingTime();
