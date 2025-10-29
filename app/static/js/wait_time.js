
async function loadWaitingTime() {
  const queueText = document.getElementById("queueText");

  try {
    const response = await fetch("/patient/get-waiting-time");
    const data = await response.json();

    if (data.waiting_time === null) {
      queueText.textContent = "No active queue found or waiting time not set.";
    } else {
      queueText.textContent = `Estimated Waiting Time: ${data.waiting_time} minutes`;
    }
  } catch (error) {
    console.error("Error fetching waiting time:", error);
    queueText.textContent = "Error loading waiting time.";
  }
}

// load once
loadWaitingTime();

// refresh every 30 seconds
setInterval(loadWaitingTime, 30000);

