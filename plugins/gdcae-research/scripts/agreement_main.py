"""Single Main's installed text views and explicit research-only actions."""
import json
import sys
from pathlib import Path

def load_core(plugin):
    # Called only after the manifest, launcher, driver, runtime and archive checks.
    archive = str(plugin / "runtime/agreement-core.zip")
    if archive not in sys.path:
        sys.path.insert(0, archive)

def markdown(view, mode):
    def show(value):
        if isinstance(value, list):
            return "、".join(show(v) for v in value) or "（无条目）"
        if isinstance(value, dict):
            return "，".join(f"{k}={show(v)}" for k,v in value.items())
        if value is None:
            return "（无）"
        text = str(value).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        for char in ("\\","`","*","_","[","]","|","#"):
            text = text.replace(char,"\\"+char)
        return text
    v = view["version"]
    lines = [f"科研约定 · {view['project']} · {('v'+str(v)) if v else '尚无生效版本'} · {view['status']}",
             f"关键 UNKNOWN · {show(view['unknowns'])}",
             "使用 overview 查看当前约定，使用 detail 查询全文与证据。"]
    if mode=="hint":
        return "\n".join(lines)
    lines.append(f"本记录 {view['agreement']}，当前生效记录 {view['current']}。科研确认不授予求解权限。")
    for heading, fields in view.get("sections",{}).items():
        lines.extend(["","### "+heading])
        lines.extend(f"- {k} · {show(value)}" for k,value in fields.items())
    if mode=="diff":
        lines.extend(["","### 修订差异",f"父版本 · {view['base']}",f"理由 · {show(view['reason'])}",
                      f"影响 · {show(view['impact'])}"])
        for k,change in view["changes"].items():
            lines.append(f"- {k} · {show(change['old'])} → {show(change['new'])}")
    if "record" in view:
        rec=view["record"]
        lines.extend(["","### 版本与证据",f"父版本 · {rec['base']}", f"拟定资格 · {rec['standing']}",
                      f"科研确认所在项目修订 · {view['confirmation_revision']}",
                      f"修订理由 · {show(rec['reason'])}", f"影响 · {show(rec['impact'])}"])
        lines.extend(f"- {k} · {v}" for k,v in rec["refs"].items())
        lines.extend(f"- {k} · {show(v)}" for k,v in view["attributions"].items())
    return "\n".join(lines)

def query(root,mode="hint",selector=None):
    from aegiscae.research import project, research_agreement
    result=research_agreement.view(project.open_agreement_project(root),mode,selector)
    return {**result, "markdown":markdown(result,mode)}

def run(args,plugin,checked):
    from aegiscae.research import project, research_agreement
    from aegiscae.contracts.research_contracts import strict_json, ContractBundle, require
    root=checked(args.project_root)
    require(not root.is_relative_to(plugin), "PROJECT_OUTSIDE_INSTALLATION_REQUIRED")
    op=args.operation
    read=op in ("overview","detail","diff","hint")
    require(not args.output and not args.agreement_root and (not args.selector or op in ("detail","diff"))
            and ((read and not args.input_file) or (not read and args.input_file)), "INVALID_AGREEMENT_ARGUMENTS")
    if read:
        return query(root,op,args.selector)
    path=checked(args.input_file)
    require(path.is_file() and path.stat().st_size<=65536,"INPUT_LIMIT")
    body=strict_json(path.read_bytes())
    if op=="new":
        require(set(body)=={"name","schema"} and body["schema"]=="research-agreement-project-v3","EXPLICIT_OPT_IN_REQUIRED")
        created=project.create_research_project(root,body["name"],research_agreements=True)
        return {**created.inspect(),"current_hint":query(root)}
    handle=project.open_agreement_project(root,write=True)
    if op=="freeze":
        require(set(body)=={"bundle","expected_revision","key"},"INVALID_FREEZE_REQUEST")
        bundle=ContractBundle.from_dict(body["bundle"])
        result=handle.freeze_contract_bundle(bundle,body["expected_revision"],body["key"])
        return {**result,"refs":bundle.digests(),"execution_authorized":False,"current_hint":query(root)}
    require(op in ("propose","confirm","attribute") and body.get("op")==op,"INVALID_AGREEMENT_OPERATION")
    result=research_agreement.record_change(handle,body)
    return {**result,"current_hint":query(root)}
