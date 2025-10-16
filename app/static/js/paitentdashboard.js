let slideIndex = 0;
const slides = document.querySelectorAll('.slide');

function showSlide(index) {
  slides.forEach((slide, i) => {
    slide.classList.toggle('active', i === index);
  });
}

setInterval(() => {
  slideIndex = (slideIndex + 1) % slides.length;
  showSlide(slideIndex);
}, 5000); 

async function loadTodayAppointment() {
  try {
    const res = await fetch("/dashboard/today-appointment");
    const data = await res.json();

    if (data.status === "none") {
      document.getElementById("todayClinic").innerText = "No appointment";
      document.getElementById("todayDate").innerText = "-";
      document.getElementById("todayTime").innerText = "-";
      document.getElementById("todayRoom").innerText = "-";
      document.getElementById("todayQueue").innerText = "-";
    } else {
      document.getElementById("todayClinic").innerText = data.clinic;
      document.getElementById("todayDate").innerText = data.date;
      document.getElementById("todayTime").innerText = data.time;
      document.getElementById("todayRoom").innerText = data.room_no;
      document.getElementById("todayQueue").innerText = data.queue_number;
    }
  } catch (err) {
    console.error("Error loading today appointment", err);
  }
}

async function loadNextAppointment() {
  try {
    const res = await fetch("/dashboard/next-appointment");
    const data = await res.json();

    if (data.status === "none") {
      document.getElementById("nextDate").innerText = "No upcoming appointment";
    } else {
      document.getElementById("nextDate").innerText = data.date;
    }
  } catch (err) {
    console.error("Error loading next appointment", err);
  }
}

// Initial load
loadTodayAppointment();
loadNextAppointment();



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



