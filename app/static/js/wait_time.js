(() => {
  const queueText = document.getElementById("queueText");
  let remainingTime = 0;      // minutes
  let patientsAhead = 0;
  let lastUpdate = null;

  const fmt = (num) => new Intl.NumberFormat().format(num);

  async function fetchQueueStatus() {
    try {
      const res = await fetch("/queue_status", { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      if (data.patients_ahead !== undefined) {
        patientsAhead = data.patients_ahead;
        remainingTime = data.estimated_wait_time || 0;
        lastUpdate = new Date();

        renderQueue(data.room_no);
      } else {
        queueText.innerText = data.message || "You are not currently in queue.";
      }
    } catch (err) {
      console.error("Queue fetch error:", err);
      queueText.innerText = "⚠️ Unable to load queue status. Retrying...";
    }
  }

  function renderQueue(roomNo) {
    if (patientsAhead <= 0) {
      queueText.innerText = `🎉 It’s your turn in Room ${roomNo}! Please proceed to the doctor.`;
      return;
    }

    const timeUnit = remainingTime > 60
      ? `${Math.floor(remainingTime / 60)}h ${remainingTime % 60}m`
      : `${remainingTime} min`;

    const elapsed = lastUpdate
      ? Math.floor((Date.now() - lastUpdate.getTime()) / 60000)
      : 0;

    const effectiveTime = Math.max(remainingTime - elapsed, 0);

    queueText.innerText =
      `🏥 Room: ${roomNo}\n` +
      `🧑‍⚕️ You are ${fmt(patientsAhead)} patient${patientsAhead > 1 ? "s" : ""} away.\n` +
      `⏳ Estimated waiting time: ${effectiveTime} min`;
  }

  setInterval(() => {
    if (remainingTime > 0) {
      remainingTime--;
      renderQueue();
    }
  }, 60000);

  setInterval(fetchQueueStatus, 20000);
  fetchQueueStatus();
})();
