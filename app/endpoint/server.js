// RFI library retrieval service: a pass-through to Pinecone Documents search.
// Zero dependencies, Node 20+. The Pinecone key lives only in the environment.
//
//   POST /search            {question, topK?, stack?}   header X-RFI-Token: <RFI_TOKEN>
//   POST /mcp/<RFI_TOKEN>   MCP Streamable HTTP (stateless) exposing tool `search_library`
//   GET  /healthz
//
// Both routes return the JSON shape pipeline/query.py prints:
//   {query, mode, results:[{id, score, stack, updated, source, tags, legal_approved, question, answer}]}
//
// Env: PINECONE_API_KEY (required), PINECONE_INDEX (default rfi-answer-library),
//      RFI_TOKEN (required; org-visible shared secret), PORT (Cloud Run sets it).
"use strict";
const http = require("http");

const KEY = process.env.PINECONE_API_KEY;
const INDEX = process.env.PINECONE_INDEX || "rfi-answer-library";
const TOKEN = process.env.RFI_TOKEN;
if (!KEY || !TOKEN) { console.error("PINECONE_API_KEY and RFI_TOKEN are required"); process.exit(1); }

const VERSION = "2026-07";
const NAMESPACE = "__default__";
const FIELDS = ["question", "answer_plain", "stack_name", "tags", "last_updated_date", "source_doc", "source", "legal_approved"];
const CURATED = new Set(["Client Strategy- Cleaned", "RFI 2026"]);

let hostPromise;
async function indexHost() {
  hostPromise ||= pc(`https://api.pinecone.io/indexes/${INDEX}`).then(d => "https://" + d.host)
    .catch(e => { hostPromise = null; throw e; });
  return hostPromise;
}

