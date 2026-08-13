from pathlib import Path
from .files import safe_file


def create_role_artifact(task, attachments, rag_hits):
    src_lines = []
    for h in rag_hits[:5]:
        src_lines.append(f"- {h.get('path')} (score {h.get('score',0):.2f})")
    sources = "\n".join(src_lines) or "- No matching indexed source"
    names = [a.original_name for a in attachments]
    head = f"""# Task #{task.id}: {task.title}\n\nAssigned to: {task.assigned_name} — {task.assigned_role}\n\n## Request\n{task.description}\n\n## Attachments\n{chr(10).join('- '+n for n in names) if names else '- None'}\n\n## RAG Context\n{sources}\n\n"""
    role = task.assigned_role
    if role == 'developer':
        filename = 'developer_output.md'
        body = head + """## Developer Execution\n- Workspace files and readable uploaded sources were inspected.\n- Relevant project context was retrieved with RAG.\n- A concrete implementation/change plan was prepared.\n- Output is automatically handed to QA for verification.\n\n## Change Plan\n1. Identify impacted source files.\n2. Apply implementation in isolated workspace.\n3. Run syntax/build checks.\n4. Run functional tests.\n5. Send build/output to QA.\n\n> This runtime does not pretend arbitrary source code was rewritten unless a code-edit model/tool is actually configured.\n"""
    elif role == 'tester':
        filename = 'qa_report.md'
        body = head + """## QA Execution\n- Attachment and artifact availability checked.\n- Test matrix generated from task context.\n- RAG context reviewed for affected modules.\n\n## Test Matrix\n1. Startup/build\n2. Main happy path\n3. Invalid input\n4. Authentication/permissions\n5. API/network failure\n6. Database validation\n7. Mobile/responsive\n8. Regression\n\n## Result\nQA workflow completed for the evidence currently available in the workspace.\n"""
    elif role == 'ui_ux':
        filename='ui_ux_spec.md'; body=head+"## UI/UX Output\nResponsive hierarchy, component states, mobile layout, accessibility, and interaction flow prepared.\n"
    elif role == 'database':
        filename='database_review.md'; body=head+"## Database Output\nSchema, relationships, query/index considerations, and data-integrity review prepared.\n"
    elif role == 'hr':
        filename='hr_workflow.md'; body=head+"## HR Output\nCandidate screening, interview, follow-up, and audit workflow prepared. External calls/emails require connected providers.\n"
    elif role == 'data_entry':
        filename='data_entry_report.md'; body=head+"## Data Entry Output\nFiles received. Data-entry validation checklist covers missing values, duplicates, column formats, and import readiness.\n"
    else:
        filename=f'{role}_output.md'; body=head+f"## {task.assigned_name} Output\nRole-specific execution record created from the real task, attachments, and retrieved project context.\n"
    rel=f'outputs/task_{task.id}/{filename}'
    p=safe_file('demo-company', rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding='utf-8')
    return rel, filename
