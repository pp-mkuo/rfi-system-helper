// Smallest check that fails if the dedupe or response shape breaks. Run: node test.js
process.env.PINECONE_API_KEY ||= "test"; process.env.RFI_TOKEN ||= "test"; process.env.PORT = "0";
const assert = require("assert");
const { collapse, shape } = require("./server.js");

const rows = [
  { _id: "a", _score: 0.9, question: "What is X?", stack_name: "Client Strategy", last_updated_date: "2024-01-01" },
  { _id: "b", _score: 0.8, question: "what is  x?", stack_name: "Client Strategy- Cleaned", last_updated_date: "2025-10-07" },
  { _id: "c", _score: 0.7, question: "What is Y?", stack_name: "RFI 2026", last_updated_date: "2026-08-20", tags: ["Data"], legal_approved: true },
];
const out = collapse(rows, 5);
assert.deepStrictEqual(out.map(r => r._id), ["b", "c"], "newest wins per question, sorted by score");
assert.deepStrictEqual(Object.keys(shape(out[1])), ["id", "score", "stack", "updated", "source", "tags", "legal_approved", "question", "answer"]);
assert.strictEqual(shape(out[1]).updated, "2026-08-20");
console.log("ok");
process.exit(0);
