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

  // also hide Medical Info again after reset
  document.getElementById("medical-info").style.display = "none";
}

// Show/hide Medical Info based on Role
document.addEventListener("DOMContentLoaded", () => {
  const roleSelect = document.getElementById("role");
  const medicalSection = document.getElementById("medical-info");

  function toggleMedicalInfo() {
    if (roleSelect.value === "Patient") {
      medicalSection.style.display = "block";
    } else {
      medicalSection.style.display = "none";
    }
  }

  // Run once on load
  toggleMedicalInfo();

  // Run again on change
  roleSelect.addEventListener("change", toggleMedicalInfo);
});
