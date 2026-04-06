const themeToggleBtn = document.getElementById('theme-toggle');
const btnNewGame = document.getElementById('btn-new-game');
const btnHistory = document.querySelector('a[href="/history"]');
const btnContinue = document.getElementById('btn-continue');
const popup = document.getElementById('difficulty-popup');
const btnClosePopup = document.getElementById('btn-close-popup');
const dashboardView = document.getElementById('dashboard-view');
const gameView = document.getElementById('game-view');
const boardElement = document.getElementById('sudoku-board');
const difficultyButtons = document.querySelectorAll('.diff-btn');
const isLoggedIn = document.body.dataset.loggedIn === 'true';
const btnUndo = document.getElementById('btn-undo');
const btnEraser = document.getElementById('btn-eraser');
const btnPencil = document.getElementById('btn-pencil');
const mistakesDisplay = document.getElementById('mistakes');
const timerDisplay = document.getElementById('timer');
const gameOverModal = document.getElementById('game-over-modal');
const closeModalBtn = document.getElementById('close-modal');
const modalIcon = document.getElementById('modal-icon');
const modalTitle = document.getElementById('modal-title');
const finalTimeDisplay = document.getElementById('final-time');
const animationContainer = document.getElementById('animation-container');
const btnPause = document.getElementById('btn-pause');
const pauseModal = document.getElementById('pause-modal');
const btnResume = document.getElementById('btn-resume');
const btnPauseMainMenu = document.getElementById('btn-pause-main-menu');

let selectedCell = null;
let moveHistory = [];
let isPencilMode = false;
let currentSolution = null;
let mistakes = 0;
let timerInterval = null;
let secondsElapsed = 0;
let isGameOver = false;

if (localStorage.getItem('sudoku_theme') === 'dark'){
    document.body.classList.add('dark-mode');
    themeToggleBtn.textContent = '☀️ Light Mode';
}
themeToggleBtn.addEventListener('click', function() {
    document.body.classList.toggle('dark-mode');
    if (document.body.classList.contains('dark-mode')) {
        themeToggleBtn.textContent = '☀️ Light Mode';
        localStorage.setItem('sudoku_theme', 'dark');
    } else {
        themeToggleBtn.textContent = '🌙 Dark Mode';
        localStorage.setItem('sudoku_theme', 'light');
    }
});

btnNewGame.addEventListener('click', function() {
    if (!isLoggedIn) {
        window.location.href = '/login';
        return; 
    }
    popup.classList.add('show');
});

btnHistory?.addEventListener('click', function(e) {
    if (!isLoggedIn) {
        e.preventDefault();
        window.location.href = '/login';
    }
});

btnContinue?.addEventListener('click', async function() {
    try {
        const response = await fetch('/continue_game');
        const data = await response.json();
        if (data.error){
            alert("No saved game found!");
            return;
        }
        dashboardView.classList.remove('active');
        gameView.classList.add('active');
        createEmptyBoard();
        currentSolution = data.solution;
        secondsElapsed = data.time || 0;
        mistakes = data.mistakes || 0;
        mistakesDisplay.textContent = `Mistakes: ${mistakes}/3`
        updateTimerDisplay();
        resumeTimer();
        const cells = document.querySelectorAll('.cell');
        if (data.current_grid){
            for (let i=0; i<81; i++){
                let cellData = data.current_grid[i];
                cells[i].textContent = cellData.text;
                if (cellData.isLocked) cells[i].classList.add('locked');
                if (cellData.isUserFilled) cells[i].classList.add('user-filled');
                if (cellData.isNotes) cells[i].classList.add('notes');
                if (cellData.isMistake) cells[i].classList.add('mistake');
            }
        } else {
            for (let i=0; i<81; i++){
                let row = Math.floor(i / 9);
                let col = i % 9;
                let number = data.puzzle[row][col];
                if (number !== 0){
                    cells[i].textContent = number;
                    cells[i].classList.add('locked');
                }
            }
        }
    } catch (error){
        console.error("Error loading saved game: ", error);
    }
});

btnClosePopup.addEventListener('click', function() {
    popup.classList.remove('show');
});

btnPause?.addEventListener('click', function() {
    stopTimer();
    pauseModal.classList.remove('hidden');
    saveGameState();
});

btnResume?.addEventListener('click', function() {
    pauseModal.classList.add('hidden');
    resumeTimer();
});

btnPauseMainMenu?.addEventListener('click', function() {
    window.location.reload();
});

