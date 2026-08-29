const state = {
  data: null,
  refs: { sites: [] },
  view: "icons",
  collectionId: "fa-7.3.0",
  styleId: "solid",
  query: "",
  searchAll: false,
  selected: null,
};

const ALL_ID = "all";
const ALL_PREF = ["cs2", "dopamina", "fa-7.3.0", "remix", "embedded-weapons", "iconsv2"];

const $ = (id) => document.getElementById(id);

function collection() {
  return state.data.collections.find((c) => c.id === state.collectionId);
}

function styleOf(col) {
  if (!col?.styles) return null;
  return col.styles.find((s) => s.id === state.styleId) || col.styles[0];
}

function hay(icon) {
  return [icon.name, ...(icon.aliases || [])].join(" ").toLowerCase();
}

function matches(icon, query) {
  if (!query) return true;
  const q = query.toLowerCase().trim();
  const h = hay(icon);
  if (h.includes(q)) return true;
  return q.split(/\s+/).every((t) => h.includes(t));
}

function defaultStyle(col, icon) {
  if (!col?.styles) return null;
  if (icon?.brand) return col.styles.find((s) => s.brand) || col.styles[0];
  return col.styles.find((s) => s.id === "solid") || col.styles[0];
}

function scoreHit(query, icon, colId) {
  const q = query.toLowerCase().trim();
  const name = (icon.name || "").toLowerCase();
  const aliases = (icon.aliases || []).map((a) => a.toLowerCase());
  let score = 0;
  if (name === q || aliases.includes(q)) score += 200;
  else if (name.startsWith(q) || aliases.some((a) => a.startsWith(q))) score += 120;
  else if (name.includes(q) || aliases.some((a) => a.includes(q))) score += 80;
  const tokens = q.split(/\s+/).filter(Boolean);
  score += tokens.filter((t) => hay(icon).includes(t)).length * 18;
  const pref = ALL_PREF.indexOf(colId);
  if (pref >= 0) score += 12 - pref;
  return score;
}

function filteredIcons() {
  const col = collection();
  if (!col) return [];
  let icons = col.icons || [];
  const style = styleOf(col);
  if (col.kind === "fa" && style) {
    icons = style.brand ? icons.filter((i) => i.brand) : icons.filter((i) => !i.brand);
  }
  return icons.filter((i) => matches(i, state.query)).map((icon) => ({ col, icon, style }));
}

function filteredAllIcons() {
  const q = state.query.trim();
  if (!q) return [];
  const hits = [];
  state.data.collections.forEach((col) => {
    (col.icons || []).forEach((icon) => {
      if (!matches(icon, q)) return;
      const style = defaultStyle(col, icon);
      hits.push({ col, icon, style, score: scoreHit(q, icon, col.id) });
    });
  });
  hits.sort((a, b) => b.score - a.score || a.col.name.localeCompare(b.col.name) || a.icon.name.localeCompare(b.icon.name));
  return hits;
}

function filteredFonts() {
  const q = state.query.toLowerCase().trim();
  return (state.data.fonts || []).filter((f) => {
    if (!q) return true;
    const h = [f.name, f.path, f.family, f.use, f.kind, f.source].join(" ").toLowerCase();
    return q.split(/\s+/).every((t) => h.includes(t));
  });
}

function loadFaSheets(col, style) {
  $("fa-core").href = style && col?.kind === "fa" ? `../${col.cssBase}${col.coreCss}` : "";
  $("fa-style").href = style && col?.kind === "fa" ? `../${col.cssBase}${style.css}` : "";
}

function faFamilyName(col, style) {
  return `LibFA ${col.id} ${style?.id || "solid"}`;
}

function ensureFaGlyphFont(col, style) {
  if (!col || col.kind !== "fa" || !style?.webfont) return;
  const id = `fa-ff-${col.id}-${style.id}`;
  if (document.getElementById(id)) return;
  const href = `../${col.cssBase.replace(/css\/$/, "")}${style.webfont}`;
  const sheet = document.createElement("style");
  sheet.id = id;
  sheet.textContent = `@font-face{font-family:"${faFamilyName(col, style)}";src:url("${href}");font-display:swap;}`;
  document.head.appendChild(sheet);
}

