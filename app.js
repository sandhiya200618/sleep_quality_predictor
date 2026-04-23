/* ── SleepSense — app.js ────────────────────────────────────────────────── */

let selectedAlgo = "Random Forest";

// ── Algorithm tabs ────────────────────────────────────────────────────────
document.querySelectorAll(".algo-tab").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".algo-tab").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    selectedAlgo = btn.dataset.algo;
  });
});

// ── Slider ────────────────────────────────────────────────────────────────
function updateSlider(el, displayId) {
  document.getElementById(displayId).textContent = el.value;
  const pct = (el.value / el.max) * 100;
  el.style.setProperty("--val", pct + "%");
  el.style.background = `linear-gradient(to right,
    var(--accent) 0%, var(--accent) ${pct}%,
    var(--mid) ${pct}%, var(--mid) 100%)`;
}
updateSlider(document.getElementById("stress_level"), "stress-display");

// ── Radio toggle ──────────────────────────────────────────────────────────
document.querySelectorAll("input[name='interruptions']").forEach(r => {
  r.closest(".radio-btn").addEventListener("click", function () {
    document.querySelectorAll(".radio-btn").forEach(b => b.classList.remove("active"));
    this.classList.add("active");
    this.querySelector("input").checked = true;
  });
});

// ── Predict ───────────────────────────────────────────────────────────────
async function predict() {
  const payload = {
    sleep_duration:    parseFloat(document.getElementById("sleep_duration").value) || 7,
    exercise_minutes:  parseFloat(document.getElementById("exercise_minutes").value) || 0,
    screen_time:       parseFloat(document.getElementById("screen_time").value) || 0,
    stress_level:      parseInt(document.getElementById("stress_level").value),
    caffeine:          document.getElementById("caffeine").value,
    mood:              document.getElementById("mood").value,
    interruptions:     document.querySelector("input[name='interruptions']:checked").value,
    bedtime:           document.getElementById("bedtime").value,
    algorithm:         selectedAlgo,
  };

  // UI feedback
  const btn = document.getElementById("predict-btn");
  document.getElementById("btn-text").style.display = "none";
  document.getElementById("btn-loader").style.display = "inline";
  btn.disabled = true;

  try {
    const res  = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.error) { alert(data.error); return; }
    renderResult(data);
  } catch (e) {
    alert("Server error: " + e.message);
  } finally {
    document.getElementById("btn-text").style.display = "inline";
    document.getElementById("btn-loader").style.display = "none";
    btn.disabled = false;
    btn.classList.add("predicting");
    setTimeout(() => btn.classList.remove("predicting"), 1600);
  }
}

// ── Render result ─────────────────────────────────────────────────────────
function renderResult(data) {
  document.getElementById("result-section").style.display = "block";
  document.getElementById("result-section").scrollIntoView({ behavior: "smooth", block: "start" });

  // Badge
  const emojiMap = { Good: "🌟", Average: "🌕", Poor: "😔" };
  const clsMap   = { Good: "quality-good", Average: "quality-avg", Poor: "quality-poor" };
  const badge    = document.getElementById("quality-badge");
  badge.textContent = `${data.quality} ${emojiMap[data.quality] || ""}`;
  badge.className   = `quality-badge ${clsMap[data.quality]}`;

  document.getElementById("result-algo").textContent = `via ${data.algorithm}`;

  // Score arc
  const arc = document.getElementById("score-arc");
  const offset = 314 - (data.score / 100) * 314;
  setTimeout(() => { arc.style.strokeDashoffset = offset; }, 80);
  document.getElementById("score-num").textContent = data.score;

  // Confidence
  document.getElementById("conf-num").textContent = data.confidence + "%";
  setTimeout(() => { document.getElementById("conf-fill").style.width = data.confidence + "%"; }, 200);

  // Probability bars
  const colorMap = { Good: "var(--good)", Average: "var(--avg)", Poor: "var(--poor)" };
  const probaEl  = document.getElementById("proba-bars");
  probaEl.innerHTML = Object.entries(data.proba).map(([cls, pct]) => `
    <div class="proba-row">
      <span class="proba-label">${cls}</span>
      <div class="proba-bar-bg">
        <div class="proba-bar-fill" style="width:0%;background:${colorMap[cls]};transition:width .8s ease"
             data-w="${pct}"></div>
      </div>
      <span class="proba-pct">${pct}%</span>
    </div>
  `).join("");
  setTimeout(() => {
    probaEl.querySelectorAll(".proba-bar-fill").forEach(el => {
      el.style.width = el.dataset.w + "%";
    });
  }, 100);

  // Importances
  renderFactors(data.importances);

  // Tips
  renderTips(data.tips);
}

// ── Feature importances ───────────────────────────────────────────────────
const FACTOR_COLORS = {
  "Sleep Duration": "#4d6fff", "Exercise": "#4ecdc4",
  "Screen Time": "#b47bff",   "Stress Level": "#ff6b6b",
  "Caffeine": "#ffd166",      "Mood": "#ff9ff3",
  "Interruptions": "#a8edea", "Bedtime": "#7b8fff",
};

