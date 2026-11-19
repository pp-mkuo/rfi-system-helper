// Self-check for the helper page's agent-reply parsing: node app/check-agent-reply.js
const s = require("fs").readFileSync(require("path").join(__dirname, "rfi-system-helper.html"), "utf8");
const js = s.slice(s.indexOf("<script>\n") + 9, s.lastIndexOf("</script>"));
new Function(js); // page script parses
const grab = n => { const a = js.indexOf("function " + n); let d = 0, i = js.indexOf("{", a); for (;; i++) { if (js[i] == "{") d++; if (js[i] == "}" && !--d) break; } return js.slice(a, i + 1); };
const uid = () => Math.random().toString(36).slice(2), dbRow = () => {};
const rows4 = () => ["1", "2", "3", "4"].map(n => ({ id: n, n, question: "q" + n, flags: [], sources: [] }));
const state = { rows: rows4() };
eval(grab("replyRows") + grab("parseReply") + grab("applyAgent"));
const assert = (c, m) => { if (!c) { console.error("FAIL: " + m); process.exit(1); } };

// Old shape: one array at the end, with a prose line before it.
const msgs = ["Triage: Q1 green [ok]", "```json\n" + JSON.stringify([
  { n: "1a", question: "part a", lane: "GREEN", route: "CS — answered", draft: "Yes.", sources: [{ score: 0.77, used: true }] },
  { n: "1b", question: "part b", lane: "RED", route: "Route out: Security/privacy team" },
  { n: "2", lane: "AMBER", route: "SME: TPM (owner unconfirmed)" },
  { n: "3", lane: "AMBER", route: "SME needed — no owner on file (supply path)" }]) + "\n```"];
applyAgent(state.rows.slice(), replyRows(msgs));
let r = state.rows;
assert(r.length === 5, "split question becomes two rows");
assert(r[0].n === "1a" && r[0].status === "drafted", "green part drafted");
assert(r[1].route === "Route out: Security/privacy team", "red route prefix not doubled");
assert(r[2].flags.includes("owner unconfirmed") && r[3].flags.includes("no owner on file"), "routing gap flags");
assert(r[4].status === "failed", "question missing from reply fails");
assert(parseReply("no json here") === null && parseReply("Triage: Q1 green [ok]") === null, "prose is not a reply");

// New shape (AF-126): one object per message, stopped after #2 — #1 and #2 are kept, #3 and #4 are marked stopped.
state.rows = rows4();
const partial = [JSON.stringify({ n: "1", lane: "RED", route: "Route out: Legal", sources: [] }), "Working on 2…",
  "```json\n" + JSON.stringify({ n: "2", lane: "GREEN", draft: "We do.", sources: [{ id: "a", score: 0.6, used: true }], flags: ["x"] }) + "\n```"];
assert(replyRows(partial).length === 2, "one object per message is collected");
applyAgent(state.rows.slice(), replyRows(partial), "stopped before rfi-agent finished it");
r = state.rows;
assert(r[0].status === "routed" && r[1].status === "drafted", "finished questions kept on stop");
assert(r[2].status === "failed" && r[3].error === "stopped before rfi-agent finished it", "unfinished questions marked stopped");
// Seen from rfi-agent on 2026-11-19: all objects in one message, a blank line between them.
assert(replyRows(["Both are green. Searching.", '{"n":"5","lane":"GREEN","draft":"a\\nb","flags":["x"]}\n\n{"n":"6","lane":"AMBER"}']).length === 2, "objects on separate lines in one message are collected");
console.log("ok");