function ensureFontFace(col) {
  if (!col || col.kind === "fa" || col.kind === "svg" || col.kind === "bdf" || !col.fontUrl) return;
  const id = `ff-${col.id}`;
  if (document.getElementById(id)) return;
  const style = document.createElement("style");
  style.id = id;
  style.textContent = `@font-face{font-family:"${col.fontFamily}";src:url("../${col.fontUrl}");font-display:swap;}`;
  document.head.appendChild(style);
}

function ensureTextFont(font) {
  if (font.kind === "bdf" || font.format === "bdf") return;
  const id = `tf-${font.id}`;
  if (document.getElementById(id)) return;
  const family = `Spec ${font.id}`;
  const style = document.createElement("style");
  style.id = id;
  style.textContent = `@font-face{font-family:"${family}";src:url("../${font.path}");font-display:swap;}`;
  document.head.appendChild(style);
  font._cssFamily = family;
}

function hexRowBits(hex) {
  const bits = [];
  const clean = hex.trim();
  for (let i = 0; i < clean.length; i += 1) {
    const n = parseInt(clean[i], 16);
    if (Number.isNaN(n)) continue;
    bits.push((n >> 3) & 1, (n >> 2) & 1, (n >> 1) & 1, n & 1);
  }
  return bits;
}

function drawBdf(icon, canvas, scale = 2) {
  const [w, h] = icon.bbx || [0, 0];
  const rows = icon.bitmap || [];
  canvas.width = Math.max(1, w * scale);
  canvas.height = Math.max(1, h * scale);
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#eceae4";
  rows.forEach((hex, y) => {
    const bits = hexRowBits(hex);
    for (let x = 0; x < w; x += 1) {
      if (bits[x] === 1) ctx.fillRect(x * scale, y * scale, scale, scale);
    }
  });
}

function className(col, icon, style) {
  if (col.kind === "fa") {
    const st = style || styleOf(col);
    return `${st?.iconClass || "fa-solid"} fa-${icon.name}`;
  }
  if (col.id === "remix") {
    return icon.name.startsWith("ri-") ? icon.name : `ri-${icon.name}`;
  }
  return null;
}

function usage(col, icon, style) {
  const cls = className(col, icon, style);
  if (col.kind === "fa") return `<i class="${cls}"></i>`;
  if (col.kind === "svg") return icon.path;
  if (col.kind === "bdf") return `${col.fontUrl}  U+${icon.unicode.toUpperCase()}  (${col.id})`;
  const ch = String.fromCodePoint(parseInt(icon.unicode, 16));
  const typed = icon.input ? ` type '${icon.input}'` : "";
  return `@font-face { font-family: "${col.fontFamily}"; src: url("${col.fontUrl}"); }\nspan { font-family: "${col.fontFamily}"; } /* ${ch} U+${icon.unicode.toUpperCase()}${typed} */`;
}

function renderCollections() {
  const host = $("collections");
  host.innerHTML = "";
  const label = document.querySelector(".nav-label");
  if (label) {
    label.textContent = state.view === "refs" ? "References" : "Collections";
  }
  if (state.view === "fonts") {
    const btn = document.createElement("button");
    btn.className = "collection is-active";
    btn.innerHTML = `<span>Typefaces</span><span>${state.data.fonts.length}</span>`;
    host.appendChild(btn);
    return;
  }
  if (state.view === "icons") {
    const all = document.createElement("button");
    const total = state.data.collections.reduce((n, c) => n + c.icons.length, 0);
    all.className = `collection${state.searchAll ? " is-active" : ""}`;
    all.innerHTML = `<span>All icons</span><span>${total}</span>`;
    all.addEventListener("click", () => {
      state.searchAll = true;
      state.collectionId = ALL_ID;
      state.selected = null;
      render();
    });
    host.appendChild(all);
  }
  if (state.view === "refs") {
    const btn = document.createElement("button");
    btn.className = "collection is-active";
    btn.innerHTML = `<span>UI references</span><span>${state.refs.sites.length}</span>`;
    host.appendChild(btn);
    return;
  }
  state.data.collections.forEach((col) => {
    const btn = document.createElement("button");
    btn.className = `collection${!state.searchAll && col.id === state.collectionId ? " is-active" : ""}`;
    btn.innerHTML = `<span>${col.name}</span><span>${col.icons.length}</span>`;
    btn.addEventListener("click", () => {
      state.searchAll = false;
      state.collectionId = col.id;
      state.styleId = col.styles?.some((s) => s.id === "solid") ? "solid" : col.styles?.[0]?.id || state.styleId;
      state.selected = null;
      render();
    });
    host.appendChild(btn);
  });
}

