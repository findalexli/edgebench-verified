// Independent small semantic analyzer written only from the v2 TASK.md contract
// (analyze(program) -> array of {level, message}) and CHEATSHEET scoping rules.
// Works on program.source (the starter parser keeps statement text only).
const KEYWORDS = new Set(["let","mut","fn","if","el","else","for","in","match","true","false","nil","return","while","and","or","not","type","use","import","export","async","await","break","continue","do"]);
let BUILTINS = new Set(["print","len","map","filter","reduce","sum","range","keys","values","str","int","float","push","join","split","slice","upper","lower","trim","abs","min","max","sort","reverse","contains","type_of"]);
try { const env = require("./runtime.js").createEnv(); if (env && typeof env === "object") { const vars = env.vars || env.values || env; for (const k of (vars instanceof Map ? vars.keys() : Object.keys(vars))) BUILTINS.add(k); } } catch (_) {}

function tokenize(src) {
  const toks = []; let i = 0;
  while (i < src.length) {
    const c = src[i];
    if (c === "\n") { toks.push({ t: "nl", v: "\n" }); i++; continue; }
    if (/\s/.test(c)) { i++; continue; }
    if (c === "#") { while (i < src.length && src[i] !== "\n") i++; continue; }
    if (c === '"' || c === "'" || c === "`") { let j = i + 1; while (j < src.length && src[j] !== c) { if (src[j] === "\\") j++; j++; } toks.push({ t: "str", v: src.slice(i, j + 1) }); i = j + 1; continue; }
    if (/[A-Za-z_]/.test(c)) { let j = i; while (j < src.length && /[A-Za-z0-9_]/.test(src[j])) j++; toks.push({ t: "id", v: src.slice(i, j) }); i = j; continue; }
    if (/[0-9]/.test(c)) { let j = i; while (j < src.length && /[0-9._]/.test(src[j])) j++; toks.push({ t: "num", v: src.slice(i, j) }); i = j; continue; }
    const two = src.slice(i, i + 2);
    if (["=>","==","!=","<=",">=","..","|>","->","&&","||"].includes(two)) { toks.push({ t: "op", v: two }); i += 2; continue; }
    toks.push({ t: "op", v: c }); i++;
  }
  return toks;
}

