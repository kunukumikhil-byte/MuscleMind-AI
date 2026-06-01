async function generateWorkout() {

    const response = await fetch("/generate_workout", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            weight: document.getElementById("weight").value,
            height: document.getElementById("height").value,
            goal: document.getElementById("goal").value,
            experience: document.getElementById("experience").value,
            days: document.getElementById("days").value
        })
    });

    const data = await response.json();

    document.getElementById(
        "workoutResult"
    ).innerHTML = data.response;
}


async function generateDiet() {

    const response = await fetch("/generate_diet", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            goal: document.getElementById("dietGoal").value,
            food: document.getElementById("food").value,
            budget: document.getElementById("budget").value,
            meals: document.getElementById("meals").value
        })
    });

    const data = await response.json();

    document.getElementById(
        "dietResult"
    ).innerHTML = data.response;
}


async function sendChat() {

    const response = await fetch("/fitness_chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            message:
            document.getElementById(
                "chatMessage"
            ).value
        })
    });

    const data = await response.json();

    document.getElementById(
        "chatResult"
    ).innerHTML = data.response;
}


async function saveProgress() {

    await fetch("/save_progress", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            weight:
            document.getElementById(
                "progressWeight"
            ).value,

            waist:
            document.getElementById(
                "waist"
            ).value,

            notes:
            document.getElementById(
                "notes"
            ).value
        })
    });

    alert("Progress Saved!");
    location.reload();
}