function renderStyles() {
  const host = $("styles");
  const col = collection();
  host.innerHTML = "";
  if (state.view !== "icons" || state.searchAll || !col?.styles) {
    host.hidden = true;
    return;
  }
  host.hidden = false;
  const preferred = ["solid", "regular", "light", "thin", "brands", "duotone", "sharp-solid"];
  const ordered = [
    ...preferred.map((id) => col.styles.find((s) => s.id === id)).filter(Boolean),
    ...col.styles.filter((s) => !preferred.includes(s.id)),
  ];
  ordered.forEach((style) => {
    const chip = document.createElement("button");
    chip.className = `chip${style.id === state.styleId ? " is-active" : ""}`;
    chip.textContent = style.label;
    chip.addEventListener("click", () => {
      state.styleId = style.id;
      state.selected = null;
      render();
    });
    host.appendChild(chip);
  });
}

function iconPreview(col, icon, style, large = false) {
  const wrap = document.createElement(large ? "div" : "span");
  wrap.className = large ? "detail-preview" : "glyph";
  if (col.kind === "fa" && state.searchAll) {
    ensureFaGlyphFont(col, style);
    wrap.style.fontFamily = `"${faFamilyName(col, style)}"`;
    wrap.textContent = String.fromCodePoint(parseInt(icon.unicode, 16));
  } else if (col.kind === "fa") {
    const i = document.createElement("i");
    i.className = className(col, icon, style);
    wrap.appendChild(i);
  } else if (col.kind === "svg") {
    const img = document.createElement("img");
    img.src = `../${icon.path}`;
    img.alt = icon.name;
    wrap.appendChild(img);
  } else if (col.kind === "bdf") {
    const canvas = document.createElement("canvas");
    drawBdf(icon, canvas, large ? 4 : 2);
    wrap.appendChild(canvas);
  } else {
    wrap.style.fontFamily = `"${col.fontFamily}"`;
    wrap.textContent = String.fromCodePoint(parseInt(icon.unicode, 16));
  }
  return wrap;
}

function renderGrid() {
  const grid = $("grid");
  grid.className = "grid";
  grid.innerHTML = "";
  if (state.view === "fonts") {
    renderFonts(grid);
    return;
  }
  if (state.view === "refs") {
    renderRefs(grid);
    return;
  }
  const hits = state.searchAll ? filteredAllIcons() : filteredIcons();
  const seen = new Set();
  hits.forEach(({ col, style }) => {
    const key = `${col.id}:${style?.id || ""}`;
    if (seen.has(key)) return;
    seen.add(key);
    ensureFontFace(col);
    if (col.kind === "fa" && state.searchAll) ensureFaGlyphFont(col, style);
  });
  if (!state.searchAll) {
    const col = collection();
    loadFaSheets(col, styleOf(col));
  } else {
    loadFaSheets(null, null);
  }

  const total = state.searchAll
    ? state.data.collections.reduce((n, c) => n + c.icons.length, 0)
    : collection()?.icons.length || 0;
  $("result-meta").textContent = state.searchAll && !state.query.trim()
    ? `${total} in all sets`
    : `${hits.length} / ${total}`;

  if (state.searchAll && !state.query.trim()) {
    grid.innerHTML = `<div class="empty">Type to search every icon set.</div>`;
    return;
  }
  if (!hits.length) {
    grid.innerHTML = `<div class="empty">No icons match “${state.query}”.</div>`;
    return;
  }

  const PAGE = 360;
  let shown = Math.min(PAGE, hits.length);
  const appendHit = (host, hit) => {
    const { col, icon, style } = hit;
    const btn = document.createElement("button");
    const key = `${col.id}:${icon.name}:${icon.unicode || icon.path}`;
    btn.className = `icon-cell${state.selected?.key === key ? " is-selected" : ""}`;
    btn.appendChild(iconPreview(col, icon, style));
    const label = document.createElement("div");
    label.className = "glyph-label";
    label.textContent = icon.name;
    btn.appendChild(label);
    if (state.searchAll) {
      const set = document.createElement("div");
      set.className = "glyph-set";
      set.textContent = col.name;
      btn.appendChild(set);
    }
    btn.addEventListener("click", () => {
      state.selected = { type: "icon", key, col, icon, style };
      renderDetailOnly();
      grid.querySelectorAll(".icon-cell.is-selected").forEach((el) => el.classList.remove("is-selected"));
      btn.classList.add("is-selected");
    });
    host.appendChild(btn);
  };
  const frag = document.createDocumentFragment();
  for (let i = 0; i < shown; i += 1) appendHit(frag, hits[i]);
  grid.appendChild(frag);
  if (shown < hits.length) {
    const more = document.createElement("button");
    more.className = "icon-cell more";
    more.textContent = `Show all ${hits.length}`;
    more.addEventListener("click", () => {
      more.remove();
      const rest = document.createDocumentFragment();
      for (let i = shown; i < hits.length; i += 1) appendHit(rest, hits[i]);
      shown = hits.length;
      grid.appendChild(rest);
    });
    grid.appendChild(more);
  }
}

