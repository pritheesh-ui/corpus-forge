(() => {
  const modes = window.__MODES__ || {};

  const uploadForm = document.getElementById("upload-form");
  const uploadInput = document.getElementById("upload-input");
  const uploadDrop = document.querySelector(".upload-drop");
  const uploadSubmit = document.querySelector(".upload-submit");
  const uploadStatus = document.getElementById("upload-status");

  if (uploadInput) {
    uploadInput.addEventListener("change", () => {
      uploadSubmit.disabled = uploadInput.files.length === 0;
      if (uploadInput.files.length > 0) {
        uploadStatus.textContent = `${uploadInput.files.length} file(s) ready`;
        uploadStatus.className = "upload-status";
      }
    });

    ["dragenter", "dragover"].forEach(evt =>
      uploadDrop.addEventListener(evt, e => {
        e.preventDefault();
        uploadDrop.classList.add("is-drag");
      })
    );
    ["dragleave", "drop"].forEach(evt =>
      uploadDrop.addEventListener(evt, e => {
        e.preventDefault();
        uploadDrop.classList.remove("is-drag");
      })
    );
    uploadDrop.addEventListener("drop", e => {
      uploadInput.files = e.dataTransfer.files;
      uploadInput.dispatchEvent(new Event("change"));
    });

    uploadForm.addEventListener("submit", async e => {
      e.preventDefault();
      if (!uploadInput.files.length) return;

      const formData = new FormData();
      for (const file of uploadInput.files) {
        formData.append("files", file);
      }

      uploadSubmit.disabled = true;
      uploadStatus.textContent = "Uploading…";
      uploadStatus.className = "upload-status";

      try {
        const res = await fetch("/files/upload", { method: "POST", body: formData });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();

        let msg = `Saved ${data.saved}`;
        if (data.skipped && data.skipped.length) {
          msg += ` · skipped: ${data.skipped.join(", ")}`;
        }
        uploadStatus.textContent = msg;
        uploadStatus.className = "upload-status is-ok";
        setTimeout(() => window.location.reload(), 500);
      } catch (err) {
        uploadStatus.textContent = `Failed: ${err.message}`;
        uploadStatus.className = "upload-status is-err";
        uploadSubmit.disabled = false;
      }
    });
  }

  const newChatBtn = document.getElementById("new-chat-btn");
  const dialog = document.getElementById("new-chat-dialog");

  if (newChatBtn && dialog) {
    const form = document.getElementById("new-chat-form");
    const modeSelect = document.getElementById("new-chat-mode");
    const optionsBox = document.getElementById("new-chat-options");
    const titleInput = form.querySelector("input[name='title']");

    const renderOptions = () => {
      renderModeOptions(modes[modeSelect.value], optionsBox, "new");
    };

    modeSelect.addEventListener("change", renderOptions);

    document.querySelectorAll(".mode-card").forEach(card => {
      card.addEventListener("click", () => {
        modeSelect.value = card.dataset.mode;
        renderOptions();
        openDialog();
      });
    });

    newChatBtn.addEventListener("click", () => {
      modeSelect.value = "ask";
      renderOptions();
      openDialog();
    });

    dialog.querySelectorAll("[data-close]").forEach(el =>
      el.addEventListener("click", () => dialog.close())
    );

    form.addEventListener("submit", async e => {
      e.preventDefault();
      const mode = modeSelect.value;
      const options = collectOptions(optionsBox);
      const title = (titleInput.value || "").trim() || null;

      try {
        const res = await fetch("/chats/new", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title, mode, options }),
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        window.location.href = `/chat/${data.id}`;
      } catch (err) {
        alert(`Could not create chat: ${err.message}`);
      }
    });

    function openDialog() {
      titleInput.value = "";
      if (typeof dialog.showModal === "function") {
        dialog.showModal();
      } else {
        dialog.setAttribute("open", "open");
      }
    }
  }

  function renderModeOptions(spec, container, scope) {
    container.innerHTML = "";
    if (!spec) return;
    for (const [key, values] of Object.entries(spec.options || {})) {
      const label = document.createElement("label");
      label.className = "field";

      const span = document.createElement("span");
      span.className = "field-label";
      span.textContent = key.replace(/_/g, " ");
      label.appendChild(span);

      const select = document.createElement("select");
      select.name = key;
      select.dataset.scope = scope;
      values.forEach(v => {
        const opt = document.createElement("option");
        opt.value = String(v);
        opt.textContent = String(v).replace(/_/g, " ");
        select.appendChild(opt);
      });
      label.appendChild(select);
      container.appendChild(label);
    }
  }

  function collectOptions(container) {
    const result = {};
    container.querySelectorAll("select").forEach(sel => {
      const value = sel.value;
      const asNumber = Number(value);
      result[sel.name] = Number.isFinite(asNumber) && String(asNumber) === value ? asNumber : value;
    });
    return result;
  }

  window.__renderModeOptions = renderModeOptions;
  window.__collectOptions = collectOptions;
})();
