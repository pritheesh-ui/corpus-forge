(() => {
  const chat = window.__CHAT__;
  const modes = window.__MODES__ || {};
  if (!chat) return;

  const messagesEl = document.getElementById("messages");
  const form = document.getElementById("message-form");
  const input = document.getElementById("composer-input");
  const sendBtn = document.getElementById("send-btn");

  const settingsToggle = document.getElementById("settings-toggle");
  const settingsPanel = document.getElementById("settings-panel");
  const settingsMode = document.getElementById("settings-mode");
  const settingsOptions = document.getElementById("settings-options");
  const settingsSave = document.getElementById("settings-save");
  const settingsStatus = document.getElementById("settings-status");

  const renderSettings = (preserveValues = false) => {
    const previous = preserveValues ? collect(settingsOptions) : null;
    window.__renderModeOptions(modes[settingsMode.value], settingsOptions, "settings");
    const source = preserveValues ? previous : (chat.options || {});
    settingsOptions.querySelectorAll("select").forEach(sel => {
      const v = source[sel.name];
      if (v !== undefined && v !== null) sel.value = String(v);
    });
  };
  renderSettings();

  settingsMode.addEventListener("change", () => renderSettings(false));
  settingsToggle.addEventListener("click", () => settingsPanel.classList.toggle("hidden"));

  settingsSave.addEventListener("click", async () => {
    settingsStatus.textContent = "Saving…";
    try {
      const options = collect(settingsOptions);
      const res = await fetch(`/chats/${chat.id}/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: settingsMode.value, options, title: null }),
      });
      if (!res.ok) throw new Error(await res.text());
      chat.mode = settingsMode.value;
      chat.options = options;
      settingsStatus.textContent = "Saved.";
      setTimeout(() => (settingsStatus.textContent = ""), 1500);
    } catch (err) {
      settingsStatus.textContent = `Error: ${err.message}`;
    }
  });

  input.addEventListener("keydown", e => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      form.requestSubmit();
    }
  });

  form.addEventListener("submit", async e => {
    e.preventDefault();
    const content = input.value.trim();
    if (!content) return;

    const docIds = selectedDocIds();

    appendMessage("user", content);
    const pending = appendMessage("assistant", "…", true);

    input.value = "";
    input.disabled = true;
    sendBtn.disabled = true;

    try {
      const res = await fetch(`/chats/${chat.id}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content, document_ids: docIds }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || res.statusText);
      }
      const data = await res.json();
      replacePending(pending, data.assistant.content, data.assistant.sources || []);
    } catch (err) {
      replacePending(pending, `[Error: ${err.message}]`, []);
    } finally {
      input.disabled = false;
      sendBtn.disabled = false;
      input.focus();
    }
  });

  function selectedDocIds() {
    const ids = [];
    document.querySelectorAll(".doc-checkbox:checked").forEach(c => ids.push(parseInt(c.value, 10)));
    return ids.filter(Number.isFinite);
  }

  function appendMessage(role, content, pending = false) {
    const empty = messagesEl.querySelector(".msg-empty");
    if (empty) empty.remove();

    const article = document.createElement("article");
    article.className = `msg msg-${role}${pending ? " msg-pending" : ""}`;
    article.innerHTML = `
      <div class="msg-role">${role}</div>
      <div class="msg-body"></div>
    `;
    article.querySelector(".msg-body").textContent = content;
    messagesEl.appendChild(article);
    article.scrollIntoView({ behavior: "smooth", block: "end" });
    return article;
  }

  function replacePending(article, content, sources) {
    article.classList.remove("msg-pending");
    article.querySelector(".msg-body").textContent = content;
    if (sources && sources.length) {
      const details = document.createElement("details");
      details.className = "msg-sources";
      const items = sources
        .map(s => `
          <li>
            <code>${escapeHtml(s.document_name)} #${s.position}</code>
            <span class="msg-source-score">score ${s.score}</span>
            <p>${escapeHtml((s.preview || "").slice(0, 280))}${(s.preview || "").length >= 280 ? "…" : ""}</p>
          </li>
        `)
        .join("");
      details.innerHTML = `
        <summary>${sources.length} source${sources.length === 1 ? "" : "s"}</summary>
        <ol>${items}</ol>
      `;
      article.appendChild(details);
    }
  }

  function collect(container) {
    return window.__collectOptions(container);
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
})();