function filteredRefs() {
  const q = state.query.toLowerCase().trim();
  return (state.refs.sites || []).filter((site) => {
    if (!q) return true;
    const h = [site.name, site.url, site.use, site.id].join(" ").toLowerCase();
    return q.split(/\s+/).every((t) => h.includes(t));
  });
}

function renderRefs(host) {
  host.className = "refs";
  const sites = filteredRefs();
  $("result-meta").textContent = `${sites.length} sites`;
  if (!sites.length) {
    host.innerHTML = `<div class="empty">No references match “${state.query}”.</div>`;
    return;
  }
  sites.forEach((site) => {
    const card = document.createElement("a");
    card.className = `ref-card${state.selected?.key === site.id ? " is-selected" : ""}`;
    card.href = site.url;
    card.target = "_blank";
    card.rel = "noreferrer";
    card.innerHTML = `
      <div class="font-head">
        <div class="font-name">${site.name}</div>
      </div>
      <p class="font-use">${site.use}</p>
      <div class="ref-url">${site.url}</div>
    `;
    card.addEventListener("click", (e) => {
      if (e.metaKey || e.ctrlKey) return;
      e.preventDefault();
      state.selected = { type: "ref", key: site.id, site };
      render();
    });
    host.appendChild(card);
  });
}

function renderDetailOnly() {
  renderDetail();
}

function renderFonts(host) {
  host.className = "fonts";
  const fonts = filteredFonts();
  $("result-meta").textContent = `${fonts.length} faces`;
  if (!fonts.length) {
    host.innerHTML = `<div class="empty">No fonts match “${state.query}”.</div>`;
    return;
  }
  fonts.forEach((font) => {
    ensureTextFont(font);
    const card = document.createElement("button");
    card.className = `font-card${state.selected?.key === font.id ? " is-selected" : ""}`;
    const sample = font.kind === "bdf" || font.format === "bdf"
      ? `<div class="bdf-row" data-bdf="${font.id}"></div>`
      : `<div class="specimen" style="font-family:'${font._cssFamily || font.family}'">Hamburglefons 012345</div>`;
    card.innerHTML = `
      <div class="font-head">
        <div>
          <div class="font-name">${font.name}</div>
          <div class="font-path">${font.path}</div>
        </div>
        <div class="specimen-meta">${font.kind || ""}${font.glyphCount ? ` · ${font.glyphCount} glyphs` : ""}</div>
      </div>
      <p class="font-use">${font.use || ""}</p>
      ${sample}
    `;
    if (font.kind === "bdf" || font.format === "bdf") {
      const col = state.data.collections.find((c) => c.id === font.id);
      const row = card.querySelector("[data-bdf]");
      const pangram = "ABCabc012";
      pangram.split("").forEach((ch) => {
        const icon = col?.icons.find((i) => parseInt(i.unicode, 16) === ch.charCodeAt(0));
        if (!icon) return;
        const canvas = document.createElement("canvas");
        drawBdf(icon, canvas, 2);
        row.appendChild(canvas);
      });
    }
    card.addEventListener("click", () => {
      state.selected = { type: "font", key: font.id, font };
      render();
    });
    host.appendChild(card);
  });
}

