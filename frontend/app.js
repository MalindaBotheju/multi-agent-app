// IMPORTANT: change this to your actual Render URL after deploying the backend.
const API_BASE_URL = "https://your-app-name.onrender.com";

let currentReviewId = null;

async function runPipeline() {
  const question = document.getElementById("question").value.trim();
  if (!question) return;

  setStatus("Running the pipeline... this can take a minute.");
  document.getElementById("report").textContent = "";
  document.getElementById("reviewSection").style.display = "none";

  const res = await fetch(`${API_BASE_URL}/pipeline/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!res.ok) {
    setStatus(`Error: ${res.status} ${await res.text()}`);
    return;
  }

  const data = await res.json();
  currentReviewId = data.review_id;
  document.getElementById("report").textContent = data.report;
  document.getElementById("reviewSection").style.display = "block";
  setStatus("");
}

async function approve() {
  await submitDecision({ decision: "approve" });
}

function showRejectForm() {
  document.getElementById("rejectForm").style.display = "block";
}

async function reject() {
  const reason = document.getElementById("reason").value;
  const comment = document.getElementById("comment").value;
  await submitDecision({ decision: "reject", reason, comment });
}

async function submitDecision(body) {
  setStatus("Submitting your decision...");
  const res = await fetch(`${API_BASE_URL}/pipeline/review/${currentReviewId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    setStatus(`Error: ${res.status} ${await res.text()}`);
    return;
  }

  const data = await res.json();

  if (data.status === "APPROVED") {
    setStatus("Approved! Final report above.");
    document.getElementById("reviewSection").style.display = "none";
  } else if (data.status === "REJECTED") {
    setStatus(`Rejected permanently: ${data.detail}`);
    document.getElementById("reviewSection").style.display = "none";
  } else {
    // Another round: new report to review
    currentReviewId = data.review_id;
    document.getElementById("report").textContent = data.report;
    document.getElementById("rejectForm").style.display = "none";
    setStatus(`Revised report ready (rejection ${data.rejections_so_far} so far).`);
  }
}

function setStatus(msg) {
  const el = document.getElementById("status");
  el.textContent = msg;
  el.style.display = msg ? "block" : "none";
}