difficultyButtons.forEach(button => {
    button.addEventListener('click', function() {
        const difficulty = this.getAttribute('data-level'); 

        popup.classList.remove('show');
        dashboardView.classList.remove('active');
        gameView.classList.add('active');

        createEmptyBoard();
        loadGame(difficulty);
    });
});

function createEmptyBoard() {
    moveHistory = [];
    mistakes = 0;
    isGameOver = false;
    mistakesDisplay.textContent = "Mistakes: 0/3";
    boardElement.innerHTML = ''; 
    for (let i = 0; i < 81; i++) {
        const cell = document.createElement('div');
        cell.classList.add('cell');
        cell.addEventListener('click', function(){
            if (this.classList.contains('locked')) return;
            if (selectedCell){
                selectedCell.classList.remove('selected');
            }
            selectedCell = this;
            this.classList.add('selected');
        });
        boardElement.appendChild(cell);
    }
}

function startTimer(){
    clearInterval(timerInterval);
    secondsElapsed = 0;
    updateTimerDisplay();

    timerInterval = setInterval(() => {
        secondsElapsed++;
        updateTimerDisplay();
    }, 1000);
}

function resumeTimer(){
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
        secondsElapsed++;
        updateTimerDisplay();
    }, 1000);
}

function updateTimerDisplay(){
    const minutes = Math.floor(secondsElapsed / 60);
    const seconds = secondsElapsed % 60;
    timerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

function stopTimer(){
    clearInterval(timerInterval);
}

async function loadGame(difficulty) {
    const response = await fetch(`/get_board/${difficulty}`);
    const data = await response.json();

    currentSolution = data.solution;
    startTimer();
    
    const cells = document.querySelectorAll('.cell');
    
    for (let i = 0; i < 81; i++) {
        let row = Math.floor(i / 9);
        let col = i % 9;
        let number = data.puzzle[row][col];
        
        if (number !== 0) {
            cells[i].textContent = number;
            cells[i].classList.add('locked');
        } else {
            cells[i].textContent = '';
        }
    }
}

btnPencil.addEventListener('click', function(){
    isPencilMode = !isPencilMode;
    if (isPencilMode){
        btnPencil.classList.add('active-tool');
    } else {
        btnPencil.classList.remove('active-tool');
    }
});

btnEraser.addEventListener('click', function(){
    if (selectedCell && !selectedCell.classList.contains('locked')){
        saveMoveToHistory(selectedCell);
        selectedCell.textContent = '';
        selectedCell.classList.remove('user-filled', 'notes', 'mistake');
    }
});

btnUndo.addEventListener('click', function(){
    if (moveHistory.length>0){
        const lastMove = moveHistory.pop();
        const cell = lastMove.cell;
        cell.textContent = lastMove.oldText;
        cell.className = lastMove.oldClass;

        if (selectedCell){
            selectedCell.classList.remove('selected');
        }
        cell.classList.add('selected');
        selectedCell = cell;
    }
});

function saveMoveToHistory(cell){
    moveHistory.push({
        cell: cell,
        oldText: cell.textContent,
        oldClass: cell.className
    });
}

document.addEventListener('keydown', async function(e){
    if (!selectedCell || selectedCell.classList.contains('locked')) return;
    const cellIndex = Array.from(boardElement.children).indexOf(selectedCell);
    const row = Math.floor(cellIndex / 9);
    const col = cellIndex % 9;
    if (e.key >= '1' && e.key <='9'){
        const newValue = e.key;
        if (isPencilMode){
            saveMoveToHistory(selectedCell);
            let currentNodes = selectedCell.classList.contains('notes') ? selectedCell.textContent : '';
            if (currentNodes.includes(newValue)){
                currentNodes = currentNodes.replace(newValue, '');
            } else {
                currentNodes += newValue;
                currentNodes = currentNodes.split('').sort().join('');
            }
            selectedCell.textContent = currentNodes;
            selectedCell.classList.add('notes');
            selectedCell.classList.remove('user-filled');
        } else {
            saveMoveToHistory(selectedCell);
            selectedCell.textContent = newValue;
            selectedCell.classList.add('user-filled');
            selectedCell.classList.remove('notes');
            try {
                const response = await fetch('/check_move', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ row: row, col: col, value: newValue })
                });
                const data = await response.json();
                if (data.is_correct){
                    selectedCell.classList.remove('mistake');
                    removeNotesFromPeers(row, col, newValue);
                    checkWinCondition();
                } else {
                    selectedCell.classList.add('mistake');
                    mistakes++;
                    mistakesDisplay.textContent = `Mistakes: ${mistakes}/3`;
                    if (mistakes >= 3){
                        setTimeout(() => triggerGameOver(false), 100);
                    }
                }
            } catch (error) {
                console.error("Error checking move:", error);
            }
        }
    }
    else if (e.key === 'Backspace' || e.key === 'Delete'){
        if (selectedCell.textContent !== ''){
            saveMoveToHistory(selectedCell);
            selectedCell.textContent = '';
            selectedCell.classList.remove('user-filled', 'notes', 'mistake');
        }
    }
});

