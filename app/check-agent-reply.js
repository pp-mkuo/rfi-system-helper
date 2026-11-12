// Self-check for the helper page's agent-reply parsing: node app/check-agent-reply.js
const s = require("fs").readFileSync(require("path").join(__dirname, "rfi-system-helper.html"), "utf8");
const js = s.slice(s.indexOf("<script>\n") + 9, s.lastIndexOf("</script>"));
new Function(js); // page script parses
const grab = n => { const a = js.indexOf("function " + n); let d = 0, i = js.indexOf("{", a); for (;; i++) { if (js[i] == "{") d++; if (js[i] == "}" && !--d) break; } return js.slice(a, i + 1); };
const uid = () => Math.random().toString(36).slice(2), dbRow = () => {};
const state = { rows: ["1", "2", "3", "4"].map(n => ({ id: n, n, question: "q" + n, flags: [], sources: [] })) };
eval(grab("parseReply") + grab("applyAgent"));
const msgs = ["Triage: Q1 green [ok]", "```json\n" + JSON.stringify([
  { n: "1a", question: "part a", lane: "GREEN", route: "CS — answered", draft: "Yes.", sources: [{ score: 0.77, used: true }] },
  { n: "1b", question: "part b", lane: "RED", route: "Route out: Security/privacy team" },
  { n: "2", lane: "AMBER", route: "SME: TPM (owner unconfirmed)" },
  { n: "3", lane: "AMBER", route: "SME needed — no owner on file (supply path)" }]) + "\n```"];
applyAgent(state.rows.slice(), msgs.slice().reverse().map(parseReply).find(Boolean));
const r = state.rows;
const assert = (c, m) => { if (!c) { console.error("FAIL: " + m); process.exit(1); } };
assert(r.length === 5, "split question becomes two rows");
assert(r[0].n === "1a" && r[0].status === "drafted", "green part drafted");
assert(r[1].route === "Route out: Security/privacy team", "red route prefix not doubled");
assert(r[2].flags.includes("owner unconfirmed") && r[3].flags.includes("no owner on file"), "routing gap flags");
assert(r[4].status === "failed", "question missing from reply fails");
assert(parseReply("no json here") === null, "prose is not a reply");
console.log("ok");
