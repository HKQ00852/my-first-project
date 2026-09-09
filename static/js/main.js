const COOKIE_NAME = "caixun_lang";
const SUPPORTED = ["zh-Hant", "zh-Hans", "en"];

const i18nData = (() => {
  const el = document.getElementById("i18n-data");
  if (!el) return {};
  try {
    return JSON.parse(el.textContent);
  } catch {
    return {};
  }
})();

function readCookie(name) {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : "";
}

function writeCookie(name, value) {
  document.cookie = `${name}=${encodeURIComponent(value)};path=/;max-age=${60 * 60 * 24 * 365};samesite=lax`;
}

function normalizeLang(value) {
  if (!value) return "zh-Hant";
  if (SUPPORTED.includes(value)) return value;
  const aliases = {
    zh: "zh-Hant",
    "zh-TW": "zh-Hant",
    "zh-HK": "zh-Hant",
    "zh-CN": "zh-Hans",
    "zh-SG": "zh-Hans",
  };
  return aliases[value] || "zh-Hant";
}

function t(key, lang) {
  const pack = i18nData[lang] || i18nData["zh-Hant"] || {};
  return pack[key] ?? i18nData["zh-Hant"]?.[key] ?? key;
}

function scoreText(raw, lang) {
  const map = { 高: "score.high", 中: "score.mid", 低: "score.low", High: "score.high", Mid: "score.mid", Low: "score.low" };
  const key = map[raw];
  return key ? t(key, lang) : raw;
}

function applyLanguage(lang) {
  const code = normalizeLang(lang);
  const htmlLang = code === "zh-Hant" ? "zh-HK" : code === "zh-Hans" ? "zh-CN" : "en";
  document.documentElement.lang = htmlLang;
  writeCookie(COOKIE_NAME, code);
  window.__CAIXUN_LANG__ = code;

  const formLang = document.getElementById("form-lang");
  if (formLang) formLang.value = code;

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (!key) return;
    const value = t(key, code);
    if (el.tagName === "TITLE") {
      document.title = value;
    } else if (el.tagName === "META") {
      el.setAttribute("content", value);
    } else {
      el.textContent = value;
    }
  });

  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.getAttribute("data-i18n-placeholder");
    if (key) el.setAttribute("placeholder", t(key, code));
  });

  document.querySelectorAll("[data-i18n-alt]").forEach((el) => {
    const key = el.getAttribute("data-i18n-alt");
    if (key) el.setAttribute("alt", t(key, code));
  });

  document.querySelectorAll("[data-score]").forEach((el) => {
    el.textContent = scoreText(el.getAttribute("data-score") || "", code);
  });

  document.querySelectorAll(".lang-btn").forEach((btn) => {
    btn.classList.toggle("is-active", btn.getAttribute("data-lang") === code);
  });

  // Prefer SC fonts when Simplified is active.
  document.body.dataset.lang = code;
  drawCapabilityRadar();
}

function escapeXml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function wrapRadarLabel(text) {
  const raw = String(text || "").trim();
  if (!raw) return [""];
  if (raw.length <= 6 || !/\s/.test(raw)) return [raw];
  const parts = raw.split(/\s+/);
  if (parts.length === 1) return [raw];
  const mid = Math.ceil(parts.length / 2);
  return [parts.slice(0, mid).join(" "), parts.slice(mid).join(" ")];
}

function drawCapabilityRadar() {
  const root = document.getElementById("capability-radar");
  if (!root) return;
  const svg = root.querySelector("svg.radar-svg");
  if (!svg) return;

  const lang = window.__CAIXUN_LANG__ || "zh-Hant";
  const values = [
    Number(root.dataset.hook) || 1,
    Number(root.dataset.distinct) || 1,
    Number(root.dataset.cta) || 1,
    Number(root.dataset.retention) || 1,
  ].map((n) => Math.min(3, Math.max(1, n)));
  const labels = [
    t("result.hook", lang),
    t("result.radar_distinct", lang),
    t("result.radar_cta", lang),
    t("result.retention", lang),
  ];

  const cx = 180;
  const cy = 168;
  const rMax = 100;
  const levels = 3;
  const n = 4;
  const start = -Math.PI / 2;

  const point = (index, radius) => {
    const angle = start + (Math.PI * 2 * index) / n;
    return [cx + radius * Math.cos(angle), cy + radius * Math.sin(angle)];
  };
  const poly = (radius) =>
    Array.from({ length: n }, (_, i) => point(i, radius).map((v) => v.toFixed(1)).join(",")).join(" ");

  let rings = "";
  for (let lv = 1; lv <= levels; lv += 1) {
    rings += `<polygon class="radar-ring" points="${poly((rMax * lv) / levels)}"></polygon>`;
  }

  let axes = "";
  let dots = "";
  const valuePts = [];
  for (let i = 0; i < n; i += 1) {
    const [x, y] = point(i, rMax);
    axes += `<line class="radar-axis" x1="${cx}" y1="${cy}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}"></line>`;
    const [vx, vy] = point(i, (rMax * values[i]) / levels);
    valuePts.push(`${vx.toFixed(1)},${vy.toFixed(1)}`);
    dots += `<circle class="radar-dot" cx="${vx.toFixed(1)}" cy="${vy.toFixed(1)}" r="3.5"></circle>`;
  }

  let labelMarkup = "";
  for (let i = 0; i < n; i += 1) {
    const [lx, ly] = point(i, rMax + 28);
    const lines = wrapRadarLabel(labels[i]);
    const startY = ly - ((lines.length - 1) * 7);
    const tspans = lines
      .map(
        (line, idx) =>
          `<tspan x="${lx.toFixed(1)}" dy="${idx === 0 ? 0 : 14}">${escapeXml(line)}</tspan>`,
      )
      .join("");
    labelMarkup += `<text class="radar-label" x="${lx.toFixed(1)}" y="${startY.toFixed(1)}" text-anchor="middle">${tspans}</text>`;
  }

  const title = svg.querySelector("title");
  const desc = svg.querySelector("desc");
  svg.innerHTML = `${title ? title.outerHTML : ""}${desc ? desc.outerHTML : ""}${rings}${axes}<polygon class="radar-fill" points="${valuePts.join(" ")}"></polygon>${dots}${labelMarkup}`;
}

document.querySelectorAll("[data-reveal]").forEach((section) => {
  const observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        section.classList.add("in");
        observer.disconnect();
      }
    },
    { threshold: 0.2 },
  );
  observer.observe(section);
});

const result = document.getElementById("result");
if (result) {
  result.scrollIntoView({ behavior: "smooth", block: "start" });
}

const initialLang = normalizeLang(
  window.__CAIXUN_LANG__ || readCookie(COOKIE_NAME) || document.documentElement.lang || "zh-Hant",
);
applyLanguage(initialLang);

document.querySelectorAll(".lang-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const next = btn.getAttribute("data-lang");
    if (next) applyLanguage(next);
  });
});

const form = document.querySelector(".diagnose-form");
if (form) {
  form.addEventListener("submit", () => {
    const lang = normalizeLang(window.__CAIXUN_LANG__);
    const btn = form.querySelector('button[type="submit"]');
    const fileInput = form.querySelector('input[name="video"]');
    const hasVideo = fileInput && fileInput.files && fileInput.files.length > 0;
    if (btn) {
      btn.disabled = true;
      btn.textContent = hasVideo ? t("form.submitting_video", lang) : t("form.submitting", lang);
    }
  });
}
