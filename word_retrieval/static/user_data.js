/**
 * 用户差分数据（方案 A）：仅存本浏览器，与服务器基准对照表 / ECDICT 合并使用。
 * localStorage key: word-retrieval-user-data
 *
 * dict_extra：ECDICT 风格词条数组
 *   { word, phonetic, definition, translation, pos, exchange }
 * 兼容旧版纯字符串词头列表。
 */
(function (global) {
  const STORAGE_KEY = "word-retrieval-user-data";
  const SELECTED_KEY = "word-retrieval-selected-wordlist";
  const VERSION = 3;
  const HIGHLIGHT_KEYS = ["green", "yellow", "red"];
  const VOCAB_OUTPUT_KEYS = ["phonetic", "translation", "definition", "exchange"];
  const DEFAULT_HIGHLIGHT = {
    green: { enabled: true, hex: "#1b8f3a" },
    yellow: { enabled: true, hex: "#c4a000" },
    red: { enabled: true, hex: "#c62828" },
  };
  const HEX_RE = /^#[0-9a-fA-F]{6}$/;

  function defaultVocabOutput() {
    return {
      phonetic: true,
      translation: true,
      definition: false,
      exchange: false,
    };
  }

  function normalizeVocabOutput(raw) {
    const out = defaultVocabOutput();
    if (!raw || typeof raw !== "object") return out;
    VOCAB_OUTPUT_KEYS.forEach((key) => {
      if (!(key in raw)) return;
      const val = raw[key];
      if (typeof val === "boolean") out[key] = val;
      else if (val === 0 || val === 1) out[key] = !!val;
      else if (typeof val === "string") {
        const s = val.toLowerCase();
        if (s === "true" || s === "1") out[key] = true;
        else if (s === "false" || s === "0") out[key] = false;
      }
    });
    return out;
  }

  function defaultHighlight() {
    return {
      green: { enabled: true, hex: "#1b8f3a" },
      yellow: { enabled: true, hex: "#c4a000" },
      red: { enabled: true, hex: "#c62828" },
    };
  }

  function normalizeHighlight(raw) {
    const out = defaultHighlight();
    if (!raw || typeof raw !== "object") return out;
    HIGHLIGHT_KEYS.forEach((key) => {
      const item = raw[key];
      if (!item || typeof item !== "object") return;
      if (typeof item.enabled === "boolean") out[key].enabled = item.enabled;
      else if (item.enabled === 0 || item.enabled === 1)
        out[key].enabled = !!item.enabled;
      else if (typeof item.enabled === "string") {
        const s = item.enabled.toLowerCase();
        if (s === "true" || s === "1") out[key].enabled = true;
        else if (s === "false" || s === "0") out[key].enabled = false;
      }
      const hex = String(item.hex || "").trim();
      if (HEX_RE.test(hex)) out[key].hex = hex.toLowerCase();
    });
    return out;
  }

  function emptyData() {
    return {
      version: VERSION,
      dict_extra: [],
      dict_exclude: [],
      patches: {},
      custom_lists: {},
      highlight: defaultHighlight(),
      vocab_output: defaultVocabOutput(),
    };
  }

  function emptyDictEntry(word) {
    return {
      word: String(word || "")
        .trim()
        .toLowerCase(),
      phonetic: "",
      definition: "",
      translation: "",
      pos: "",
      exchange: "",
    };
  }

  function normalizeWords(list) {
    const out = new Set();
    (list || []).forEach((w) => {
      const t = String(w || "")
        .trim()
        .toLowerCase();
      if (t) out.add(t);
    });
    return Array.from(out).sort();
  }

  function normalizeDictEntry(raw, requireGloss) {
    if (typeof raw === "string") {
      const word = raw.trim().toLowerCase();
      if (!word) return null;
      if (requireGloss) {
        throw new Error("「" + word + "」加入大词典时必须填写中文释义。");
      }
      return emptyDictEntry(word);
    }
    if (!raw || typeof raw !== "object") return null;
    const word = String(raw.word || "")
      .trim()
      .toLowerCase();
    if (!word) return null;
    const entry = emptyDictEntry(word);
    entry.phonetic = String(raw.phonetic || "").trim();
    entry.definition = String(raw.definition || "").trim();
    entry.translation = String(raw.translation || "").trim();
    entry.pos = String(raw.pos || "").trim();
    entry.exchange = String(raw.exchange || "").trim();
    if (requireGloss) {
      if (!entry.translation) {
        throw new Error("「" + word + "」加入大词典时必须填写中文释义。");
      }
    }
    return entry;
  }

  function normalizeDictExtra(list) {
    const byWord = {};
    (Array.isArray(list) ? list : []).forEach((item) => {
      try {
        const entry = normalizeDictEntry(item, false);
        if (entry) byWord[entry.word] = entry;
      } catch (_) {
        /* skip */
      }
    });
    return Object.keys(byWord)
      .sort()
      .map((k) => byWord[k]);
  }

  function safeListName(name) {
    let raw = String(name || "").trim();
    if (!raw) return "";
    raw = raw.split(/[/\\]/).pop();
    if (!raw.toLowerCase().endsWith(".txt")) raw += ".txt";
    return raw;
  }

  function load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return emptyData();
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object") return emptyData();
      return {
        version: VERSION,
        dict_extra: normalizeDictExtra(parsed.dict_extra),
        dict_exclude: normalizeWords(parsed.dict_exclude),
        patches: sanitizePatches(parsed.patches),
        custom_lists: sanitizeCustoms(parsed.custom_lists),
        highlight: normalizeHighlight(parsed.highlight),
        vocab_output: normalizeVocabOutput(parsed.vocab_output),
      };
    } catch (_) {
      return emptyData();
    }
  }

  function sanitizePatches(patches) {
    const out = {};
    if (!patches || typeof patches !== "object") return out;
    Object.keys(patches).forEach((name) => {
      const key = safeListName(name);
      const p = patches[name];
      if (!key || !p || typeof p !== "object") return;
      const add = new Set(normalizeWords(p.add));
      const remove = new Set(normalizeWords(p.remove));
      add.forEach((w) => {
        if (remove.has(w)) {
          add.delete(w);
          remove.delete(w);
        }
      });
      if (add.size || remove.size) {
        out[key] = {
          add: Array.from(add).sort(),
          remove: Array.from(remove).sort(),
        };
      }
    });
    return out;
  }

  function sanitizeCustoms(customs) {
    const out = {};
    if (!customs || typeof customs !== "object") return out;
    Object.keys(customs).forEach((name) => {
      const key = safeListName(name);
      if (!key) return;
      out[key] = normalizeWords(customs[name]);
    });
    return out;
  }

  function save(data) {
    const payload = {
      version: VERSION,
      dict_extra: normalizeDictExtra(data.dict_extra),
      dict_exclude: normalizeWords(data.dict_exclude),
      patches: sanitizePatches(data.patches),
      custom_lists: sanitizeCustoms(data.custom_lists),
      highlight: normalizeHighlight(data && data.highlight),
      vocab_output: normalizeVocabOutput(data && data.vocab_output),
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    return payload;
  }

  function dump() {
    return JSON.stringify(load());
  }

  function replaceAll(data) {
    return save(data && typeof data === "object" ? data : emptyData());
  }

  function clear() {
    localStorage.removeItem(STORAGE_KEY);
    return emptyData();
  }

  function getSelected() {
    return localStorage.getItem(SELECTED_KEY) || "words.txt";
  }

  function setSelected(name) {
    const key = safeListName(name) || "words.txt";
    localStorage.setItem(SELECTED_KEY, key);
    return key;
  }

  /** 合并服务器基准选项与本地自建表 */
  function mergeWordlistOptions(selectEl, baselineNames) {
    if (!selectEl) return;
    const data = load();
    const selected = getSelected();
    const names = [];
    const seen = new Set();
    (baselineNames || []).forEach((n) => {
      if (!seen.has(n)) {
        names.push(n);
        seen.add(n);
      }
    });
    Object.keys(data.custom_lists)
      .sort()
      .forEach((n) => {
        if (!seen.has(n)) {
          names.push(n);
          seen.add(n);
        }
      });

    selectEl.innerHTML = "";
    names.forEach((name) => {
      const opt = document.createElement("option");
      opt.value = name;
      const patched = data.patches[name];
      const isCustom = Object.prototype.hasOwnProperty.call(data.custom_lists, name);
      let label = name;
      if (isCustom) label += "（本机）";
      else if (patched && (patched.add.length || patched.remove.length))
        label += "（已改）";
      opt.textContent = label;
      if (name === selected) opt.selected = true;
      selectEl.appendChild(opt);
    });
    if (!names.includes(selected) && names.length) {
      selectEl.value = names[0];
      setSelected(names[0]);
    }
  }

  /** 表单提交前写入隐藏域 */
  function attachHiddenField(form, fieldName) {
    if (!form) return;
    const name = fieldName || "user_data";
    let input = form.querySelector(`input[name="${name}"]`);
    if (!input) {
      input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      form.appendChild(input);
    }
    const sync = () => {
      input.value = dump();
      const sel = form.querySelector('select[name="wordlist"]');
      if (sel && sel.value) setSelected(sel.value);
    };
    form.addEventListener("submit", sync);
    sync();
  }

  /** 结果页：用服务端算好的新差分覆盖本地 */
  function applyServerPayload(jsonText) {
    if (!jsonText) return;
    try {
      const data = typeof jsonText === "string" ? JSON.parse(jsonText) : jsonText;
      replaceAll(data);
    } catch (err) {
      console.warn("无法保存用户差分", err);
    }
  }

  function summaryText() {
    const d = load();
    const patchCount = Object.keys(d.patches).length;
    const customCount = Object.keys(d.custom_lists).length;
    const extra = d.dict_extra.length;
    const excl = d.dict_exclude.length;
    if (!patchCount && !customCount && !extra && !excl) {
      return "本浏览器尚未保存任何对照表/词典改动。";
    }
    return (
      `本机已存：词典增补词条 ${extra}、排除 ${excl}；` +
      `基准表差分 ${patchCount} 份；自建对照表 ${customCount} 份。`
    );
  }

  global.UserDataStore = {
    STORAGE_KEY,
    DEFAULT_HIGHLIGHT,
    emptyData,
    emptyDictEntry,
    normalizeDictEntry,
    normalizeDictExtra,
    defaultHighlight,
    normalizeHighlight,
    defaultVocabOutput,
    normalizeVocabOutput,
    load,
    save,
    dump,
    replaceAll,
    clear,
    getSelected,
    setSelected,
    mergeWordlistOptions,
    attachHiddenField,
    applyServerPayload,
    summaryText,
    safeListName,
    normalizeWords,
  };
})(typeof window !== "undefined" ? window : globalThis);