async function pc(url, body) {
  const r = await fetch(url, {
    method: body ? "POST" : "GET",
    headers: { "Content-Type": "application/json", "Api-Key": KEY, "X-Pinecone-Api-Version": VERSION },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error(`pinecone ${r.status}: ${(await r.text()).slice(0, 300)}`);
  return r.json();
}

const norm = s => String(s || "").toLowerCase().split(/\s+/).join(" ");
const rankKey = m => [String(m.last_updated_date || ""), CURATED.has(m.stack_name) ? 1 : 0, m._score || 0];
const gt = (a, b) => { for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return a[i] > b[i]; return false; };

// One row per question; newest last_updated_date wins, curated stacks break ties. Same as query.py.
function collapse(matches, want) {
  const best = new Map();
  for (const m of matches) {
    const k = norm(m.question) || m._id;
    if (!best.has(k) || gt(rankKey(m), rankKey(best.get(k)))) best.set(k, m);
  }
  return [...best.values()].sort((a, b) => (b._score || 0) - (a._score || 0)).slice(0, want);
}

const shape = m => ({
  id: m._id, score: Math.round((m._score || 0) * 1e4) / 1e4, stack: m.stack_name,
  updated: String(m.last_updated_date || "").slice(0, 10), source: m.source_doc ?? null,
  tags: m.tags || [], legal_approved: !!m.legal_approved, question: m.question, answer: m.answer_plain,
});

async function search(question, topK = 5, stack) {
  if (typeof question !== "string" || !question.trim()) throw Object.assign(new Error("question is required"), { status: 400 });
  if (question.length > 8000) throw Object.assign(new Error("question too long"), { status: 400 });
  const want = Math.min(Math.max(parseInt(topK, 10) || 5, 1), 20);
  const body = { top_k: stack ? want : Math.max(want * 4, 20), include_fields: FIELDS,
    score_by: [{ type: "embed", fields: ["embed_text"], query: question }] };
  if (stack) body.filter = { stack_name: { $eq: String(stack) } };
  const { matches = [] } = await pc(`${await indexHost()}/namespaces/${NAMESPACE}/documents/search`, body);
  const rows = stack ? matches : collapse(matches, want);
  return { query: question, mode: stack ? `stack:${stack}` : "prefer-newest", results: rows.map(shape) };
}

// ponytail: in-memory per-IP limiter, resets per instance; move to a shared store if abuse shows up.
const hits = new Map();
function limited(ip) {
  const now = Date.now(), win = hits.get(ip) || [];
  const recent = win.filter(t => now - t < 60_000);
  recent.push(now); hits.set(ip, recent);
  return recent.length > 60;
}

// --- MCP (Streamable HTTP, stateless) --------------------------------------
const TOOL = {
  name: "search_library",
  description: "Semantic search over PulsePoint's RFI answer library. Returns prior approved answers " +
    "(question, answer, stack, date, tags, legal_approved, score) most similar to the question. Read-only.",
  inputSchema: { type: "object", properties: {
    question: { type: "string", description: "The client's question, as literally as possible." },
    topK: { type: "integer", minimum: 1, maximum: 20, default: 5 },
    stack: { type: "string", description: "Optional hard filter on stack_name." } }, required: ["question"] },
  annotations: { readOnlyHint: true },
};

async function mcp(msg) {
  const reply = (result) => ({ jsonrpc: "2.0", id: msg.id, result });
  const fail = (code, message) => ({ jsonrpc: "2.0", id: msg.id, error: { code, message } });
  switch (msg.method) {
    case "initialize": return reply({ protocolVersion: msg.params?.protocolVersion || "2025-06-18",
      capabilities: { tools: {} }, serverInfo: { name: "rfi-library", version: "1.0.0" } });
    case "ping": return reply({});
    case "tools/list": return reply({ tools: [TOOL] });
    case "tools/call": {
      if (msg.params?.name !== TOOL.name) return fail(-32602, "unknown tool");
      const a = msg.params.arguments || {};
      try {
        const out = await search(a.question, a.topK, a.stack);
        return reply({ content: [{ type: "text", text: JSON.stringify(out) }], structuredContent: out });
      } catch (e) {
        return reply({ content: [{ type: "text", text: e.message }], isError: true });
      }
    }
    default: return fail(-32601, "method not found");
  }
}

// --- HTTP -------------------------------------------------------------------
const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Content-Type, X-RFI-Token, Mcp-Session-Id, Accept, Mcp-Protocol-Version",
  "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS", "Access-Control-Expose-Headers": "Mcp-Session-Id" };
const send = (res, status, body, extra = {}) => {
  res.writeHead(status, { ...CORS, "Content-Type": "application/json", ...extra });
  res.end(body === undefined ? "" : JSON.stringify(body));
};
const readJson = req => new Promise((ok, no) => {
  let s = ""; req.on("data", c => { s += c; if (s.length > 1e6) no(Object.assign(new Error("body too large"), { status: 413 })); });
  req.on("end", () => { try { ok(s ? JSON.parse(s) : {}); } catch { no(Object.assign(new Error("invalid JSON"), { status: 400 })); } });
});

http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://x");
  const ip = (req.headers["x-forwarded-for"] || req.socket.remoteAddress || "").split(",")[0].trim();
  try {
    if (req.method === "OPTIONS") return send(res, 204);
    if (url.pathname === "/healthz") return send(res, 200, { ok: true, index: INDEX });
    if (limited(ip)) return send(res, 429, { error: "rate limited: 60 requests per minute" }, { "Retry-After": "60" });

    if (url.pathname === "/search") {
      if (req.method !== "POST") return send(res, 405, { error: "POST only" });
      if (req.headers["x-rfi-token"] !== TOKEN) return send(res, 401, { error: "bad token" });
      const b = await readJson(req);
      return send(res, 200, await search(b.question, b.topK, b.stack));
    }

    if (url.pathname === `/mcp/${TOKEN}`) {
      if (req.method === "GET") return send(res, 405, { error: "no server-initiated stream" });
      if (req.method === "DELETE") return send(res, 200);
      const b = await readJson(req);
      const msgs = Array.isArray(b) ? b : [b];
      const out = (await Promise.all(msgs.filter(m => m.id !== undefined).map(mcp)));
      if (!out.length) return send(res, 202);               // notifications only
      return send(res, 200, Array.isArray(b) ? out : out[0]);
    }
    return send(res, 404, { error: "not found" });
  } catch (e) {
    console.error(e);
    send(res, e.status || 502, { error: e.message });
  }
}).listen(process.env.PORT || 8080, () => console.log(`rfi-library listening on ${process.env.PORT || 8080} (index ${INDEX})`));

module.exports = { collapse, shape };
