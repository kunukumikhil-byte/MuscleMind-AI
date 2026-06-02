// ---------------- WORKOUT ---------------- //

async function generateWorkout() {

    const resultDiv =
        document.getElementById(
            "workoutResult"
        );

    resultDiv.innerHTML =
        "🧠 MuscleMind AI is generating your workout...";

    try {

        const response = await fetch(
            "/generate_workout",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                    "application/json"
                },

                body: JSON.stringify({
                    weight:
                    document.getElementById(
                        "weight"
                    ).value,

                    height:
                    document.getElementById(
                        "height"
                    ).value,

                    goal:
                    document.getElementById(
                        "goal"
                    ).value,

                    experience:
                    document.getElementById(
                        "experience"
                    ).value,

                    days:
                    document.getElementById(
                        "days"
                    ).value
                })
            }
        );

        const data =
            await response.json();

        resultDiv.innerHTML = `
            <div class="ai-response">
                ${data.response
                    .replace(/\n/g, "<br>")
                    .replace(/\*\*(.*?)\*\*/g,
                    "<b>$1</b>")
                }
            </div>
        `;

    }

    catch(error) {

        console.error(error);

        resultDiv.innerHTML =
            "❌ Error generating workout.";
    }
}


// ---------------- DIET ---------------- //

async function generateDiet() {

    const resultDiv =
        document.getElementById(
            "dietResult"
        );

    resultDiv.innerHTML =
        "🥗 Creating your AI diet plan...";

    try {

        const response = await fetch(
            "/generate_diet",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                    "application/json"
                },

                body: JSON.stringify({
                    goal:
                    document.getElementById(
                        "dietGoal"
                    ).value,

                    food:
                    document.getElementById(
                        "food"
                    ).value,

                    budget:
                    document.getElementById(
                        "budget"
                    ).value,

                    meals:
                    document.getElementById(
                        "meals"
                    ).value
                })
            }
        );

        const data =
            await response.json();

        resultDiv.innerHTML = `
            <div class="ai-response">
                ${data.response
                    .replace(/\n/g, "<br>")
                    .replace(/\*\*(.*?)\*\*/g,
                    "<b>$1</b>")
                }
            </div>
        `;

    }

    catch(error) {

        console.error(error);

        resultDiv.innerHTML =
            "❌ Error generating diet.";
    }
}


// ---------------- CHAT ---------------- //

async function sendChat() {

    const resultDiv =
        document.getElementById(
            "chatResult"
        );

    resultDiv.innerHTML =
        "💬 MuscleMind AI is thinking...";

    try {

        const response = await fetch(
            "/fitness_chat",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                    "application/json"
                },

                body: JSON.stringify({
                    message:
                    document.getElementById(
                        "chatMessage"
                    ).value
                })
            }
        );

        const data =
            await response.json();

        resultDiv.innerHTML = `
            <div class="ai-response">
                ${data.response
                    .replace(/\n/g, "<br>")
                    .replace(/\*\*(.*?)\*\*/g,
                    "<b>$1</b>")
                }
            </div>
        `;

    }

    catch(error) {

        console.error(error);

        resultDiv.innerHTML =
            "❌ Error getting AI response.";
    }
}


// ---------------- PROGRESS ---------------- //

async function saveProgress() {

    try {

        await fetch(
            "/save_progress",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                    "application/json"
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
            }
        );

        alert(
            "✅ Progress Saved!"
        );

        location.reload();

    }

    catch(error) {

        console.error(error);

        alert(
            "❌ Failed to save progress."
        );
    }
}