function removeNotesFromPeers(row, col, value){
    const cells = document.querySelectorAll('.cell');
    const boxRowStart = Math.floor(row / 3) * 3;
    const boxColStart = Math.floor(col / 3) * 3;

    cells.forEach((cell, index) => {
        const r = Math.floor(index/9);
        const c = index % 9;
        const inSameBox = (r >= boxRowStart && r < boxRowStart+3 && c >= boxColStart && c < boxColStart+3);
        if (r === row || c === col || inSameBox){
            if (cell.classList.contains('notes') && cell.textContent.includes(value)){
                cell.textContent = cell.textContent.replace(value, '');
                if (cell.textContent === ''){
                    cell.classList.remove('notes');
                }
            }
        }
    });
}

function checkWinCondition(){
    const cells = document.querySelectorAll('.cell');
    for (let i=0; i<81; i++){
        if (cells[i].textContent === '' || cells[i].classList.contains('notes') || cells[i].classList.contains('mistake')){
            return;
        }
    }
    triggerGameOver(true);
}

function triggerGameOver(isWin){
    isGameOver = true;
    stopTimer();
    if (isLoggedIn){
        fetch('/clear_saved_game', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                isWin: isWin,
                mistakes: mistakes
            })
        });
    }
    gameOverModal.classList.remove('hidden');
    finalTimeDisplay.textContent = timerDisplay.textContent;
    if (isWin) {
        modalIcon.textContent = "🏆";
        modalTitle.textContent = "You Won!";
        spawnConfetti();
    } else {
        modalIcon.textContent = "💔";
        modalTitle.textContent = "Game Over!";
        spawnEmojis();
    }
    finalTimeDisplay.textContent = timerDisplay.textContent;
    gameOverModal.classList.remove('hidden');
}

closeModalBtn.addEventListener('click', () => window.location.reload());
gameOverModal.addEventListener('click', (e) => {
    if (e.target === gameOverModal) window.location.reload();
});

function spawnEmojis(){
    for (let i = 0; i<40; i++){
        const emoji = document.createElement('div');
        emoji.classList.add('emoji-drop');
        emoji.textContent = "😭";
        emoji.style.left = Math.random() * 100 + "vw";
        emoji.style.animationDuration = (Math.random() * 2 + 2) + "s";
        emoji.style.animationDelay = (Math.random() * 1.5) + "s";
        animationContainer.appendChild(emoji);
    }
}

function spawnConfetti(){
    const colors = ['#f44336', '#e91e63', '#9c27b0', '#2196f3', '#4caf50', '#ffeb3b', '#ff9800'];
    for (let i=0; i<100; i++){
        const confetti = document.createElement('div');
        confetti.classList.add('confetti');
        const isLeft = Math.random() > 0.5;
        confetti.style.left = isLeft ? (Math.random() * 20 + "vw") : ((80 + Math.random() * 20) + "vw");
        confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        confetti.style.animationDuration = (Math.random() * 1.5 + 1.5) + "s";
        confetti.style.animationDelay = (Math.random() * 0.5) + "s";
        animationContainer.appendChild(confetti);
    }
}

async function saveGameState() {
    if (!isLoggedIn || !gameView.classList.contains('active') || isGameOver) return;
    const cells = document.querySelectorAll('.cell');
    let gridData = [];
    cells.forEach(cell => {
        gridData.push({
            text: cell.textContent,
            isLocked: cell.classList.contains('locked'),
            isUserFilled: cell.classList.contains('user-filled'),
            isNotes: cell.classList.contains('notes'),
            isMistake: cell.classList.contains('mistake')
        });
    });
    await fetch('/save_game', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            grid: gridData,
            mistakes: mistakes,
            time: secondsElapsed
        })
    });
}
setInterval(saveGameState, 5000)

document.querySelectorAll('.numpad-btn').forEach(button => {
    button.addEventListener('click', function() {
        if (isGameOver || !selectedCell) return;
        const val = this.getAttribute('data-value');
        const keyToSimulate = (val === "0") ? "Backspace" : val;
        document.dispatchEvent(new KeyboardEvent('keydown', { 'key': keyToSimulate }));
    });
});