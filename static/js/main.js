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
