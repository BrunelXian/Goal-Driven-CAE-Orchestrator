// Read one actual Desktop turn. The caller supplies independently selected project identities.
export async function verifyT02Turn(readThread, scope) {
  const {hostId, threadId, researchId, backendId, manifestSha256, installedRoot} = scope;
  const reply = await readThread({hostId, threadId, turnLimit: 1, includeOutputs: true, maxOutputCharsPerItem: 20000});
  const result = JSON.parse(reply.content[0].text);
  if (reply.isError || result.thread.id !== threadId || result.thread.hostId !== hostId) throw Error("HOST_IDENTITY");
  const commands = result.turns.at(-1).items.filter(i => i.type === "commandExecution" && i.exitCode === 0 && !i.output.truncated);
  const body = c => {
    const s = c.output.text.trim();
    try { return JSON.parse(s.slice(s.indexOf("{"), s.lastIndexOf("}") + 1)); } catch { return null; }
  };
  const events = commands.map(c => ({text: c.output.text, data: body(c)}));
  const find = (test, from = -1) => {
    const i = events.findIndex((e, j) => j > from && test(e));
    if (i < 0) throw Error("MISSING_ORDERED_TOOL_RECEIPT");
    return i;
  };
  const hex = v => typeof v === "string" && /^[0-9a-f]{64}$/.test(v);
  const install = find(e => e.data?.status === "PACKAGE_AND_CORE_VERIFIED" &&
    e.data.runtime.plugin === installedRoot && e.data.runtime.package_manifest_sha256 === manifestSha256);
  const proposal = find(e => e.data?.status === "READ_PROPOSAL" && e.data.expected_backend_id === backendId, install);
  const denial = find(e => e.data?.error === "T02_READ_CONSENT_REQUIRED" && /exit=2\b/.test(e.text), proposal);
  const consent = find(e => e.data?.status === "REGISTERED_READ_BACK" && e.data.project === researchId, denial);
  const captured = find(e => e.data?.observation?.research_project === researchId &&
    e.data.observation.backend_project === backendId && e.data.status === "REGISTERED_READ_BACK" && /exit=0\b/.test(e.text), consent);
  const cap = events[captured].data;
  const replay = find(e => e.data?.status === "REPLAYED" && e.data.artifact.sha256 === cap.artifact.sha256 &&
    e.data.receipt.digest === cap.receipt.digest && e.data.receipt.revision === cap.receipt.revision, captured);
  const reopened = find(e => e.data?.project === researchId && e.data.revision === cap.receipt.revision &&
    e.data.execution_authorized === false && e.data.tasks?.some(t => t.task_id === "T02" &&
    t.execution === "SUBMITTED" && t.authorization === "NOT_GRANTED" && t.verification === "NOT_VERIFIED" &&
    t.scientific_decision === "NOT_ASSESSED" && t.evidence.some(ref => ref.sha256 === cap.artifact.sha256)), replay);
  const o = cap.observation;
  if (o.execution_authorized !== false || o.server !== "AbqJobPilot" || o.version !== "0.2.2" ||
    o.task_id !== "T02" || cap.receipt.project !== researchId || cap.receipt.execution_authorized !== false ||
    !hex(cap.artifact.sha256) || !hex(cap.receipt.digest) ||
    !["queue", "history", "status"].every(key => hex(o.response_sha256[key]))) throw Error("INVALID_MCP_RECEIPT");
  return {status: "PASS", server: o.version, protocol: o.protocol, rows: o.rows_returned,
    observed_state: o.queue_status.status, active_confirmed: o.queue_status.active_execution_confirmed,
    artifact_sha256: cap.artifact.sha256, receipt_sha256: cap.receipt.digest, recovered_revision: events[reopened].data.revision,
    execution_authorized: false};
}
