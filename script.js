let games = [];

const gameGrid = document.getElementById("gameGrid");
const gameCount = document.getElementById("gameCount");
const installedCount = document.getElementById("installedCount");
const searchInput = document.getElementById("searchInput");

window.addEventListener("pywebviewready", async () => {
    try {
        games = await window.pywebview.api.load_games();
        displayGames(games);
    } catch (error) {
        console.error("Failed to load saved games:", error);
    }
});

async function addGameDialog() {
    try {
        const updatedGames = await window.pywebview.api.add_game();
        
        if (!updatedGames) {
            return;
        }

        games = updatedGames;
        displayGames(games);

    } catch (error) {
        alert("Could not add game.");
        console.error(error);
    }
}

async function removeGame(path) {
    try {
        const updatedGames = await window.pywebview.api.remove_game(path);
        games = updatedGames;
        displayGames(games);
    } catch (error) {
        alert("Could not remove game.");
        console.error(error);
    }
}

function displayGames(gameList) {
    gameGrid.innerHTML = "";
    gameCount.textContent = games.length;
    installedCount.textContent = games.length;

    if (gameList.length === 0) {
        gameGrid.innerHTML = `
            <div class="empty">
                <div class="icon">🎮</div>
                <h2>NO GAMES FOUND</h2>
                <p>Click "+ ADD GAME" to select a game executable (.exe).</p>
            </div>
        `;
        return;
    }

    gameList.forEach(game => {
        const card = document.createElement("div");
        card.className = "game-card";

        const headerIconHtml = game.icon 
            ? `<img src="${game.icon}" class="game-icon" alt="icon">`
            : `<div class="game-icon" style="display:flex;align-items:center;justify-content:center;">🎮</div>`;

        const buttonIconHtml = game.icon
            ? `<img src="${game.icon}" alt="">`
            : `▶`;

        card.innerHTML = `
            <div>
                <div class="card-top">
                    <div class="card-header">
                        ${headerIconHtml}
                        <h3>${game.name}</h3>
                    </div>
                    <button class="remove-btn" onclick='removeGame(${JSON.stringify(game.path)})'>✕</button>
                </div>
                <div class="path">${game.path}</div>
            </div>

            <button
                class="play"
                onclick='launchGame(${JSON.stringify(game.path)})'
            >
                ${buttonIconHtml} PLAY
            </button>
        `;

        gameGrid.appendChild(card);
    });
}

async function launchGame(path) {
    const result = await window.pywebview.api.launch_game(path);
    if (!result) {
        alert("Could not launch this game.");
    }
}

searchInput.addEventListener("input", function () {
    const query = this.value.toLowerCase();
    const filtered = games.filter(game =>
        game.name.toLowerCase().includes(query)
    );
    displayGames(filtered);
});