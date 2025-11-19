function searchUser() {
    let query = document.getElementById("searchInput").value.trim();

    if (!query) {
        alert("Please enter a name to search.");
        return;
    }

    fetch(`/search_user?name=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(user => {
            if (user) {
                document.getElementById("userid").value = user.id || "";
                document.getElementById("dob").value = user.date_of_birth || "";
                document.getElementById("firstname").value = user.firstname || "";
                document.getElementById("lastname").value = user.lastname || "";
                document.getElementById("maritalstatus").value = user.marital_status || "";
                document.getElementById("email").value = user.email || "";
                document.getElementById("gender").value = user.gender || "";
                document.getElementById("address").value = user.address || "";
                document.getElementById("nic").value = user.nic || "";
                document.getElementById("contact").value = user.phone || "";
            } else {
                alert("User not found!");
            }
        })
        .catch(err => console.error("Search failed:", err));
}


function saveUser() {
    let userId = document.getElementById("userid").value;

    let updatedData = {};    
    const firstNameEl = document.getElementById("firstname");
    const lastNameEl = document.getElementById("lastname");
    const maritalEl = document.getElementById("maritalstatus");
    const emailEl = document.getElementById("email");
    const genderEl = document.getElementById("gender");
    const addressEl = document.getElementById("address");
    const nicEl = document.getElementById("nic");
    const phoneEl = document.getElementById("contact");
    const dobEl = document.getElementById("dob");

    if (firstNameEl?.value) updatedData.first_name = firstNameEl.value;
    if (lastNameEl?.value) updatedData.last_name = lastNameEl.value;
    if (maritalEl?.value) updatedData.marital_status = maritalEl.value;
    if (emailEl?.value) updatedData.email = emailEl.value;
    if (genderEl?.value) updatedData.gender = genderEl.value;
    if (addressEl?.value) updatedData.address = addressEl.value;
    if (nicEl?.value) updatedData.nic = nicEl.value;
    if (phoneEl?.value) updatedData.phone = phoneEl.value;
    if (dobEl?.value) updatedData.date_of_birth = dobEl.value;

    console.log("Updating user:", updatedData); // ✅ debug

    fetch(`/update_user/${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedData)
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message || "Updated successfully!");
    })
    .catch(err => console.error("Update failed:", err));
}
