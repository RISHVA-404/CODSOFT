document.addEventListener("DOMContentLoaded", function () {

// --- Global Variables ---
let simulationRunning = false;
let currentTimeout = null;
let currentEmergency = false;
let timerInterval = null;

const totalResources = [1, 20, 4];
const LANES = ['North', 'South', 'East', 'West'];

let processes = [];
let available = [...totalResources];
let safeSequenceFound = [];
let activeVehicles = { 'North': [], 'South': [], 'East': [], 'West': [] };

// DOM Elements
const inputUI = {
    'North': document.getElementById('in-N'),
    'South': document.getElementById('in-S'),
    'East': document.getElementById('in-E'),
    'West': document.getElementById('in-W')
};

const errorMsg = document.getElementById('error-msg');
const tableBody = document.getElementById('banker-table-body');
const stateBadge = document.getElementById('system-state');
const sequenceBox = document.getElementById('safe-sequence-display');
const availSpan = document.getElementById('avail-res');
const countdownTimer = document.getElementById('countdown-timer');
const activeLaneDisplay = document.getElementById('active-lane-display');
const intersectionContainer = document.getElementById('intersection-container');

// Lane configuration
const LANE_CONFIG = {
    'North': { startX: 162, startY: 100, gap: -55, axis: 'top', class: 'v-up-down', moveDir: 450 },
    'South': { startX: 212, startY: 250, gap: 55, axis: 'top', class: 'v-up-down', moveDir: -450 },
    'East': { startY: 162, startX: 250, gap: 55, axis: 'left', class: 'v-left-right', moveDir: -450 },
    'West': { startY: 212, startX: 100, gap: -55, axis: 'left', class: 'v-left-right', moveDir: 450 }
};

// Delay helper
const delay = ms => new Promise(res => {
    currentTimeout = setTimeout(res, ms);
});

// Reset all lights
function resetAllLightsToRed() {
    LANES.forEach(lane => {
        const tl = document.getElementById(`tl-${lane}`);
        const bulbs = tl.querySelectorAll('.bulb');
        bulbs.forEach(b => b.classList.remove('active'));
        tl.querySelector('.red').classList.add('active');
    });
}

// Change signal
function setLight(lane, color) {
    const tl = document.getElementById(`tl-${lane}`);
    const bulbs = tl.querySelectorAll('.bulb');
    bulbs.forEach(b => b.classList.remove('active'));
    tl.querySelector(`.${color}`).classList.add('active');
}

// Render vehicles
function renderVehicles(lane, count) {
    const config = LANE_CONFIG[lane];

    for (let i = 0; i < count; i++) {

        let v = document.createElement('div');
        v.classList.add('vehicle', config.class);

        if (config.axis === 'top') {
            v.style.left = `${config.startX}px`;
            v.style.top = `${config.startY + (i * config.gap)}px`;
        } else {
            v.style.top = `${config.startY}px`;
            v.style.left = `${config.startX + (i * config.gap)}px`;
        }

        intersectionContainer.appendChild(v);
        activeVehicles[lane].push(v);
    }
}

// Clear vehicles
function clearAllVehicles() {
    document.querySelectorAll('.vehicle').forEach(v => v.remove());
    activeVehicles = { 'North': [], 'South': [], 'East': [], 'West': [] };
}

// Initialize processes
function initProcesses() {

    processes = [];
    available = [...totalResources];
    clearAllVehicles();

    LANES.forEach((lane) => {

        let qVal = parseInt(inputUI[lane].value) || 0;

        let allocated = [0, 0, 0];
        let max = qVal > 0 ? [1, Math.min(qVal * 2, 20), 1] : [0, 0, 0];

        let need = [
            max[0] - allocated[0],
            max[1] - allocated[1],
            max[2] - allocated[2]
        ];

        processes.push({
            id: lane,
            queue: qVal,
            allocated,
            max,
            need
        });

        renderVehicles(lane, qVal);
    });

    updateDashboardUI();
}

// Banker's Algorithm
function runBankersAlgorithm() {

    let work = [...totalResources];
    let finish = [false, false, false, false];
    let safeSequence = [];

    let count = 0;

    while (count < processes.length) {

        let found = false;

        for (let p = 0; p < processes.length; p++) {

            if (!finish[p] && processes[p].queue > 0) {

                let canAllocate = true;

                for (let j = 0; j < 3; j++) {
                    if (processes[p].need[j] > work[j]) {
                        canAllocate = false;
                        break;
                    }
                }

                if (canAllocate) {

                    for (let k = 0; k < 3; k++) {
                        work[k] += processes[p].allocated[k];
                    }

                    safeSequence.push(processes[p].id);
                    finish[p] = true;
                    found = true;
                    count++;
                }
            }

            else if (!finish[p] && processes[p].queue === 0) {
                finish[p] = true;
                found = true;
                count++;
            }
        }

        if (!found) return false;
    }

    return safeSequence;
}

// Update dashboard
function updateDashboardUI() {

    tableBody.innerHTML = '';

    processes.forEach(p => {

        const row = document.createElement('tr');

        row.innerHTML = `
        <td>${p.id} (Q:${p.queue})</td>
        <td>[${p.allocated.join(',')}]</td>
        <td>[${p.max.join(',')}]</td>
        <td>[${p.need.join(',')}]</td>
        `;

        tableBody.appendChild(row);
    });

    availSpan.innerText = `[${available.join(', ')}]`;
}

// Timer
function startTimer(duration) {

    clearInterval(timerInterval);

    let timeLeft = duration;

    countdownTimer.innerText = timeLeft;

    timerInterval = setInterval(() => {

        timeLeft--;

        countdownTimer.innerText = timeLeft;

        if (timeLeft <= 0) clearInterval(timerInterval);

    }, 1000);
}

// Execute safe sequence
async function executeSafeSequence(sequence) {

    simulationRunning = true;

    const baseGreenTimeSec = parseInt(document.getElementById('in-time').value) || 5;

    for (let lane of sequence) {

        if (!simulationRunning) break;

        let pIndex = processes.findIndex(p => p.id === lane);
        let carsToClear = processes[pIndex].queue;

        activeLaneDisplay.innerText = lane.toUpperCase();

        setLight(lane, 'green');
        startTimer(baseGreenTimeSec);

        let delayTime = (baseGreenTimeSec * 1000) / (carsToClear + 1);

        for (let i = 0; i < carsToClear; i++) {

            let car = activeVehicles[lane].shift();

            if (car) {

                const config = LANE_CONFIG[lane];

                if (config.axis === 'top')
                    car.style.transform = `translateY(${config.moveDir}px)`
                else
                    car.style.transform = `translateX(${config.moveDir}px)`;

                setTimeout(() => car.remove(), 1500);
            }

            processes[pIndex].queue--;

            await delay(delayTime);
        }

        setLight(lane, 'yellow');
        await delay(2000);

        setLight(lane, 'red');
        await delay(500);
    }

    simulationRunning = false;
    activeLaneDisplay.innerText = "IDLE";
}

// START button
document.getElementById('btn-start').addEventListener('click', () => {

    if (simulationRunning) return;

    resetAllLightsToRed();

    initProcesses();

    safeSequenceFound = runBankersAlgorithm();

    if (!safeSequenceFound) {

        stateBadge.innerText = "UNSAFE STATE";

        return;
    }

    stateBadge.innerText = "SAFE STATE";

    sequenceBox.innerText = safeSequenceFound.join(" ➜ ");

    executeSafeSequence(safeSequenceFound);
});

// Pause
document.getElementById('btn-pause').addEventListener('click', () => {

    simulationRunning = false;

    clearTimeout(currentTimeout);

    clearInterval(timerInterval);
});

// Reset
document.getElementById('btn-reset').addEventListener('click', () => {

    simulationRunning = false;

    clearTimeout(currentTimeout);
    clearInterval(timerInterval);

    resetAllLightsToRed();
    clearAllVehicles();

    initProcesses();

    activeLaneDisplay.innerText = "IDLE";

    stateBadge.innerText = "Reset";
});

// Emergency
document.getElementById('btn-emergency').addEventListener('click', () => {

    currentEmergency = true;

    safeSequenceFound = ['East'];

    executeSafeSequence(safeSequenceFound);
});

// Initialize
initProcesses();
stateBadge.innerText = "Awaiting Start";

});