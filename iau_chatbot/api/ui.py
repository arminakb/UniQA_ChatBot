"""Plain HTML/JavaScript test UI for the chatbot interface."""

from __future__ import annotations


def render_chat_ui() -> str:
    """Return a lightweight browser UI for manual chatbot testing."""

    return """<!doctype html>
<html lang="fa" dir="ltr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>چت‌بات دانشجویی دانشگاه آزاد اسلامی</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Vazirmatn, IRANSans, Tahoma, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      --ink: #102033;
      --muted: #5c748b;
      --muted-strong: #34516b;
      --blue-900: #0b3b71;
      --blue-800: #0d4f9c;
      --blue-700: #0d63c9;
      --blue-500: #1685e8;
      --blue-100: #dceeff;
      --glass: rgba(255, 255, 255, 0.74);
      --glass-strong: rgba(255, 255, 255, 0.9);
      --border: rgba(92, 153, 220, 0.26);
      --border-strong: rgba(79, 145, 220, 0.42);
      --shadow-soft: 0 22px 70px rgba(25, 103, 210, 0.12);
      --shadow-tight: 0 14px 34px rgba(25, 103, 210, 0.10);
      --radius-xl: 30px;
      --radius-lg: 22px;
      --radius-md: 16px;
      background: #f3f8ff;
      color: var(--ink);
    }
    * {
      box-sizing: border-box;
    }
    html {
      min-height: 100%;
      scrollbar-gutter: stable;
    }
    body {
      margin: 0;
      min-height: 100vh;
      overflow-y: auto;
      background:
        linear-gradient(135deg, rgba(248, 252, 255, 0.98) 0%, rgba(235, 246, 255, 0.96) 45%, rgba(255, 255, 255, 0.98) 100%),
        linear-gradient(90deg, rgba(13, 99, 201, 0.06), transparent 38%, rgba(22, 133, 232, 0.06));
      -webkit-font-smoothing: antialiased;
      text-rendering: optimizeLegibility;
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(13, 99, 201, 0.055) 1px, transparent 1px),
        linear-gradient(90deg, rgba(13, 99, 201, 0.045) 1px, transparent 1px);
      background-size: 44px 44px;
      mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.58), transparent 78%);
      -webkit-mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.58), transparent 78%);
    }
    .app {
      position: relative;
      z-index: 1;
      direction: rtl;
      min-height: 100vh;
    }
    .brand-lockup {
      position: fixed;
      top: 18px;
      left: 18px;
      z-index: 30;
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 15px 10px 10px;
      border-radius: 20px;
      border: 1px solid var(--border);
      background:
        linear-gradient(135deg, rgba(255, 255, 255, 0.88), rgba(245, 250, 255, 0.66)),
        rgba(255, 255, 255, 0.72);
      box-shadow: var(--shadow-tight);
      backdrop-filter: blur(22px) saturate(140%);
      -webkit-backdrop-filter: blur(22px) saturate(140%);
      transition: transform 180ms ease, box-shadow 180ms ease, background 180ms ease, border-color 180ms ease;
    }
    .brand-lockup:hover {
      transform: translateY(-2px);
      box-shadow: 0 20px 54px rgba(25, 103, 210, 0.16);
      border-color: var(--border-strong);
      background:
        linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(248, 252, 255, 0.78)),
        rgba(255, 255, 255, 0.82);
    }
    .brand-logo {
      width: 44px;
      height: 44px;
      object-fit: contain;
      border-radius: 14px;
      padding: 4px;
      background: rgba(255, 255, 255, 0.92);
      border: 1px solid rgba(89, 150, 218, 0.20);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
      flex: none;
    }
    .brand-text {
      display: grid;
      gap: 2px;
      min-width: 0;
    }
    .brand-name {
      margin: 0;
      font-size: 14.5px;
      line-height: 1.35;
      color: var(--blue-900);
      font-weight: 800;
      letter-spacing: 0;
      white-space: nowrap;
    }
    .brand-subtitle {
      margin: 0;
      font-size: 12px;
      line-height: 1.35;
      color: var(--muted);
      white-space: nowrap;
    }
    button {
      border: 0;
      border-radius: 14px;
      background: linear-gradient(135deg, var(--blue-700), var(--blue-500));
      color: #ffffff;
      padding: 12px 18px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
      min-width: 126px;
      box-shadow: 0 16px 32px rgba(13, 99, 201, 0.20);
      transition: transform 180ms ease, box-shadow 180ms ease, filter 180ms ease, opacity 180ms ease;
    }
    button:disabled {
      cursor: progress;
      opacity: 0.72;
    }
    button:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 18px 36px rgba(13, 99, 201, 0.26);
      filter: brightness(1.02);
    }
    button:active:not(:disabled) {
      transform: translateY(0);
      box-shadow: 0 12px 24px rgba(13, 99, 201, 0.18);
    }
    .settings-toggle {
      position: fixed;
      top: 18px;
      right: 18px;
      z-index: 20;
      min-width: 46px;
      width: 46px;
      height: 46px;
      padding: 0;
      border-radius: 50%;
      font-size: 18px;
      line-height: 1;
      color: var(--blue-800);
      background: rgba(255, 255, 255, 0.82);
      border: 1px solid var(--border);
      box-shadow: var(--shadow-tight);
      backdrop-filter: blur(18px);
      -webkit-backdrop-filter: blur(18px);
    }
    .settings-panel {
      position: fixed;
      top: 76px;
      right: 18px;
      z-index: 19;
      width: min(360px, calc(100vw - 32px));
      padding: 20px;
      opacity: 0;
      visibility: hidden;
      pointer-events: none;
      transform: translateY(-8px) scale(0.98);
      background:
        linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(244, 250, 255, 0.76)),
        rgba(255, 255, 255, 0.84);
      border: 1px solid var(--border-strong);
      border-radius: 22px;
      box-shadow: 0 26px 80px rgba(25, 103, 210, 0.16);
      backdrop-filter: blur(24px) saturate(150%);
      -webkit-backdrop-filter: blur(24px) saturate(150%);
      transition: opacity 180ms ease, transform 180ms ease;
    }
    .settings-panel.open {
      opacity: 1;
      visibility: visible;
      pointer-events: auto;
      transform: translateY(0) scale(1);
    }
    .settings-panel h2 {
      margin: 0 0 14px;
      font-size: 16px;
      color: var(--blue-900);
      letter-spacing: 0;
    }
    .settings-form {
      display: grid;
      gap: 14px;
    }
    label {
      display: grid;
      gap: 6px;
      color: var(--muted-strong);
      font-size: 13px;
      font-weight: 700;
    }
    input,
    textarea {
      width: 100%;
      border: 1px solid rgba(104, 162, 224, 0.48);
      border-radius: 14px;
      padding: 12px 13px;
      font: inherit;
      color: var(--ink);
      background: rgba(255, 255, 255, 0.84);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
      transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease, background 160ms ease;
    }
    input:focus,
    textarea:focus {
      outline: 3px solid rgba(47, 111, 237, 0.18);
      outline-offset: 2px;
      border-color: #1d6fd4;
      box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.86),
        0 0 0 4px rgba(29, 111, 212, 0.08);
    }
    .settings-actions {
      display: flex;
      justify-content: flex-start;
    }
    .settings-status {
      min-height: 20px;
      color: var(--muted);
      font-size: 13px;
    }
    main {
      width: 100%;
      min-height: 100vh;
      margin: 0;
      padding: 28px clamp(16px, 2.4vw, 34px) 24px;
      display: grid;
      grid-template-rows: auto 1fr;
      gap: 24px;
    }
    header {
      text-align: center;
      display: grid;
      justify-items: center;
      gap: 10px;
      min-height: 162px;
      align-content: center;
      padding: 8px clamp(96px, 14vw, 190px) 0;
    }
    .hero-mark {
      width: 98px;
      height: 98px;
      object-fit: contain;
      border-radius: 26px;
      padding: 13px;
      background:
        linear-gradient(145deg, rgba(255, 255, 255, 0.9), rgba(232, 244, 255, 0.72)),
        rgba(255, 255, 255, 0.76);
      border: 1px solid var(--border);
      box-shadow:
        0 22px 54px rgba(30, 92, 160, 0.14),
        inset 0 1px 0 rgba(255, 255, 255, 0.88);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
    }
    h1 {
      font-size: clamp(24px, 2.6vw, 34px);
      margin: 0;
      letter-spacing: 0;
      color: var(--blue-900);
      font-weight: 900;
    }
    .chat-shell {
      min-height: calc(100vh - 238px);
      display: grid;
      grid-template-rows: 1fr auto;
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.70), rgba(247, 251, 255, 0.54)),
        rgba(255, 255, 255, 0.62);
      border: 1px solid var(--border);
      border-radius: var(--radius-xl);
      box-shadow: var(--shadow-soft);
      backdrop-filter: blur(26px) saturate(150%);
      -webkit-backdrop-filter: blur(26px) saturate(150%);
      overflow: hidden;
    }
    .messages {
      min-height: calc(100vh - 360px);
      overflow: visible;
      padding: clamp(24px, 3.4vw, 52px) clamp(18px, 5vw, 86px) 32px;
      display: flex;
      flex-direction: column;
      gap: 22px;
    }
    .empty-state {
      margin: auto;
      width: min(620px, 100%);
      text-align: center;
      color: var(--muted-strong);
      line-height: 1.9;
      font-size: 16px;
      font-weight: 650;
      padding: 26px 28px;
      border: 1px solid rgba(104, 162, 224, 0.24);
      border-radius: 24px;
      background:
        linear-gradient(135deg, rgba(255, 255, 255, 0.84), rgba(237, 247, 255, 0.62)),
        rgba(255, 255, 255, 0.64);
      box-shadow:
        0 20px 60px rgba(25, 103, 210, 0.08),
        inset 0 1px 0 rgba(255, 255, 255, 0.88);
      backdrop-filter: blur(18px);
      -webkit-backdrop-filter: blur(18px);
    }
    .message {
      display: grid;
      gap: 9px;
      margin-left: auto;
      margin-right: 0;
      animation: message-in 170ms ease-out;
    }
    .message.user {
      align-self: flex-start;
      max-width: min(720px, 78%);
    }
    .message.assistant {
      align-self: flex-start;
      max-width: min(940px, 90%);
      text-align: right;
    }
    .message-role {
      font-size: 12px;
      font-weight: 700;
      color: var(--muted);
      padding-inline: 4px;
    }
    .bubble {
      line-height: 1.85;
      padding: 17px 19px;
      border-radius: 21px;
      box-shadow: 0 14px 34px rgba(25, 103, 210, 0.08);
      transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease, background 160ms ease;
    }
    .user .bubble {
      color: #ffffff;
      background:
        linear-gradient(135deg, var(--blue-700), var(--blue-500)),
        #0d63c9;
      border-top-right-radius: 8px;
      box-shadow: 0 18px 42px rgba(13, 99, 201, 0.22);
    }
    .assistant .bubble {
      color: var(--ink);
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(247, 251, 255, 0.84)),
        rgba(255, 255, 255, 0.86);
      border: 1px solid rgba(104, 162, 224, 0.24);
      border-top-right-radius: 8px;
    }
    .user .bubble {
      white-space: pre-wrap;
    }
    .assistant .bubble {
      font-size: 15.5px;
      direction: rtl;
      text-align: right;
      line-height: 2;
    }
    .assistant .bubble h1,
    .assistant .bubble h2,
    .assistant .bubble h3 {
      margin: 14px 0 8px;
      color: var(--blue-900);
      font-weight: 800;
      line-height: 1.55;
      letter-spacing: 0;
    }
    .assistant .bubble h1:first-child,
    .assistant .bubble h2:first-child,
    .assistant .bubble h3:first-child,
    .assistant .bubble p:first-child,
    .assistant .bubble ul:first-child,
    .assistant .bubble ol:first-child {
      margin-top: 0;
    }
    .assistant .bubble h1 {
      font-size: 22px;
    }
    .assistant .bubble h2 {
      font-size: 19px;
    }
    .assistant .bubble h3 {
      font-size: 17px;
    }
    .assistant .bubble p {
      margin: 8px 0;
      line-height: 1.9;
    }
    .assistant .bubble strong {
      font-weight: 800;
      color: #0f3156;
    }
    .assistant .bubble ul,
    .assistant .bubble ol {
      margin: 8px 0;
      padding-right: 22px;
      line-height: 1.9;
    }
    .assistant .bubble li {
      margin: 4px 0;
      padding-right: 2px;
    }
    .assistant .bubble code {
      direction: ltr;
      display: inline-block;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.92em;
      background: rgba(13, 99, 201, 0.08);
      border: 1px solid rgba(13, 99, 201, 0.12);
      border-radius: 4px;
      padding: 1px 5px;
    }
    .composer {
      border-top: 1px solid rgba(104, 162, 224, 0.22);
      padding: 18px clamp(14px, 4vw, 64px) 22px;
      background:
        linear-gradient(180deg, rgba(248, 252, 255, 0.46), rgba(245, 250, 255, 0.92)),
        rgba(248, 252, 255, 0.82);
      position: sticky;
      bottom: 0;
      z-index: 10;
      backdrop-filter: blur(22px) saturate(150%);
      -webkit-backdrop-filter: blur(22px) saturate(150%);
    }
    .composer form {
      display: grid;
      direction: ltr;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      align-items: end;
      max-width: min(1040px, 100%);
      margin: 0 auto;
      padding: 10px;
      border-radius: 26px;
      background:
        linear-gradient(135deg, rgba(255, 255, 255, 0.90), rgba(244, 250, 255, 0.74)),
        rgba(255, 255, 255, 0.78);
      border: 1px solid rgba(104, 162, 224, 0.24);
      box-shadow:
        0 18px 44px rgba(25, 103, 210, 0.10),
        inset 0 1px 0 rgba(255, 255, 255, 0.8);
      transition: box-shadow 180ms ease, transform 180ms ease, border-color 180ms ease;
    }
    .composer form:focus-within {
      border-color: rgba(29, 111, 212, 0.32);
      box-shadow:
        0 20px 44px rgba(25, 103, 210, 0.12),
        0 0 0 4px rgba(29, 111, 212, 0.06),
        inset 0 1px 0 rgba(255, 255, 255, 0.84);
    }
    textarea {
      min-height: 58px;
      max-height: 190px;
      resize: none;
      line-height: 1.85;
      border-radius: 20px;
      padding: 15px 17px;
      background: transparent;
      box-shadow: none;
    }
    .composer textarea {
      direction: rtl;
      text-align: right;
      border: 0;
      background: rgba(255, 255, 255, 0.18);
    }
    .composer textarea:focus {
      outline: none;
      border-color: transparent;
      box-shadow: none;
      background: rgba(255, 255, 255, 0.28);
    }
    .composer button {
      min-width: 82px;
      height: 50px;
      padding: 0 18px;
      border-radius: 17px;
      align-self: end;
    }
    .status {
      min-height: 22px;
      max-width: min(1040px, 100%);
      margin: 12px auto 0;
      padding: 0 8px;
      color: var(--muted);
      font-size: 13px;
    }
    .error {
      color: #b42318;
      font-weight: 700;
    }
    @keyframes message-in {
      from {
        transform: translateY(5px);
        opacity: 0;
      }
      to {
        transform: translateY(0);
        opacity: 1;
      }
    }
    @media (max-width: 720px) {
      main {
        padding: 92px 10px 14px;
      }
      .brand-lockup {
        left: 10px;
        top: 10px;
        right: auto;
        max-width: calc(100vw - 72px);
        padding: 8px 10px 8px 8px;
      }
      .brand-logo {
        width: 38px;
        height: 38px;
      }
      header {
        min-height: 148px;
        padding-inline: 8px;
      }
      .hero-mark {
        width: 86px;
        height: 86px;
      }
      h1 {
        font-size: 23px;
      }
      .chat-shell {
        border-radius: 24px;
      }
      .messages {
        min-height: calc(100vh - 340px);
        padding: 18px 12px 20px;
        gap: 18px;
      }
      .message.user,
      .message.assistant {
        max-width: 96%;
      }
      .composer form {
        padding: 10px;
      }
      .composer button {
        min-width: 68px;
        padding-inline: 14px;
      }
      .brand-name,
      .brand-subtitle {
        white-space: normal;
      }
    }
  </style>
</head>
<body>
  <div class="app">
    <div class="brand-lockup" aria-label="نام و نشان پروژه">
      <img class="brand-logo" src="/assets/logo-uni.png" alt="لوگوی پروژه">
      <div class="brand-text">
        <p class="brand-name">دانشگاه آزاد اسلامی واحد ساری</p>
        <p class="brand-subtitle">چت‌بات پرسش‌وپاسخ دانشجویی</p>
      </div>
    </div>
    <button id="settings-toggle" class="settings-toggle" type="button" aria-label="تنظیمات" title="تنظیمات">⚙</button>
    <aside id="settings-panel" class="settings-panel" aria-label="تنظیمات اتصال مدل">
      <h2>تنظیمات مدل زبانی</h2>
      <form id="settings-form" class="settings-form">
        <label>
          کلید API
          <input id="llm-api-key" name="llm_api_key" type="password" autocomplete="off" placeholder="کلید API را وارد کنید">
        </label>
        <label>
          آدرس Base URL
          <input id="base-url" name="base_url" type="url" dir="ltr" placeholder="https://openrouter.ai/api/v1">
        </label>
        <div class="settings-actions">
          <button id="save-settings" type="submit">ذخیره تنظیمات</button>
        </div>
        <div id="settings-status" class="settings-status"></div>
      </form>
    </aside>
    <main>
      <header>
        <img class="hero-mark" src="/assets/image.png" alt="نشان ربات">
        <h1>سامانه پاسخ‌دهی هوشمند</h1>
      </header>
      <section class="chat-shell">
        <div id="messages" class="messages" aria-live="polite"></div>
        <div class="composer">
          <form id="chat-form">
            <textarea id="question" maxlength="4000" placeholder="پرسش آموزشی خود را بنویسید؛ مثلا شرایط حذف اضطراری درس چیست؟"></textarea>
            <button id="submit" type="submit">ارسال</button>
          </form>
          <div id="status" class="status"></div>
        </div>
      </section>
    </main>
  </div>
  <script>
    const form = document.getElementById("chat-form");
    const question = document.getElementById("question");
    const submit = document.getElementById("submit");
    const statusBox = document.getElementById("status");
    const messagesBox = document.getElementById("messages");
    const settingsToggle = document.getElementById("settings-toggle");
    const settingsPanel = document.getElementById("settings-panel");
    const settingsForm = document.getElementById("settings-form");
    const llmApiKey = document.getElementById("llm-api-key");
    const baseUrl = document.getElementById("base-url");
    const settingsStatus = document.getElementById("settings-status");
    const saveSettings = document.getElementById("save-settings");
    const transcriptKey = "iau_chatbot_messages";
    let sessionId = window.localStorage.getItem("iau_chatbot_session_id") || "";
    let messages = loadMessages();
    renderMessages();

    settingsToggle.addEventListener("click", (event) => {
      event.stopPropagation();
      settingsPanel.classList.toggle("open");
    });
    settingsPanel.addEventListener("click", (event) => {
      event.stopPropagation();
    });
    document.addEventListener("click", () => {
      settingsPanel.classList.remove("open");
    });

    question.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
      }
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const text = question.value.trim();
      if (!text) {
        statusBox.innerHTML = '<span class="error">لطفا ابتدا پرسش خود را وارد کنید.</span>';
        return;
      }
      appendMessage("user", text);
      question.value = "";
      submit.disabled = true;
      statusBox.textContent = "در حال دریافت پاسخ...";
      try {
        const response = await fetch("/chat", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({question: text, session_id: sessionId || undefined})
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || data.error || "ارسال پرسش ناموفق بود.");
        }
        sessionId = data.session_id;
        window.localStorage.setItem("iau_chatbot_session_id", sessionId);
        appendMessage("assistant", data.answer || "");
        statusBox.textContent = "";
      } catch (error) {
        appendMessage("assistant", "خطا: " + error.message);
        statusBox.innerHTML = '<span class="error">' + escapeHtml(error.message) + '</span>';
      } finally {
        submit.disabled = false;
        question.focus();
      }
    });

    settingsForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const key = llmApiKey.value.trim();
      const url = baseUrl.value.trim();
      if (!key || !url) {
        settingsStatus.innerHTML = '<span class="error">کلید API و Base URL را وارد کنید.</span>';
        return;
      }
      saveSettings.disabled = true;
      settingsStatus.textContent = "در حال ذخیره...";
      try {
        const response = await fetch("/settings", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({llm_api_key: key, base_url: url})
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || "ذخیره تنظیمات ناموفق بود.");
        }
        settingsStatus.textContent = "تنظیمات ذخیره شد.";
        llmApiKey.value = "";
      } catch (error) {
        settingsStatus.innerHTML = '<span class="error">' + escapeHtml(error.message) + '</span>';
      } finally {
        saveSettings.disabled = false;
      }
    });

    function appendMessage(role, content) {
      messages.push({role, content});
      saveMessages();
      renderMessages();
    }

    function renderMessages() {
      messagesBox.innerHTML = "";
      if (!messages.length) {
        const empty = document.createElement("div");
        empty.className = "empty-state";
        empty.textContent = "لطفاً پرسش‌های آموزشی و اداری خود را مطرح کنید.";
        messagesBox.appendChild(empty);
        return;
      }
      for (const message of messages) {
        const item = document.createElement("article");
        item.className = "message " + message.role;
        const role = document.createElement("div");
        role.className = "message-role";
        role.textContent = message.role === "user" ? "شما" : "راهنمای آموزشی";
        const bubble = document.createElement("div");
        bubble.className = "bubble";
        if (message.role === "assistant") {
          bubble.innerHTML = renderMarkdown(message.content);
        } else {
          bubble.textContent = message.content;
        }
        item.appendChild(role);
        item.appendChild(bubble);
        messagesBox.appendChild(item);
      }
      window.scrollTo({top: document.documentElement.scrollHeight, behavior: "smooth"});
    }

    function loadMessages() {
      try {
        const parsed = JSON.parse(window.localStorage.getItem(transcriptKey) || "[]");
        return Array.isArray(parsed) ? parsed : [];
      } catch {
        return [];
      }
    }

    function saveMessages() {
      window.localStorage.setItem(transcriptKey, JSON.stringify(messages));
    }

    function renderMarkdown(value) {
      const lines = String(value || "").split(/\\r?\\n/);
      const blocks = [];
      let list = null;
      let paragraph = [];

      function flushParagraph() {
        if (paragraph.length) {
          blocks.push("<p>" + renderInline(paragraph.join(" ")) + "</p>");
          paragraph = [];
        }
      }

      function flushList() {
        if (list) {
          blocks.push("<" + list.type + ">" + list.items.map((item) => "<li>" + renderInline(item) + "</li>").join("") + "</" + list.type + ">");
          list = null;
        }
      }

      for (const rawLine of lines) {
        const line = rawLine.trim();
        if (!line) {
          flushParagraph();
          flushList();
          continue;
        }
        const heading = line.match(/^(#{1,3})\\s+(.+)$/);
        if (heading) {
          flushParagraph();
          flushList();
          const level = heading[1].length;
          blocks.push("<h" + level + ">" + renderInline(heading[2]) + "</h" + level + ">");
          continue;
        }
        const unordered = line.match(/^[-*]\\s+(.+)$/);
        if (unordered) {
          flushParagraph();
          if (!list || list.type !== "ul") {
            flushList();
            list = {type: "ul", items: []};
          }
          list.items.push(unordered[1]);
          continue;
        }
        const ordered = line.match(/^\\d+[.)]\\s+(.+)$/);
        if (ordered) {
          flushParagraph();
          if (!list || list.type !== "ol") {
            flushList();
            list = {type: "ol", items: []};
          }
          list.items.push(ordered[1]);
          continue;
        }
        flushList();
        paragraph.push(line);
      }
      flushParagraph();
      flushList();
      return blocks.join("");
    }

    function renderInline(value) {
      let html = escapeHtml(value);
      html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
      html = html.replace(/\\*\\*([^*]+)\\*\\*/g, "<strong>$1</strong>");
      return html;
    }

    function escapeHtml(value) {
      return String(value).replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
      }[char]));
    }
  </script>
</body>
</html>"""
