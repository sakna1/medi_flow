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
        method: "PATCH",
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
            const registeredEl = document.getElementById('registered-count');
            const appointmentsEl = document.getElementById('appointments-count');
            const ongoingEl = document.getElementById('ongoing-count');

            if (registeredEl) registeredEl.textContent = data.registered_today ?? 0;
            if (appointmentsEl) appointmentsEl.textContent = data.appointments_today ?? 0;
            if (ongoingEl) ongoingEl.textContent = data.ongoing_treatments ?? 0;
        })
        .catch(error => console.error('Error fetching counts:', error));
}


// Initial load
updateDashboardCounts();

fetch('/top-disease-monthly')
  .then(response => response.json())
  .then(data => {
      const labels = data.map(d => d.month);
      const counts = data.map(d => d.count);
      const diseases = data.map(d => d.disease);

      const ctx = document.getElementById('topDiseaseChart').getContext('2d');
      new Chart(ctx, {
          type: 'bar',
          data: {
              labels: labels,
              datasets: [{
                  label: 'Top Disease Count',
                  data: counts,
                  backgroundColor: '#E74C3C'
              }]
          },
          options: {
              responsive: true,
              plugins: {
                  tooltip: {
                      callbacks: {
                          label: function(context) {
                              let disease = diseases[context.dataIndex];
                              return disease + ': ' + context.formattedValue + ' patients';
                          }
                      }
                  },
                  legend: { display: false }
              },
              scales: { y: { beginAtZero: true } }
          }
      });
  });


  document.addEventListener("DOMContentLoaded", function() {
    fetch("/dashboard-stats")
        .then(response => response.json())
        .then(data => {
            // --- 1. Patient Registrations per Month ---
            let regLabels = data.registrations.map(r => r.month);
            let regCounts = data.registrations.map(r => r.count);

            new Chart(document.getElementById("patientCountChart"), {
                type: "bar",
                data: {
                    labels: regLabels,
                    datasets: [{
                        label: "Patient Registrations",
                        data: regCounts,
                        backgroundColor: "rgba(54, 162, 235, 0.6)"
                    }]
                }
            });

            // --- 2. Treatments by Type per Month ---
            let treatLabels = data.treatments.map(t => t.month);

            // Collect all unique treatment types safely
            let treatmentTypes = [];
            data.treatments.forEach(t => {
                if (t.treatments && typeof t.treatments === 'object') {
                    Object.keys(t.treatments).forEach(tt => {
                        if (tt && !treatmentTypes.includes(tt)) treatmentTypes.push(tt);
                    });
                }
            });

            // Prepare datasets for each treatment type
            const darkMatteColors = [
                "#374151", "#4B5563", "#1F2937", "#6B21A8",
                "#1E3A8A", "#065F46", "#92400E", "#7F1D1D"
            ];

            let datasets = treatmentTypes.map((tt, idx) => {
                return {
                    label: tt,
                    data: data.treatments.map(t => (t.treatments && t.treatments[tt]) ? t.treatments[tt] : 0),
                    backgroundColor: darkMatteColors[idx % darkMatteColors.length]
                };
            });

            // Only create the chart if there is at least one dataset
            if (datasets.length > 0 && treatLabels.length > 0) {
                new Chart(document.getElementById("treatmentChart"), {
                    type: "bar",
                    data: {
                        labels: treatLabels,
                        datasets: datasets
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return context.dataset.label + ": " + context.raw;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: { stacked: true },
                            y: { stacked: true }
                        }
                    }
                });
            } else {
                // Show message if no data
                document.getElementById("treatmentChart").replaceWith(
                    document.createElement("p").appendChild(
                        document.createTextNode("No treatment data available.")
                    )
                );
            }
        })
        .catch(err => console.error("Error loading dashboard stats:", err));
});


let ageChartInstance = null;

// Function to load the Patient Demographics Report
async function loadDemographicsReport() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    try {
        const response = await fetch(`/report/patient-demographics?start_date=${startDate}&end_date=${endDate}`);
        if (!response.ok) throw new Error('Failed to fetch data');

        const data = await response.json();

        renderAgeChart(data.age_groups);
        renderTopDiseasesTable(data.top_diseases);

    } catch (error) {
        console.error('Error loading demographics report:', error);
        alert('Failed to load report. Please try again.');
    }
}

// Render the Age Distribution Bar Chart
function renderAgeChart(ageGroups) {
    const ctx = document.getElementById('ageChart').getContext('2d');

    // Destroy previous chart instance if exists
    if (ageChartInstance) ageChartInstance.destroy();

    ageChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ageGroups.map(a => a.age_group),
            datasets: [{
                label: 'Number of Patients',
                data: ageGroups.map(a => a.count),
                backgroundColor: '#6B21A8', // Change bar color
                borderColor: '#6B21A8',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

// Render Top 5 Diseases Table
function renderTopDiseasesTable(diseases) {
    const tbody = document.querySelector('#diseaseTable tbody');
    tbody.innerHTML = '';

    diseases.forEach(d => {
        const row = document.createElement('tr');
        row.innerHTML = `<td>${d.disease}</td><td>${d.count}</td>`;
        tbody.appendChild(row);
    });
}

// Optional: Load default report on page load
document.addEventListener('DOMContentLoaded', () => {
    loadDemographicsReport();
});

document.addEventListener("DOMContentLoaded", () => {
        loadStaffWorkloadReport();
    });

async function loadStaffWorkloadReport() {
    try {
        const response = await fetch("/staff-workload-report");
        const data = await response.json();

        // Clear old content
        document.getElementById("staffWorkloadTableBody").innerHTML = "";

        // Insert table rows
        data.forEach((item, index) => {
            let row = `
                <tr>                   
                    <td>${item.doctor}</td>
                    <td>${item.patients}</td>
                </tr>
            `;
            document.getElementById("staffWorkloadTableBody").innerHTML += row;
        });

        // Chart.js Pie Chart
        const ctx = document.getElementById("staffWorkloadChart").getContext("2d");
        if (window.staffWorkloadChartInstance) {
            window.staffWorkloadChartInstance.destroy(); // prevent duplicate charts
        }
        window.staffWorkloadChartInstance = new Chart(ctx, {
            type: "bar",  // you can also use "pie" or "doughnut"
            data: {
                labels: data.map(item => item.doctor),
                datasets: [{
                    label: "Patients",
                    data: data.map(item => item.patients),
                    backgroundColor: [
                        "#4B5563", "#1F2937"
                    ],
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false,
                        position: "top",
                    },
                    title: {
                        display: false,                        
                    }
                }
            }
        });

    } catch (error) {
        console.error("Error loading staff workload report:", error);
    }
}