function renderFactors(importances) {
  const container = document.getElementById("factors-container");
  const sorted = Object.entries(importances).sort((a, b) => b[1] - a[1]);
  container.innerHTML = sorted.map(([name, val]) => `
    <div class="factor-row">
      <div class="factor-name">${name}</div>
      <div class="factor-bar">
        <div class="factor-fill" style="width:0%;background:${FACTOR_COLORS[name] || "var(--accent)"}"
             data-w="${val}"></div>
      </div>
      <div class="factor-val">${val}%</div>
    </div>
  `).join("");
  setTimeout(() => {
    container.querySelectorAll(".factor-fill").forEach(el => {
      el.style.cssText += `width:${el.dataset.w}%;transition:width 1s ease;`;
    });
  }, 60);
}

// ── Tips ──────────────────────────────────────────────────────────────────
function renderTips(tips) {
  document.getElementById("tips-container").innerHTML = tips.map((t, i) => `
    <div class="tip-item" style="animation-delay:${i * 0.07}s">
      <span class="tip-icon">${t.icon}</span>
      <span>${t.text}</span>
    </div>
  `).join("");
}

// ── Reset ─────────────────────────────────────────────────────────────────
function resetForm() {
  document.getElementById("sleep_duration").value  = "";
  document.getElementById("exercise_minutes").value = "";
  document.getElementById("screen_time").value     = "";
  document.getElementById("bedtime").value         = "23:00";
  document.getElementById("waketime").value        = "06:30";
  document.getElementById("caffeine").value        = "low";
  document.getElementById("mood").value            = "neutral";
  document.getElementById("stress_level").value   = 5;
  updateSlider(document.getElementById("stress_level"), "stress-display");
  document.querySelectorAll("input[name='interruptions']")[0].checked = true;
  document.querySelectorAll(".radio-btn")[0].classList.add("active");
  document.querySelectorAll(".radio-btn")[1].classList.remove("active");
  document.getElementById("result-section").style.display = "none";
}

// ── Toggle panels ─────────────────────────────────────────────────────────
function togglePanel(id) {
  const el = document.getElementById(id);
  el.style.display = el.style.display === "none" || !el.style.display ? "block" : "none";
  if (el.style.display === "block") el.scrollIntoView({ behavior: "smooth" });
}

// ── History ───────────────────────────────────────────────────────────────
async function loadHistory() {
  const res  = await fetch("/history");
  const list = await res.json();
  const el   = document.getElementById("history-content");
  if (!list.length) {
    el.innerHTML = '<p class="empty-msg">No history yet. Make your first prediction!</p>';
    return;
  }
  const colorMap = { Good: "var(--good)", Average: "var(--avg)", Poor: "var(--poor)" };
  const bgMap    = {
    Good:    "rgba(78,205,196,.15)",
    Average: "rgba(255,209,102,.15)",
    Poor:    "rgba(255,107,107,.15)",
  };
  el.innerHTML = `
    <table class="history-table">
      <thead><tr><th>Date</th><th>Time</th><th>Score</th><th>Quality</th><th>Algorithm</th></tr></thead>
      <tbody>
        ${list.map(e => `
          <tr>
            <td>${e.date}</td>
            <td>${e.time}</td>
            <td style="color:var(--accent);font-weight:700">${e.score}</td>
            <td><span class="badge" style="color:${colorMap[e.quality]};background:${bgMap[e.quality]}">${e.quality}</span></td>
            <td style="color:var(--muted);font-size:.8rem">${e.algorithm}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>`;
}

// Override togglePanel for history to load fresh data
const _origToggle = togglePanel;
function togglePanel(id) {
  _origToggle(id);
  if (id === "history-section" && document.getElementById(id).style.display === "block") {
    loadHistory();
  }
}

// ── Model Accuracy ────────────────────────────────────────────────────────
async function loadAccuracy() {
  const el = document.getElementById("accuracy-content");
  if (el.dataset.loaded) return;
  try {
    const res  = await fetch("/model-accuracy");
    const data = await res.json();
    el.innerHTML = Object.entries(data)
      .sort((a, b) => b[1] - a[1])
      .map(([name, acc]) => `
        <div class="acc-row">
          <div class="acc-name">${name}</div>
          <div class="acc-bar"><div class="acc-fill" style="width:0%" data-w="${acc}"></div></div>
          <div class="acc-pct">${acc}%</div>
        </div>
      `).join("") + `<p style="color:var(--muted);font-size:.78rem;margin-top:16px;">
        Trained on 2,000 synthetic records — split 80/20 train/test.</p>`;
    setTimeout(() => {
      el.querySelectorAll(".acc-fill").forEach(b => {
        b.style.cssText += `width:${b.dataset.w}%;transition:width 1s ease;`;
      });
    }, 80);
    el.dataset.loaded = "1";
  } catch (e) {
    el.innerHTML = '<p class="empty-msg">Could not load accuracy data.</p>';
  }
}
