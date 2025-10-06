function resetForm() {
  document.querySelector("form").reset();

  // wipe all values
  document.querySelectorAll("input, textarea, select").forEach(el => {
    el.value = "";
  });

  // clear radios & checkboxes
  document.querySelectorAll("input[type=radio], input[type=checkbox]").forEach(el => {
    el.checked = false;
  });

  // also hide sections again after reset
  document.getElementById("medical-info").style.display = "none";
  document.getElementById("doctor-info").style.display = "none";
}

// Show/hide Medical Info & Doctor Info based on Role
document.addEventListener("DOMContentLoaded", () => {
  const roleSelect = document.getElementById("role");
  const medicalSection = document.getElementById("medical-info");
  const doctorSection = document.getElementById("doctor-info");
  const specializationInput = document.getElementById("specialization");

  function toggleSections() {
    const role = roleSelect.value;

    // Show Patient fields
    if (role === "Patient") {
      medicalSection.style.display = "block";
    } else {
      medicalSection.style.display = "none";
    }

    // Show Doctor fields
    if (role === "Doctor") {
      doctorSection.style.display = "block";
      specializationInput.setAttribute("required", "required");
    } else {
      doctorSection.style.display = "none";
      specializationInput.removeAttribute("required");
    }
  }

  // Run once on load
  toggleSections();

  // Run on change
  roleSelect.addEventListener("change", toggleSections);
});

fetch('/api/diseases')
    .then(res => res.json())
    .then(data => {
      const select = document.getElementById('disease');
      select.innerHTML = '<option value="">-- Select Disease --</option>';
      data.forEach(d => {
        const option = document.createElement('option');
        option.value = d.id;
        option.textContent = d.name;
        select.appendChild(option);
      });
    })
    .catch(err => console.error("Error loading diseases:", err));