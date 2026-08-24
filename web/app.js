const messagesEl = document.getElementById("messages");
const historyView = document.getElementById("historyView");
const chatForm = document.getElementById("chatForm");
const userIdInput = document.getElementById("userId");
const messageInput = document.getElementById("messageInput");
const statusBadge = document.getElementById("statusBadge");
const loadHistoryBtn = document.getElementById("loadHistoryBtn");

function addBubble(role, content) {
  const node = document.createElement("div");
  node.className = `bubble ${role}`;
  node.textContent = content;
  messagesEl.appendChild(node);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setStatus(text) {
  statusBadge.textContent = text;
}

async function loadHistory() {
  const userId = userIdInput.value.trim() || "guest";
  const response = await fetch(`/api/history/${encodeURIComponent(userId)}`);
  const payload = await response.json();
  historyView.textContent = JSON.stringify(payload.history || [], null, 2);
  messagesEl.innerHTML = "";
  for (const item of payload.history || []) {
    addBubble(item.role, item.content);
  }
  setStatus(`Loaded ${userId}`);
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const userId = userIdInput.value.trim() || "guest";
  const message = messageInput.value.trim();
  if (!message) return;

  addBubble("user", message);
  messageInput.value = "";
  setStatus("Thinking");

  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, message }),
  });

  const payload = await response.json();
  addBubble("assistant", payload.reply);
  historyView.textContent = JSON.stringify(payload.history || [], null, 2);
  setStatus("Ready");
});

loadHistoryBtn.addEventListener("click", () => {
  loadHistory().catch((error) => {
    setStatus("Error");
    historyView.textContent = error.message;
  });
});

setStatus("Ready");