function copyBtn(label, value) {
  const btn = document.createElement("button");
  btn.className = "copy";
  btn.textContent = "Copy";
  btn.addEventListener("click", async (e) => {
    e.stopPropagation();
    await navigator.clipboard.writeText(value);
    btn.textContent = "Copied";
    setTimeout(() => { btn.textContent = "Copy"; }, 900);
  });
  const item = document.createElement("div");
  item.className = "kv-item";
  item.innerHTML = `<label>${label}</label><div class="kv-row"><code></code></div>`;
  item.querySelector("code").textContent = value;
  item.querySelector(".kv-row").appendChild(btn);
  return item;
}

function fileSafe(name) {
  return String(name || "icon").replace(/[^\w.-]+/g, "-").replace(/^-+|-+$/g, "") || "icon";
}

function iconFileName(col, icon, style) {
  const base = fileSafe(icon.name);
  if (col.kind === "svg" && icon.path) {
    const ext = (icon.path.split(".").pop() || "svg").toLowerCase();
    return `${base}.${ext}`;
  }
  if (style?.id && style.id !== "solid") return `${base}-${fileSafe(style.id)}.png`;
  return `${base}.png`;
}

function canDownloadIcon(col, icon) {
  return Boolean((col.kind === "svg" && icon.path) || icon.unicode || (col.kind === "bdf" && icon.bitmap));
}

function triggerDownload(href, filename) {
  const a = document.createElement("a");
  a.href = href;
  a.download = filename;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
}

function canvasPng(canvas) {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("png"))), "image/png");
  });
}

async function rasterizeGlyph(col, icon, style) {
  if (col.kind === "bdf") {
    const canvas = document.createElement("canvas");
    drawBdf(icon, canvas, 16);
    return canvasPng(canvas);
  }
  if (col.kind === "fa") ensureFaGlyphFont(col, style);
  else ensureFontFace(col);
  const family = col.kind === "fa" ? faFamilyName(col, style) : col.fontFamily;
  const ch = String.fromCodePoint(parseInt(icon.unicode, 16));
  const spec = `${style?.weight || 400} 448px "${family}"`;
  try {
    await document.fonts.load(spec);
  } catch (_) { /* draw anyway */ }
  await document.fonts.ready;
  const size = 512;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, size, size);
  ctx.fillStyle = "#eceae4";
  ctx.font = spec;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(ch, size / 2, size / 2);
  return canvasPng(canvas);
}

async function downloadCurrentIcon(col, icon, style) {
  const name = iconFileName(col, icon, style);
  if (col.kind === "svg" && icon.path) {
    triggerDownload(`../${icon.path}`, name);
    return;
  }
  const blob = await rasterizeGlyph(col, icon, style);
  const href = URL.createObjectURL(blob);
  triggerDownload(href, name);
  setTimeout(() => URL.revokeObjectURL(href), 2000);
}

function downloadBtn(col, icon, style) {
  const name = iconFileName(col, icon, style);
  const isFile = col.kind === "svg" && icon.path;
  const el = document.createElement(isFile ? "a" : "button");
  el.className = "download";
  el.textContent = `Download ${name}`;
  if (isFile) {
    el.href = `../${icon.path}`;
    el.download = name;
  } else {
    el.type = "button";
    el.addEventListener("click", async (e) => {
      e.stopPropagation();
      el.disabled = true;
      try {
        await downloadCurrentIcon(col, icon, style);
      } finally {
        el.disabled = false;
      }
    });
  }
  return el;
}

