from pathlib import Path
import zipfile
from .roles import BY_ROLE
from .files import safe_file

TEMPLATES={
'developer':('developer_report.md','Developer analysis and implementation checklist.'),
'tester':('qa_report.md','QA test report and regression checklist.'),
'ui_ux':('ui_ux_spec.md','Responsive UI/UX specification and component plan.'),
'database':('database_design.md','Database entities, relationships, indexes and integrity plan.'),
'devops':('deployment_plan.md','Render/Docker deployment and rollback plan.'),
'security':('security_report.md','OWASP-oriented security review and remediation checklist.'),
'ml_engineer':('ml_plan.md','Dataset, baseline model, evaluation and inference plan.'),
'data_entry':('records_report.md','Data-entry validation and import report.'),
'hr':('hr_workflow.md','Candidate screening and interview workflow.'),
'email':('email_draft.txt','Draft prepared. External sending requires approval.'),
'documentation':('README_generated.md','Generated technical documentation.'),
'project_manager':('project_plan.md','Milestones, owners, dependencies and progress plan.'),
'product_manager':('product_requirements.md','User stories, backlog priorities and acceptance criteria.'),
'code_reviewer':('code_review.md','Readability, architecture, error handling and maintainability review.'),
'researcher':('research_report.md','Research plan and findings structure.'),
'data_analyst':('data_analysis.md','KPI and trend analysis plan.'),
'sales':('sales_plan.md','Lead qualification, proposal and follow-up workflow.'),
'marketing':('marketing_plan.md','Audience, messaging, channel and campaign measurement plan.'),
'support':('support_resolution.md','Issue reproduction, severity and resolution workflow.'),
'finance':('finance_report.md','Budget, expense and anomaly review.'),
'compliance':('compliance_report.md','Privacy, policy and regulatory checklist.'),
'operations':('operations_plan.md','Workflow, bottleneck, SLA and coordination plan.'),
'automation':('automation_plan.md','Safe automation workflow with approval gates.'),
}

def inspect_attachments(paths):
    sections=[]
    for p in paths or []:
        p=Path(p)
        try:
            ext=p.suffix.lower()
            if ext in {'.txt','.md','.json','.csv','.py','.js','.jsx','.ts','.tsx','.html','.css','.sql'}:
                content=p.read_text(encoding='utf-8',errors='ignore')[:12000]
                sections.append(f'### {p.name}\n```\n{content}\n```')
            elif ext=='.zip':
                with zipfile.ZipFile(p) as z:
                    names=z.namelist()[:120]
                sections.append(f'### {p.name} (ZIP contents)\n'+'\n'.join(f'- {n}' for n in names))
            else:
                sections.append(f'### {p.name}\nBinary attachment, {p.stat().st_size} bytes.')
        except Exception as e:
            sections.append(f'### {p.name}\nCould not inspect: {e}')
    return '\n\n'.join(sections)

def execute(task, attachment_paths=None):
    role=task.assigned_role
    meta=BY_ROLE.get(role,BY_ROLE['manager'])
    fname,summary=TEMPLATES.get(role,('manager_notes.md','Manager coordinated the work.'))
    rel=f'outputs/task_{task.id}/{fname}'
    p=safe_file('demo-company',rel)
    p.parent.mkdir(parents=True,exist_ok=True)
    evidence=inspect_attachments(attachment_paths)
    content=(
        f'# {meta["name"]} — {meta["title"]}\n\n'
        f'## Task\n{task.title}\n\n'
        f'## Requirement\n{task.description}\n\n'
    )
    if evidence:
        content += f'## Attached files inspected\n{evidence}\n\n'
    if role=='developer':
        content += ('## Developer result\n'
                    '- Requirement parsed.\n'
                    '- Uploaded source/project structure inspected where readable.\n'
                    '- Implementation checklist prepared.\n'
                    '- This build does not falsely claim source-code edits unless a real code-generation/runtime provider is connected.\n')
    elif role=='tester':
        content += ('## QA result\n'
                    '- Attached build/files inspected.\n'
                    '- Happy path, validation, API failure, auth, regression and responsive checks prepared.\n'
                    '- True executable tests require a runnable project/runtime.\n')
    else:
        content += f'## Result\n{summary}\n'
    p.write_text(content,encoding='utf-8')
    approval=role in {'email'} or ('call' in task.description.lower()) or ('send' in task.description.lower() and role in {'hr','sales','marketing'})
    return rel,summary,approval
