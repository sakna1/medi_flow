// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.querySelector('.notification-search input');
  const notifications = document.querySelectorAll('.notification-item');

  searchInput.addEventListener('input', function() {
    const query = this.value.toLowerCase();

    notifications.forEach(function(item) {
      const text = item.textContent.toLowerCase();
      if (text.includes(query)) {
        item.style.display = 'block';
      } else {
        item.style.display = 'none';
      }
    });
  });
});

// for patient search
document.getElementById("search-btn").addEventListener("click", function () {
    const name = document.getElementById("patient_name").value;
    const id = document.getElementById("patient_id").value;

    fetch("/search_patient", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
            patient_name: name,
            patient_id: id
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
           document.getElementById("patientid").value = data.id;
            document.getElementById("firstname").value = data.first_name;
            document.getElementById("lastname").value = data.last_name;
            document.getElementById("email").value = data.email;
            document.getElementById("contact").value = data.phone;
            document.getElementById("dob").value = data.dob;
            document.getElementById("gender").value = data.gender;
            document.getElementById("address").value = data.address;
            document.getElementById("nic").value = data.nic;
            document.getElementById("maritalstatus").value = data.marital_status;

            // Medical Info
            document.getElementById("disease").value = data.disease;
            document.getElementById("description").value = data.description;
            document.getElementById("treatmentstatus").value = data.treatment_status;
            document.getElementById("bloodtype").value = data.blood_type;
        }
    })
    .catch(err => console.error(err));
});