function analyze(program) {
  const src = typeof program === "string" ? program : (program && program.source) || "";
  const diags = [];
  const toks = tokenize(src);
  const scopes = [new Map()];
  const lookup = (n) => { for (let s = scopes.length - 1; s >= 0; s--) if (scopes[s].has(n)) return scopes[s].get(n); return null; };
  const declare = (n, info) => scopes[scopes.length - 1].set(n, info);
  // stack of open frames: {kind:'brace'|'paren'|'bracket'|'arrow', depth}
  const frames = [];
  // hoist fn declarations in the block starting at token index k (until matching close)
  function hoist(k) {
    let d = 0;
    for (let j = k; j < toks.length; j++) {
      const v = toks[j].v;
      if (v === "{" || v === "(" || v === "[") d++;
      else if (v === "}" || v === ")" || v === "]") { if (d === 0) break; d--; }
      else if (d === 0 && v === "fn" && toks[j + 1] && toks[j + 1].t === "id") {
        let n = 0, p = j + 3, dd = 0, any = false;
        for (; p < toks.length; p++) { const w = toks[p].v; if (w === "(" || w === "[" || w === "{") dd++; else if (w === ")" && dd === 0) break; else if (w === ")" || w === "]" || w === "}") dd--; else if (w === "," && dd === 0) n++; else any = true; }
        declare(toks[j + 1].v, { kind: "fn", arity: any ? n + 1 : 0, mutable: false });
      }
    }
  }
  function closeArrows(atNewline) {
    while (frames.length && frames[frames.length - 1].kind === "arrow" && frames[frames.length - 1].nest === 0) { frames.pop(); scopes.pop(); if (!atNewline) break; }
  }
  hoist(0);
  let pendingParams = null; // params to inject into the next scope opened by fn body
  for (let i = 0; i < toks.length; i++) {
    const tk = toks[i], v = tk.v, prev = toks[i - 1], next = toks[i + 1];
    const top = frames[frames.length - 1];
    if (tk.t === "nl" || v === ";") { if (top && top.kind === "arrow" && top.nest === 0) { frames.pop(); scopes.pop(); } continue; }
    if (v === "{" || v === "(" || v === "[") {
      if (top && top.kind === "arrow") top.nest++;
      frames.push({ kind: v });
      if (v === "{") { scopes.push(new Map()); if (pendingParams) { for (const p of pendingParams) declare(p, { kind: "var", mutable: false }); pendingParams = null; } hoist(i + 1); }
      continue;
    }
    if (v === "}" || v === ")" || v === "]") {
      while (frames.length && frames[frames.length - 1].kind === "arrow" && frames[frames.length - 1].nest === 0) { frames.pop(); scopes.pop(); }
      const f = frames.pop(); if (f && f.kind === "{") scopes.pop();
      const t2 = frames[frames.length - 1]; if (t2 && t2.kind === "arrow") t2.nest--;
      continue;
    }
    if (v === "fn" && next && next.t === "id") {
      // collect params
      const params = []; let j = i + 3;
      for (; j < toks.length && toks[j].v !== ")"; j++) if (toks[j].t === "id" && toks[j + 1] && toks[j + 1].v !== ":" ) params.push(toks[j].v); else if (toks[j].t === "id") params.push(toks[j].v);
      i = j; // at ')'
      // skip optional return type until '{' or '=>'
      let k = i + 1; while (k < toks.length && toks[k].v !== "{" && toks[k].v !== "=>") k++;
      if (toks[k] && toks[k].v === "=>") { scopes.push(new Map()); for (const p of params) declare(p, { kind: "var", mutable: false }); frames.push({ kind: "arrow", nest: 0 }); i = k; }
      else { pendingParams = params; i = k - 1; }
      continue;
    }
    if (v === "let") {
      let j = i + 1, mutable = false;
      if (toks[j] && toks[j].v === "mut") { mutable = true; j++; }
      const names = [];
      if (toks[j] && (toks[j].v === "{" || toks[j].v === "[")) { const close = toks[j].v === "{" ? "}" : "]"; j++; for (; j < toks.length && toks[j].v !== close; j++) if (toks[j].t === "id") names.push(toks[j].v); }
      else if (toks[j] && toks[j].t === "id") names.push(toks[j].v);
      // RHS is analyzed with the names not yet declared; declare after the statement start by deferring
      for (const n of names) declare(n, { kind: "var", mutable });
      i = j; continue;
    }
    if (v === "for" && next && next.t === "id") {
      pendingParams = [next.v]; i++; continue;
    }
    if (tk.t === "id") {
      if (KEYWORDS.has(v) || v === "_") continue;
      if (prev && prev.v === ".") continue;
      if (next && next.v === ":") continue; // object key / type annotation
      const info = lookup(v);
      if (!info && !BUILTINS.has(v)) { diags.push({ level: "error", message: `Undefined variable '${v}'` }); continue; }
      if (next && next.v === "=" && info && info.kind === "var" && !info.mutable) diags.push({ level: "error", message: `Cannot reassign immutable variable '${v}'` });
      if (next && next.v === "(" && info && info.kind === "fn") {
        let d = 0, n = 0, any = false, j = i + 2;
        for (; j < toks.length; j++) { const w = toks[j].v; if (w === "(" || w === "[" || w === "{") d++; else if (w === ")" && d === 0) break; else if (w === ")" || w === "]" || w === "}") d--; else if (w === "," && d === 0) n++; else if (toks[j].t !== "nl") any = true; }
        const got = any ? n + 1 : 0;
        if (got !== info.arity) diags.push({ level: "error", message: `Function '${v}' expects ${info.arity} arguments, got ${got}` });
      }
    }
  }
  return diags;
}
function checkSemantics(program) { return analyze(program); }
module.exports = { analyze, checkSemantics };