function renderDetail() {
  const host = $("detail");
  const workspace = document.querySelector(".workspace");
  if (!state.selected) {
    host.hidden = true;
    workspace.classList.remove("has-detail");
    return;
  }
  host.hidden = false;
  workspace.classList.add("has-detail");
  host.innerHTML = "";
  if (state.selected.type === "icon") {
    const { col, icon, style } = state.selected;
    host.appendChild(iconPreview(col, icon, style, true));
    const title = document.createElement("h2");
    title.textContent = icon.name;
    host.appendChild(title);
    const sub = document.createElement("div");
    sub.className = "muted";
    sub.textContent = `${col.name}${style ? ` · ${style.label}` : ""}`;
    host.appendChild(sub);
    if (canDownloadIcon(col, icon)) host.appendChild(downloadBtn(col, icon, style));
    const kv = document.createElement("div");
    kv.className = "kv";
    const cls = className(col, icon, style);
    if (cls) kv.appendChild(copyBtn("Class", cls));
    if (icon.input) kv.appendChild(copyBtn("Key", icon.input));
    if (icon.unicode) kv.appendChild(copyBtn("Unicode", `U+${icon.unicode.toUpperCase()}`));
    if (icon.path) kv.appendChild(copyBtn("Path", icon.path));
    else if (col.fontUrl) kv.appendChild(copyBtn("Font", col.fontUrl));
    kv.appendChild(copyBtn("Usage", usage(col, icon, style)));
    if (icon.aliases?.length) kv.appendChild(copyBtn("Aliases", icon.aliases.join(", ")));
    host.appendChild(kv);
    return;
  }
  if (state.selected.type === "font") {
    const font = state.selected.font;
    const preview = document.createElement("div");
    preview.className = "detail-preview";
    if (font.kind === "bdf" || font.format === "bdf") {
      preview.textContent = "BDF";
    } else {
      preview.style.fontFamily = `'${font._cssFamily || font.family}'`;
      preview.textContent = "Ag";
    }
    host.appendChild(preview);
    const title = document.createElement("h2");
    title.textContent = font.name;
    host.appendChild(title);
    const sub = document.createElement("div");
    sub.className = "muted";
    sub.textContent = font.family || font.kind;
    host.appendChild(sub);
    const kv = document.createElement("div");
    kv.className = "kv";
    kv.appendChild(copyBtn("Path", font.path));
    if (font.source) kv.appendChild(copyBtn("Source", font.source));
    if (font.use) kv.appendChild(copyBtn("Use", font.use));
    kv.appendChild(copyBtn(
      "CSS",
      `@font-face {\n  font-family: "${font.family}";\n  src: url("${font.path}");\n}`
    ));
    host.appendChild(kv);
    return;
  }
  if (state.selected.type === "ref") {
    const site = state.selected.site;
    const preview = document.createElement("div");
    preview.className = "detail-preview";
    preview.textContent = "↗";
    host.appendChild(preview);
    const title = document.createElement("h2");
    title.textContent = site.name;
    host.appendChild(title);
    const sub = document.createElement("div");
    sub.className = "muted";
    sub.textContent = "UI reference";
    host.appendChild(sub);
    const kv = document.createElement("div");
    kv.className = "kv";
    kv.appendChild(copyBtn("URL", site.url));
    kv.appendChild(copyBtn("Use", site.use));
    const open = document.createElement("a");
    open.className = "copy";
    open.href = site.url;
    open.target = "_blank";
    open.rel = "noreferrer";
    open.textContent = "Open";
    open.style.textDecoration = "none";
    const item = document.createElement("div");
    item.className = "kv-item";
    item.appendChild(open);
    kv.appendChild(item);
    host.appendChild(kv);
    return;
  }
}

function render() {
  $("counts").textContent = `${state.data.collections.reduce((n, c) => n + c.icons.length, 0)} icons · ${state.data.fonts.length} faces`;
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("is-active", t.dataset.view === state.view));
  const allBtn = $("search-all");
  if (allBtn) {
    allBtn.hidden = state.view !== "icons";
    allBtn.classList.toggle("is-active", state.searchAll);
  }
  $("search").placeholder = state.view === "icons" && state.searchAll
    ? "Search every icon set"
    : "Search names, aliases, weapons, fonts";
  renderCollections();
  renderStyles();
  renderGrid();
  renderDetail();
}

async function init() {
  const [icons, fonts, refs] = await Promise.all([
    (await fetch("../catalog/icons.json")).json(),
    (await fetch("../catalog/fonts.json")).json(),
    (await fetch("../catalog/refs.json")).json(),
  ]);
  state.data = { collections: icons.collections, fonts: fonts.fonts };
  state.refs = refs;
  if (!state.data.collections.some((c) => c.id === state.collectionId)) {
    state.collectionId = state.data.collections[0].id;
  }
  $("search").addEventListener("input", (e) => {
    state.query = e.target.value;
    render();
  });
  $("search-all").addEventListener("click", () => {
    state.searchAll = !state.searchAll;
    state.collectionId = state.searchAll ? ALL_ID : (state.data.collections[0]?.id || "fa-7.3.0");
    state.selected = null;
    if (state.searchAll) $("search").focus();
    render();
  });
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      state.view = tab.dataset.view;
      state.selected = null;
      render();
    });
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && document.activeElement !== $("search")) {
      e.preventDefault();
      $("search").focus();
    }
    if (e.key === "Escape") {
      state.selected = null;
      render();
    }
  });
  render();
}

init();
