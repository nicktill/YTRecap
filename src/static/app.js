(() => {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  const els = {
    topbar: $(".topbar"),
    form: $("#composer"),
    input: $("#url"),
    submit: $("#submit-btn"),
    paste: $("#paste-btn"),
    formError: $("#form-error"),
    result: $("#result"),
    progress: $("#progress"),
    summary: $("#summary"),
    errorPanel: $("#error-panel"),
    errorMsg: $("#error-msg"),
    player: $("#player"),
    thumb: $("#thumb"),
    title: $("#video-title"),
    channel: $("#video-channel"),
    stats: $("#video-stats"),
    ytLink: $("#yt-link"),
    copy: $("#copy-btn"),
    download: $("#download-btn"),
    share: $("#share-btn"),
    recent: $("#recent"),
    recentList: $("#recent-list"),
    toast: $("#toast"),
    foot: $("#summary-foot"),
    footStats: $("#foot-stats"),
  };

  // --- storage (per-viewer conveniences only; the app works without it) ---
  const store = {
    get(key, fallback) {
      try {
        const v = localStorage.getItem("ytrecap:" + key);
        return v === null ? fallback : JSON.parse(v);
      } catch {
        return fallback;
      }
    },
    set(key, value) {
      try {
        localStorage.setItem("ytrecap:" + key, JSON.stringify(value));
      } catch {}
    },
  };

  const state = {
    length: store.get("length", "standard"),
    videoId: null,
    video: null,
    markdown: "",
    source: null,
    controller: null,
  };

  // --- helpers ---
  const VIDEO_ID_PATTERNS = [
    /(?:v=|vi=)([\w-]{11})/,
    /youtu\.be\/([\w-]{11})/,
    /\/(?:shorts|embed|live|v)\/([\w-]{11})/,
    /^([\w-]{11})$/,
  ];

  function extractVideoId(text) {
    text = (text || "").trim();
    for (const re of VIDEO_ID_PATTERNS) {
      const m = text.match(re);
      if (m) return m[1];
    }
    return null;
  }

  function toSeconds(ts) {
    return ts.split(":").reduce((acc, part) => acc * 60 + Number(part), 0);
  }

  const escapeHtml = (s) =>
    s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

  let toastTimer;
  function toast(message) {
    $("span", els.toast).textContent = message;
    els.toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => els.toast.classList.remove("show"), 2200);
  }

  function flashDone(btn) {
    const use = $("use", btn);
    const prev = use.getAttribute("href");
    btn.classList.add("done");
    use.setAttribute("href", "#i-check");
    setTimeout(() => {
      btn.classList.remove("done");
      use.setAttribute("href", prev);
    }, 1600);
  }

  // --- theme ---
  $("#theme-toggle").addEventListener("click", () => {
    const current =
      document.documentElement.dataset.theme ||
      (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("ytrecap:theme", next);
    } catch {}
  });

  addEventListener("scroll", () => els.topbar.classList.toggle("scrolled", scrollY > 4), { passive: true });

  // --- length selector (two synced segmented controls) ---
  function renderLength() {
    $$("[data-length-group] button").forEach((b) =>
      b.setAttribute("aria-checked", String(b.dataset.length === state.length)),
    );
  }

  $$("[data-length-group]").forEach((group) =>
    group.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-length]");
      if (!btn || btn.dataset.length === state.length) return;
      state.length = btn.dataset.length;
      store.set("length", state.length);
      renderLength();
      // Changing length on a result re-generates it in place.
      if (state.videoId && group.closest(".summary-card")) summarize(state.videoId);
    }),
  );

  // --- markdown rendering (escaped first, so model output can't inject HTML) ---
  function inline(text) {
    return escapeHtml(text)
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*\s][^*]*?)\*(?!\*)/g, "$1<em>$2</em>")
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\[(\d{1,2}:\d{2}(?::\d{2})?)\]/g, (_, t) => `<button class="ts" type="button" data-t="${toSeconds(t)}">${t}</button>`);
  }

  function renderBlocks(lines) {
    let html = "";
    let list = null;
    let para = [];
    const flushPara = () => {
      if (para.length) html += `<p>${inline(para.join(" "))}</p>`;
      para = [];
    };
    const flushList = () => {
      if (list) html += `<${list.tag}>${list.items.map((i) => `<li>${i}</li>`).join("")}</${list.tag}>`;
      list = null;
    };
    for (const raw of lines) {
      const line = raw.trim();
      const bullet = line.match(/^[-*•]\s+(.*)$/);
      const numbered = line.match(/^\d+[.)]\s+(.*)$/);
      if (bullet || numbered) {
        flushPara();
        const tag = bullet ? "ul" : "ol";
        if (!list || list.tag !== tag) {
          flushList();
          list = { tag, items: [] };
        }
        list.items.push(inline((bullet || numbered)[1]));
      } else if (!line) {
        flushPara();
        flushList();
      } else {
        flushList();
        para.push(line);
      }
    }
    flushPara();
    flushList();
    return html;
  }

  function renderChapters(lines) {
    const items = lines
      .map((l) => l.trim().match(/^[-*•]?\s*\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.*)$/))
      .filter(Boolean)
      .map(([, t, rest]) => {
        const [title, ...desc] = rest.split(/\s+[—–-]\s+/);
        return `<li><button class="ts" type="button" data-t="${toSeconds(t)}">${t}</button><div class="chapter-body"><strong>${inline(title)}</strong>${desc.length ? `<span>${inline(desc.join(" — "))}</span>` : ""}</div></li>`;
      });
    return items.length ? `<ul>${items.join("")}</ul>` : renderBlocks(lines);
  }

  function sectionKind(heading) {
    const h = heading.toLowerCase();
    if (h.includes("tl;dr") || h.includes("tldr")) return "tldr";
    if (h.includes("takeaway")) return "takeaways";
    if (h.includes("chapter")) return "chapters";
    return "body";
  }

  function parseSections(md) {
    const sections = [];
    let current = { heading: null, lines: [] };
    for (const line of md.split("\n")) {
      const h = line.match(/^#{1,4}\s+(.*)$/);
      if (h) {
        if (current.heading || current.lines.some((l) => l.trim())) sections.push(current);
        current = { heading: h[1].trim(), lines: [] };
      } else {
        current.lines.push(line);
      }
    }
    sections.push(current);
    return sections.map(({ heading, lines }) => {
      const kind = heading ? sectionKind(heading) : "body";
      const body = kind === "chapters" ? renderChapters(lines) : renderBlocks(lines);
      return { kind, html: (heading ? `<h3>${escapeHtml(heading)}</h3>` : "") + body };
    });
  }

  // Patch sections in place so each one animates in once instead of on every token.
  function renderSummary() {
    const sections = parseSections(state.markdown).filter((s) => s.html);
    const nodes = els.summary.children;
    sections.forEach((sec, i) => {
      let node = nodes[i];
      if (!node) {
        node = document.createElement("section");
        els.summary.appendChild(node);
      }
      node.className = `sec-${sec.kind}`;
      if (node.innerHTML !== sec.html) node.innerHTML = sec.html;
    });
    while (nodes.length > sections.length) els.summary.lastElementChild.remove();
  }

  let renderQueued = false;
  function scheduleRender() {
    if (renderQueued) return;
    renderQueued = true;
    requestAnimationFrame(() => {
      renderQueued = false;
      renderSummary();
    });
  }

  // --- video card + player ---
  function resetVideoCard(videoId) {
    els.player.querySelector("iframe")?.remove();
    els.thumb.hidden = false;
    $("#play-btn").hidden = false;
    els.thumb.classList.remove("broken");
    els.thumb.src = `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`;
    els.title.innerHTML = '<span class="skeleton" style="width:90%"></span><span class="skeleton" style="width:60%"></span>';
    els.channel.textContent = "";
    els.stats.innerHTML = "";
    els.ytLink.href = `https://www.youtube.com/watch?v=${videoId}`;
  }

  els.thumb.addEventListener("error", () => els.thumb.classList.add("broken"));

  function fillVideoCard(video) {
    state.video = video;
    els.title.textContent = video.title;
    els.channel.textContent = video.channel;
    const stats = [
      video.views && `${video.views} views`,
      video.duration,
      video.published,
    ].filter(Boolean);
    els.stats.innerHTML = stats.map((s) => `<span class="stat">${escapeHtml(s)}</span>`).join("");
    document.title = `${video.title} · YTRecap`;
  }

  function playAt(seconds = 0) {
    const id = state.videoId;
    if (!id) return;
    const existing = els.player.querySelector("iframe");
    if (existing) {
      existing.contentWindow.postMessage(
        JSON.stringify({ event: "command", func: "seekTo", args: [seconds, true] }),
        "*",
      );
      existing.contentWindow.postMessage(JSON.stringify({ event: "command", func: "playVideo", args: [] }), "*");
    } else {
      const iframe = document.createElement("iframe");
      iframe.src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1&enablejsapi=1&rel=0&start=${Math.floor(seconds)}`;
      iframe.title = state.video?.title || "YouTube video";
      iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
      iframe.allowFullscreen = true;
      els.player.appendChild(iframe);
      els.thumb.hidden = true;
      $("#play-btn").hidden = true;
    }
    if (matchMedia("(max-width: 900px)").matches) {
      els.player.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  $("#play-btn").addEventListener("click", () => playAt(0));
  els.summary.addEventListener("click", (e) => {
    const ts = e.target.closest(".ts");
    if (ts) playAt(Number(ts.dataset.t));
  });

  // --- progress steps ---
  const STEPS = ["video", "transcript", "writing"];
  function setStep(step) {
    const idx = STEPS.indexOf(step);
    $$("li", els.progress).forEach((li, i) => {
      li.classList.toggle("complete", i < idx);
      li.classList.toggle("active", i === idx);
    });
  }

  function setActionsEnabled(on) {
    [els.copy, els.download, els.share].forEach((b) => (b.disabled = !on));
  }

  // --- history ---
  function saveHistory(video) {
    const list = store.get("history", []).filter((v) => v.id !== video.id);
    list.unshift({ id: video.id, title: video.title });
    store.set("history", list.slice(0, 6));
  }

  function renderHistory() {
    const list = store.get("history", []);
    els.recent.hidden = !list.length;
    els.recentList.innerHTML = list
      .map(
        (v) =>
          `<button class="recent-item" type="button" data-id="${escapeHtml(v.id)}"><img src="https://i.ytimg.com/vi/${encodeURIComponent(v.id)}/mqdefault.jpg" alt="" loading="lazy" onerror="this.style.visibility='hidden'" /><span>${escapeHtml(v.title)}</span></button>`,
      )
      .join("");
  }

  els.recentList.addEventListener("click", (e) => {
    const item = e.target.closest(".recent-item");
    if (!item) return;
    els.input.value = `https://www.youtube.com/watch?v=${item.dataset.id}`;
    summarize(item.dataset.id);
  });

  // --- main flow ---
  function showFormError(message) {
    els.formError.textContent = message;
    els.formError.hidden = false;
    els.form.classList.remove("invalid");
    void els.form.offsetWidth;
    els.form.classList.add("invalid");
  }

  function showError(message) {
    els.progress.hidden = true;
    els.errorMsg.textContent = message;
    els.errorPanel.hidden = false;
    els.summary.classList.remove("streaming");
  }

  function durationMinutes(duration) {
    if (!duration) return null;
    const secs = toSeconds(duration);
    return Number.isFinite(secs) ? Math.max(1, Math.round(secs / 60)) : null;
  }

  function renderFooter() {
    const words = state.markdown.split(/\s+/).filter(Boolean).length;
    const readMin = Math.max(1, Math.round(words / 230));
    const videoMin = durationMinutes(state.video?.duration);
    let text = `<b>${readMin} min</b> read`;
    if (videoMin) {
      text += ` · ${videoMin} min video`;
      if (videoMin > readMin) text += ` · saves ~${videoMin - readMin} min`;
    }
    els.footStats.innerHTML = text;
    els.foot.hidden = false;
  }

  async function summarize(videoId, { fresh = false } = {}) {
    state.controller?.abort();
    const controller = (state.controller = new AbortController());

    const isNewVideo = videoId !== state.videoId;
    state.videoId = videoId;
    state.markdown = "";
    state.source = null;
    $("#summary-source").hidden = true;
    els.formError.hidden = true;
    els.form.classList.remove("invalid");
    document.body.classList.add("has-result");
    els.result.hidden = false;
    els.errorPanel.hidden = true;
    requestAnimationFrame(() => {
      els.result.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    els.progress.hidden = false;
    els.summary.innerHTML = "";
    els.summary.classList.add("streaming");
    els.foot.hidden = true;
    els.submit.disabled = true;
    els.submit.classList.add("loading");
    setActionsEnabled(false);
    setStep("video");
    if (isNewVideo) resetVideoCard(videoId);

    const shareUrl = `/watch?v=${videoId}`;
    if (location.pathname + location.search !== shareUrl) history.pushState({ videoId }, "", shareUrl);

    try {
      const res = await fetch("/api/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: videoId, length: state.length, fresh }),
        signal: controller.signal,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || "Something went wrong. Please try again.");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let finished = false;
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop();
        for (const line of lines) {
          if (!line.trim()) continue;
          const evt = JSON.parse(line);
          if (evt.type === "status") setStep(evt.step);
          else if (evt.type === "video") {
            state.source = evt.source;
            const sourceNote = $("#summary-source");
            sourceNote.textContent = evt.demo ? "Example summary" : evt.source === "transcript" ? "Based on video captions" : "Description-only overview — captions were unavailable; this may miss the video’s content.";
            sourceNote.hidden = false;
            fillVideoCard(evt.video);
            saveHistory(evt.video);
          } else if (evt.type === "delta") {
            els.progress.hidden = true;
            state.markdown += evt.text;
            scheduleRender();
          } else if (evt.type === "error") throw new Error(evt.message);
          else if (evt.type === "done") finished = true;
        }
      }
      if (!finished) throw new Error("The connection was interrupted. Please try again.");
      els.summary.classList.remove("streaming");
      renderSummary();
      renderFooter();
      setActionsEnabled(true);
    } catch (err) {
      if (err.name === "AbortError") return;
      showError(err.message || "Something went wrong. Please try again.");
    } finally {
      if (state.controller === controller) {
        els.submit.disabled = false;
        els.submit.classList.remove("loading");
      }
    }
  }

  els.form.addEventListener("submit", (e) => {
    e.preventDefault();
    const id = extractVideoId(els.input.value);
    if (!id) {
      showFormError(
        els.input.value.trim()
          ? "That doesn't look like a YouTube link. Try pasting the full video URL."
          : "Paste a YouTube link to get started.",
      );
      els.input.focus();
      return;
    }
    els.input.blur();
    summarize(id);
  });

  els.input.addEventListener("input", () => {
    els.formError.hidden = true;
    els.form.classList.remove("invalid");
  });

  // Auto-submit when a YouTube link is pasted into an empty field.
  els.input.addEventListener("paste", () => {
    setTimeout(() => {
      if (extractVideoId(els.input.value)) els.form.requestSubmit();
    });
  });

  if (navigator.clipboard?.readText && matchMedia("(pointer: fine)").matches) {
    els.paste.hidden = false;
    els.paste.addEventListener("click", async () => {
      try {
        els.input.value = (await navigator.clipboard.readText()).trim();
        if (extractVideoId(els.input.value)) els.form.requestSubmit();
        else els.input.focus();
      } catch {
        els.input.focus();
      }
    });
  }

  $("#retry-btn").addEventListener("click", () => state.videoId && summarize(state.videoId));
  $("#regen-btn").addEventListener("click", () => state.videoId && summarize(state.videoId, { fresh: true }));

  $("#examples").addEventListener("click", (e) => {
    const chip = e.target.closest("[data-example]");
    if (!chip) return;
    els.input.value = `https://www.youtube.com/watch?v=${chip.dataset.example}`;
    summarize(chip.dataset.example);
  });

  $("#clear-history").addEventListener("click", () => {
    store.set("history", []);
    renderHistory();
  });

  // --- actions ---
  function exportMarkdown() {
    const v = state.video || {};
    return `# ${v.title || "Video summary"}\n\n${v.channel ? `*${v.channel}* · ` : ""}https://www.youtube.com/watch?v=${state.videoId}\n\n${state.source === "description" ? "> Description-only overview: captions were unavailable.\n\n" : ""}${state.markdown.trim()}\n`;
  }

  els.copy.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(exportMarkdown());
      flashDone(els.copy);
      toast("Summary copied");
    } catch {
      toast("Couldn't access the clipboard");
    }
  });

  els.download.addEventListener("click", () => {
    const blob = new Blob([exportMarkdown()], { type: "text/markdown" });
    const a = document.createElement("a");
    const slug = (state.video?.title || "summary").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60);
    a.href = URL.createObjectURL(blob);
    a.download = `${slug || "summary"}.md`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    flashDone(els.download);
  });

  els.share.addEventListener("click", async () => {
    const url = `${location.origin}/watch?v=${state.videoId}`;
    if (navigator.share && matchMedia("(pointer: coarse)").matches) {
      try {
        await navigator.share({ title: state.video?.title, url });
      } catch {}
      return;
    }
    try {
      await navigator.clipboard.writeText(url);
      flashDone(els.share);
      toast("Share link copied");
    } catch {
      toast(url);
    }
  });

  // --- keyboard ---
  addEventListener("keydown", (e) => {
    if (e.key === "/" && !/^(INPUT|TEXTAREA)$/.test(document.activeElement.tagName)) {
      e.preventDefault();
      els.input.focus();
      els.input.select();
    }
  });

  // --- navigation ---
  function goHome() {
    state.controller?.abort();
    state.videoId = null;
    document.body.classList.remove("has-result");
    els.result.hidden = true;
    els.input.value = "";
    document.title = "YTRecap — Summarize any YouTube video";
    renderHistory();
  }

  addEventListener("popstate", () => {
    const id = new URLSearchParams(location.search).get("v") || extractVideoId(location.pathname);
    if (id) {
      els.input.value = `https://www.youtube.com/watch?v=${id}`;
      summarize(id);
    } else goHome();
  });

  $(".brand").addEventListener("click", (e) => {
    if (!state.videoId) return;
    e.preventDefault();
    history.pushState({}, "", "/");
    goHome();
  });

  // --- init ---
  renderLength();
  renderHistory();
  const initialId = document.body.dataset.initialId;
  if (initialId) {
    els.input.value = `https://www.youtube.com/watch?v=${initialId}`;
    summarize(initialId);
  }
})();
