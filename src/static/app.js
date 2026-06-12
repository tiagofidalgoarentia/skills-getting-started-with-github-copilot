document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;
        const participantItems = details.participants
          .map((participant) => `<li><span class="activity-card__participant-email">${participant}</span><button class="activity-card__delete-btn" data-activity="${name}" data-email="${participant}" title="Remove participant">×</button></li>`)
          .join("");

        activityCard.innerHTML = `
          <div class="activity-card__header">
            <div>
              <h4>${name}</h4>
              <p class="activity-card__schedule">${details.schedule}</p>
            </div>
            <span class="activity-card__badge">${spotsLeft} spots left</span>
          </div>
          <p class="activity-card__description">${details.description}</p>
          <div class="activity-card__participants">
            <div class="activity-card__participants-heading">
              <strong>Participants</strong>
              <span>${details.participants.length} signed up</span>
            </div>
            <ul class="activity-card__participants-list">
              ${participantItems}
            </ul>
          </div>
        `;

        // Add event listeners for delete buttons
        activityCard.querySelectorAll(".activity-card__delete-btn").forEach((btn) => {
          btn.addEventListener("click", async (e) => {
            e.preventDefault();
            const activity = btn.getAttribute("data-activity");
            const email = btn.getAttribute("data-email");

            try {
              const response = await fetch(
                `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
                { method: "DELETE" }
              );

              if (response.ok) {
                // Refresh activities after deletion
                fetchActivities();
                // Show success message
                const msgDiv = document.getElementById("message");
                msgDiv.textContent = `Removed ${email} from ${activity}`;
                msgDiv.className = "success";
                msgDiv.classList.remove("hidden");
                setTimeout(() => msgDiv.classList.add("hidden"), 5000);
              } else {
                const result = await response.json();
                const msgDiv = document.getElementById("message");
                msgDiv.textContent = result.detail || "Failed to remove participant";
                msgDiv.className = "error";
                msgDiv.classList.remove("hidden");
              }
            } catch (error) {
              console.error("Error removing participant:", error);
              const msgDiv = document.getElementById("message");
              msgDiv.textContent = "Failed to remove participant";
              msgDiv.className = "error";
              msgDiv.classList.remove("hidden");
            }
          });
        });

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
