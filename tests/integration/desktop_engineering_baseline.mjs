// Invoke on A with the Desktop tools in the current session. Return only aggregate evidence.
export async function verifyDesktop(call, target) {
  const { hostId, projectId, threadId } = target;
  const invoke = async (name, args) => {
    const result = await call(name, args);
    if (result.isError) throw new Error("DESKTOP_READ_FAILED");
    return JSON.parse(result.content[0].text);
  };
  const ensure = (value, code) => { if (!value) throw new Error(code); };
  const projects = await invoke("list_projects", {});
  ensure(projects.projects.some(p => p.projectId === projectId && p.hostId === hostId), "PROJECT_NOT_LISTED");
  const listed = await invoke("list_threads", { limit: 50 });
  let active = [...listed.threads, ...listed.pinnedThreads].find(t => t.id === threadId);
  if (!active) {
    let cursor;
    do {
      const page = await invoke("list_threads", {hostId, mode:"history", limit:50, ...(cursor ? {cursor} : {})});
      active = page.threads.find(t => t.id === threadId);
      cursor = page.nextCursor;
    } while (!active && cursor);
  }
  ensure(active?.hostId === hostId && active?.projectId === projectId, "MAIN_NOT_IN_PROJECT");
  const thread = await invoke("read_thread", { hostId, threadId, turnLimit: 8,
    includeOutputs: true, maxOutputCharsPerItem: 14000 });
  ensure(thread.thread.id === threadId && thread.thread.hostId === hostId, "THREAD_READBACK_MISMATCH");
  const items = thread.turns.flatMap(t => t.items);
  let cursor = thread.page.nextCursor;
  while (cursor) {
    const older = await invoke("read_thread", {hostId, threadId, cursor, turnLimit:8,
      includeOutputs:true, maxOutputCharsPerItem:14000});
    ensure(older.thread.id === threadId && older.thread.hostId === hostId, "THREAD_READBACK_MISMATCH");
    items.push(...older.turns.flatMap(t => t.items));
    cursor = older.page.nextCursor;
  }
  const records = [];
  for (const item of items) {
    if (item.type !== "commandExecution" || item.status !== "completed" || item.exitCode !== 0 ||
        !item.output?.text || item.output.truncated) continue;
    const out = item.output.text;
    // A successful PowerShell invocation can print path/hash headers before the JSON result.
    try { records.push(JSON.parse(out.slice(out.indexOf("{"), out.lastIndexOf("}") + 1))); }
    catch { /* No complete structured result in this item. */ }
  }
  ensure(records.some(r => r.schema === "gdcae-main-handoff-v1" && r.state === "VERIFIED" &&
    r.project_id === projectId && r.host_id === hostId && r.thread_id === threadId &&
    r.title === active.title && r.may_create === false), "VERIFIED_MAIN_RECEIPT_MISSING");
  const created = records.find(r => r.schema_version === 3 && r.research_project_id && r.project_revision === 1);
  ensure(created, "PROJECT_CREATION_RECEIPT_MISSING");
  const registered = records.find(r => r.project === created.research_project_id && r.status === "REGISTERED_READ_BACK" &&
    r.execution_authorized === false && /^[0-9a-f]{64}$/.test(r.digest));
  ensure(registered, "TASK_REGISTRATION_MISSING");
  const views = records.filter(r => r.project === registered.project && r.revision === registered.revision &&
    r.execution_authorized === false && Array.isArray(r.tasks) &&
    ["T01", "T02"].every(id => r.tasks.some(t => t.task_id === id && t.project === r.project)));
  ensure(views.length >= 2 && views.some((v, i) => views.slice(i + 1).some(w =>
    JSON.stringify(v.tasks) === JSON.stringify(w.tasks))), "MATCHING_TASK_READBACK_MISSING");
  const children = [...new Set(items.filter(i => i.type === "subAgentActivity" && i.kind === "completed")
    .map(i => i.agentThreadId).filter(Boolean))];
  ensure(children.length, "NATIVE_RETURN_MISSING");
  let childrenWithCommands = 0;
  for (const id of children) {
    const child = await invoke("read_thread", {hostId, threadId: id, turnLimit: 4, includeOutputs: false});
    if (child.thread.id === id && child.thread.hostId === hostId &&
        child.turns.some(t => t.items.some(i => i.type === "commandExecution" && i.exitCode === 0))) childrenWithCommands++;
  }
  ensure(childrenWithCommands === children.length, "CHILD_EXECUTION_UNVERIFIED");
  return { main_receipt: "VERIFIED", project_schema: 3, registration_revision: registered.revision,
    repeated_task_views: views.length, completed_children: children.length, children_with_command_receipts: childrenWithCommands,
    job_authorization: false };
}
