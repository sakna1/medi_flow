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
    if (document.getElementById("dob").value) updatedData.dob = document.getElementById("dob").value;
    if (document.getElementById("firstname").value) updatedData.firstname = document.getElementById("firstname").value;
    if (document.getElementById("lastname").value) updatedData.lastname = document.getElementById("lastname").value;
    if (document.getElementById("maritalstatus").value) updatedData.marital_status = document.getElementById("maritalstatus").value;
    if (document.getElementById("email").value) updatedData.email = document.getElementById("email").value;
    if (document.getElementById("gender").value) updatedData.gender = document.getElementById("gender").value;
    if (document.getElementById("address").value) updatedData.address = document.getElementById("address").value;
    if (document.getElementById("nic").value) updatedData.nic = document.getElementById("nic").value;
    if (document.getElementById("contact").value) updatedData.contact = document.getElementById("contact").value;

    fetch(`/update_user/${userId}`, {
        method: "PATCH",  // PATCH = partial update
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedData)
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message || "Updated successfully!");
    })
    .catch(err => console.error("Update failed:", err));
}

function updateDashboardCounts() {
    fetch('/get_dashboard_counts')
        .then(response => response.json())
        .then(data => {
            document.getElementById('registered-count').textContent = data.registered_today;
            document.getElementById('appointments-count').textContent = data.appointments_today;
            document.getElementById('ongoing-count').textContent = data.ongoing_treatments;
        })
        .catch(error => console.error('Error fetching counts:', error));
}

// Initial load
updateDashboardCounts();

