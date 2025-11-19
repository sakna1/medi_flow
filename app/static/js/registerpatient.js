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
    if (role === "patient") {
      medicalSection.style.display = "block";
    } else {
      medicalSection.style.display = "none";
    }

    // Show Doctor fields
    if (role === "doctor") {
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
   document.querySelector('form').addEventListener('submit', e => {
   console.log('Form submitted!');
  
});
});
// === FORM VALIDATION ===
document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("form");

  const nicInput = document.getElementById("nic");
  const phoneInput = document.getElementById("phone");
  const emergencyPhoneInput = document.getElementById("emergency_contact_phone");

  // Create error message elements
  const nicError = document.createElement("small");
  const phoneError = document.createElement("small");
  const emergencyError = document.createElement("small");

  [nicError, phoneError, emergencyError].forEach(el => {
    el.style.color = "red";
    el.style.display = "block";
    el.style.marginTop = "3px";
    el.style.fontSize = "13px";
  });

  nicInput.parentNode.appendChild(nicError);
  phoneInput.parentNode.appendChild(phoneError);
  emergencyPhoneInput.parentNode.appendChild(emergencyError);

  form.addEventListener("submit", (e) => {
    let valid = true;

    const nic = nicInput.value.trim();
    const phone = phoneInput.value.trim();
    const emergency = emergencyPhoneInput.value.trim();

    // Sri Lankan phone pattern: 0712345678 or +94712345678
    const phoneRegex = /^(?:\+94|0)?7\d{8}$/;
    // NIC pattern: old (9 digits + V/X) or new (12 digits)
    const nicRegex = /^(\d{9}[vVxX]|\d{12})$/;

    // Reset errors
    nicError.textContent = "";
    phoneError.textContent = "";
    emergencyError.textContent = "";

    // Validate NIC
    if (!nicRegex.test(nic)) {
      nicError.textContent = "Invalid NIC. Use 991234567V or 200012345678 format.";
      valid = false;
    }

    // Validate Phone
    if (!phoneRegex.test(phone)) {
      phoneError.textContent = "Invalid phone number. Example: 0712345678 or +94712345678.";
      valid = false;
    }

    // Validate Emergency Contact Phone (if not empty)
    if (emergency && !phoneRegex.test(emergency)) {
      emergencyError.textContent = "Invalid emergency phone. Example: 0712345678 or +94712345678.";
      valid = false;
    }

    // Stop form submission if invalid
    if (!valid) {
      e.preventDefault();
    }
  });
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