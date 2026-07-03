"""Generate the daily utilization HTML (Mar 02 – Jun 18 2026).

Mon–Fri working days, excluding 5 general holidays. First 54 days = SmartRecruitz;
last 20 days = a mix of SmartRecruitz + Interview SaaS.
"""
from datetime import date, timedelta

HOLIDAYS = {
    date(2026, 3, 3): "Holi",
    date(2026, 3, 19): "Ugadi",
    date(2026, 3, 27): "Sri Rama Navami",
    date(2026, 4, 3): "Good Friday",
    date(2026, 5, 1): "Workers' Day",
}
START, END = date(2026, 3, 2), date(2026, 6, 19)

# (project, task) for each working day, in order. project: SR | IS | BOTH
TASKS = [
    # ── March: foundation (SmartRecruitz) ──
    ("SR", "Project kick-off; went through the requirements and mapped the candidate verification flow end to end"),
    ("SR", "Finalised the architecture: async FastAPI backend, Next.js frontend, PostgreSQL, with the AI work split into separate single-purpose agents"),
    ("SR", "Designed the Postgres schema: a staging table for raw parsed data and a main table for verified candidates, plus interviews, verifications and a skill taxonomy"),
    ("SR", "Set up the repo, the Python virtualenv, Alembic and the local Postgres, and the base service structure"),
    ("SR", "Built the FastAPI application factory, the pydantic settings layer and the async SQLAlchemy engine and session"),
    ("SR", "Added the SQLAlchemy models for candidates_staging and candidates_main with UUID primary keys and JSONB columns for the parsed profile and analysis"),
    ("SR", "Added the interview, interview_question and verification models with their foreign keys back to the candidate"),
    ("SR", "Added the skill_taxonomy, uploaded_document and background_task models"),
    ("SR", "Set up Alembic and wrote the initial migration, including the pg_trgm extension for fuzzy name search"),
    ("SR", "Built the candidate repository: create and fetch staging, and the staging to main promotion logic"),
    ("SR", "Built the candidate registration endpoint and service that creates the staging row and generates the candidate ref"),
    ("SR", "Set up the async background-task handling with a tasks table that the frontend polls for status"),
    ("SR", "Wired up the OpenAI client wrapper and the base agent structure with the prompt files"),
    ("SR", "Scaffolded the Next.js app-router frontend and the routing"),
    ("SR", "Added the shared shadcn UI components and the ky-based API client"),
    ("SR", "Built the onboarding chat shell and the Zustand stores for the chat and onboarding state"),
    ("SR", "Worked on the Agent 1 resume-parsing prompt to extract structured fields"),
    # ── April: AI agent pipeline ──
    ("SR", "Got Agent 1 parsing resumes into a structured profile with skills, experience and education"),
    ("SR", "Added vision parsing so scanned and image PDFs go through the vision model instead of plain text extraction"),
    ("SR", "Normalised the parsed skills against the skill taxonomy so search and matching stay consistent"),
    ("SR", "Added the resume scoring with sub-scores and the analytics it pulls out"),
    ("SR", "Wrote the Agent 1 background handler that saves the parsed profile and analysis onto the staging row"),
    ("SR", "Built the resume-review card so the candidate confirms the parsed profile before continuing"),
    ("SR", "Started Agent 2 (duplicate detection) using a pg_trgm fuzzy match on name plus email and phone to shortlist candidates"),
    ("SR", "Finished Agent 2 with the LLM comparison over the shortlist, returning unique, duplicate or uncertain"),
    ("SR", "Added the promotion from staging into the main talent pool once a candidate clears the duplicate check"),
    ("SR", "Started Agent 3 (ID verification), sending the document image through the vision model"),
    ("SR", "Handled Aadhaar, PAN and Passport with the mandatory-document ordering"),
    ("SR", "Added the name and DOB match against the claimed details and the document authenticity confidence"),
    ("SR", "Built the verification records and the per-document status flow"),
    ("SR", "Built the ID upload widget with the step-by-step mandatory-document prompts"),
    ("SR", "Worked on the Agent 4 prompt to generate interview questions from the candidate profile"),
    ("SR", "Got Agent 4 generating questions targeted at the candidate's actual skills with expected-answer points"),
    ("SR", "Worked on the Agent 5 scoring prompt and the evaluation rubric"),
    ("SR", "Finished Agent 5 scoring the transcript into an overall score, the L1 pass/fail and a recommendation"),
    ("SR", "Wired the interview question and answer loop into the chatbot"),
    ("SR", "Built the interview recording and transcription UI with the video widget"),
    ("SR", "Added the scoring task polling and cached the result on the candidate so it loads instantly"),
    ("SR", "Showed the readiness score, L1 status and recommendation on the result screen"),
    ("SR", "Added the re-interview controls so an admin can grant another attempt"),
    # ── May (early): chatbot, then the client requirement set (received 08 May) ──
    ("SR", "Reworked the onboarding chatbot into a proper state machine, one step at a time"),                     # 41 Mon 04 May
    ("SR", "Made the chatbot sessions resumable by persisting the onboarding state to localStorage"),             # 42 Tue 05 May
    ("SR", "Added the email lookup and restore so returning candidates pick up exactly where they left off"),     # 43 Wed 06 May
    ("SR", "Cleaned up the typed chat message rendering and the flow handling"),                                  # 44 Thu 07 May
    ("SR", "Got the new requirement set from the client, went through it and planned the changes"),               # 45 Fri 08 May
    ("SR", "Added the candidate fields they asked for (current CTC, expected CTC, notice period, working status) with the migration"),  # 46 Mon 11 May
    ("SR", "Added current and preferred location, and made Aadhaar and PAN mandatory in the ID verification step"),  # 47 Tue 12 May
    ("SR", "Added the resume score and the general analytics from the resume (tenure, employment gaps, company-type mix)"),  # 48 Wed 13 May
    ("SR", "Captured the Git and LinkedIn URLs and added the LinkedIn vs resume cross check via the Coresignal lookup"),  # 49 Thu 14 May
    ("SR", "Added the service vs product company classification, the value-addition check, certifications and the resume pros and cons"),  # 50 Fri 15 May
    ("SR", "Stored the interview video link and the full interview context, and made sure everything persists to the DB"),  # 51 Mon 18 May
    ("SR", "Added LMS course recommendations for profiles that come from the LMS, and set up Zoho for project tracking"),  # 52 Tue 19 May
    ("SR", "Built the hiring manager dashboard with the pool stats, domain breakdown and recent candidates"),     # 53 Wed 20 May
    ("SR", "Built the JD search with the weighted mandatory/preferred skill-match ranking and the candidate detail page"),  # 54 Thu 21 May
    # ── Last working days (22 May – 19 Jun): MIX of SmartRecruitz + Interview SaaS ──
    ("SR", "Wrapped up the candidate data-model changes and ran the migrations"),  # 55 Fri 22 May
    ("IS", "Set up the HeyGen LiveAvatar account and got the streaming API key"),  # 56 Mon 25 May
    ("IS", "Did a basic LiveAvatar demo, got the avatar WebRTC stream rendering in the browser"),      # 57 Tue 26 May
    ("SR", "Tidied up the hiring manager search, added pagination and the filters"),                 # 58 Wed 27 May
    ("IS", "Got the avatar to speak by sending text through the LiveAvatar session repeat call"),      # 59 Thu 28 May
    ("IS", "Fixed the avatar going silent; it was calling repeat before the session reached the connected state, so I fixed the event timing"),  # 60 Fri 29 May
    ("IS", "Hooked up Deepgram nova-2 streaming speech to text over a websocket for the candidate audio"),  # 61 Mon 01 Jun
    ("IS", "Got the realtime transcript working with the avatar, handling the interim and final results"),  # 62 Tue 02 Jun
    ("IS", "Wired the basic question and follow-up loop, sending the transcript to the model and the reply back to the avatar"),  # 63 Wed 03 Jun
    ("SR", "Got LMS access from the team and went through how SmartRecruitz would plug into it"),     # 64 Thu 04 Jun
    ("SR", "Started the LMS integration: built the recruitment module and the candidate to LMS-user mapping table"),  # 65 Fri 05 Jun
    ("SR", "Wired the approval flow and the short-lived token handoff between the LMS and SmartRecruitz"),  # 66 Mon 08 Jun
    ("SR", "Started merging the SmartRecruitz database into the LMS Postgres database"),              # 67 Tue 09 Jun
    ("SR", "Moved the tables into the LMS application schema with the lms_recruit_ prefix and matched their naming conventions"),  # 68 Wed 10 Jun
    ("SR", "Pointed the FastAPI backend at the shared LMS database, updated the models, FKs and the Alembic version schema, and verified it still worked"),  # 69 Thu 11 Jun
    ("SR", "Wired the location filter into the hiring manager search, matching current or preferred location"),  # 70 Fri 12 Jun
    ("SR", "Started the standalone auth: argon2 password hashing and HS256 JWTs, and set up the Google sign in"),  # 71 Mon 15 Jun
    ("SR", "Finished the auth: the hiring manager login, the get_current_user dependency and the route guards"),  # 72 Tue 16 Jun
    ("IS", "Tested the LiveAvatar interview demo end to end"),                           # 73 Wed 17 Jun
    ("BOTH", "Stabilised both apps, sorted the env config and the run scripts, and wrote up the docs"),  # 74 Thu 18 Jun
    ("SR", "Added the Google sign in for both candidates and hiring managers, with the intent-based OAuth callback assigning the role"),  # 75 Fri 19 Jun
]

# Build working-day list
days = []
d = START
while d <= END:
    if d.weekday() < 5 and d not in HOLIDAYS:
        days.append(d)
    d += timedelta(days=1)
assert len(days) == len(TASKS), f"{len(days)} days vs {len(TASKS)} tasks"

PROJ = {
    "SR": ("SmartRecruitz", "#0f766e", "#ecfdf5"),
    "IS": ("Interview SaaS", "#6d28d9", "#f5f3ff"),
    "BOTH": ("SmartRecruitz · Interview SaaS", "#475569", "#f1f5f9"),
}
n_sr = sum(1 for p, _ in TASKS if p in ("SR", "BOTH"))
n_is = sum(1 for p, _ in TASKS if p in ("IS", "BOTH"))

# Group by month, preserving order.
by_month = []
for i, (dt, (proj, task)) in enumerate(zip(days, TASKS), 1):
    m = dt.strftime("%B %Y")
    if not by_month or by_month[-1][0] != m:
        by_month.append((m, []))
    by_month[-1][1].append((i, dt, proj, task))

THEAD = ('<thead><tr><th style="width:5%">#</th><th style="width:15%">Date</th>'
         '<th>Work performed</th></tr></thead>')


def render_table(groups, extra_cls=""):
    body = []
    for m, items in groups:
        body.append(f'<tr class="mh"><td colspan="3">{m}</td></tr>')
        for i, dt, proj, task in items:
            cls = "is" if proj in ("IS", "BOTH") else ""
            label = 'Interview as a Service: ' if proj == "IS" else ''
            body.append(
                f'<tr class="{cls}"><td class="d">{i}</td>'
                f'<td class="dt">{dt:%a, %d %b}</td><td>{label}{task}</td></tr>'
            )
    return (f'<table class="log {extra_cls}">{THEAD}<tbody>'
            + "\n".join(body) + "</tbody></table>")


# 2 months per page: March+April, then May+June on a new page.
table1 = render_table(by_month[:2])
table2 = render_table(by_month[2:], extra_cls="pgbreak")

HTML = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Resource Utilization Report</title>
<style>
  @page {{ size: A4; margin: 11mm 14mm 11mm 14mm;
    @bottom-left {{ content: "Resource Utilization (Daily) · Mar–Jun 2026"; font-size: 8pt; color:#9aa3af; }}
    @bottom-right {{ content: "Page " counter(page) " of " counter(pages); font-size: 8pt; color:#9aa3af; }} }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; color:#1f2733; font-size:9.5pt; margin:0; }}
  h1 {{ font-size:18pt; font-weight:700; color:#0f766e; margin:0 0 2px; letter-spacing:-0.3px; }}
  .subtitle {{ color:#6b7280; font-size:10pt; margin:0 0 12px; }}
  h2 {{ font-size:12pt; font-weight:700; margin:18px 0 6px; color:#111827; page-break-after:avoid; }}
  .meta {{ width:100%; border-collapse:collapse; font-size:9.5pt; margin-bottom:4px; }}
  .meta td {{ padding:2.5px 0; border:none; }} .meta td:first-child {{ color:#6b7280; width:120px; font-weight:600; }}
  .kpi {{ display:flex; gap:8px; margin:10px 0; }}
  .kpi div {{ flex:1; background:#f0fdfa; border:1px solid #ccfbf1; border-radius:8px; padding:8px 10px; }}
  .kpi .n {{ font-size:15pt; font-weight:700; color:#0f766e; }} .kpi .l {{ font-size:7.4pt; color:#6b7280; text-transform:uppercase; letter-spacing:.3px; }}
  table.log {{ width:100%; border-collapse:collapse; font-size:8pt; }}
  table.log thead th {{ text-align:left; background:#0f766e; color:#fff; font-size:7pt; text-transform:uppercase; letter-spacing:.3px; padding:4px 7px; }}
  table.log thead {{ display:table-header-group; }}
  table.log td {{ padding:5px 7px; border-bottom:1px solid #eef0f3; vertical-align:top; }}
  table.log tr {{ page-break-inside:avoid; }}
  td.d {{ color:#9aa3af; width:5%; }} td.dt {{ width:14%; white-space:nowrap; font-weight:600; color:#334155; }}
  tr.mh td {{ background:#f1f5f9; font-weight:700; color:#0f766e; font-size:8pt; letter-spacing:.3px; padding:5px 7px; }}
  table.pgbreak {{ break-before: page; }}
  .box {{ background:#f9fafb; border:1px solid #e5e7eb; border-radius:8px; padding:10px 12px; margin:8px 0; font-size:9pt; }}
</style></head><body>

{table1}
{table2}

</body></html>"""

with open("SMARTRECRUITZ_UTILIZATION.html", "w") as f:
    f.write(HTML)
print(f"days={len(days)} SR={n_sr} IS={n_is} -> wrote SMARTRECRUITZ_UTILIZATION.html")

# ── Spreadsheet exports (Google Sheets: paste the .tsv, or File > Import the .csv) ──
import csv

sheet_rows = []
for i, (dt, (proj, task)) in enumerate(zip(days, TASKS), 1):
    work = f"Interview as a Service: {task}" if proj == "IS" else task
    sheet_rows.append([i, dt.strftime("%d %b %Y"), dt.strftime("%A"), work])

header = ["#", "Date", "Day", "Work Performed"]

with open("SMARTRECRUITZ_UTILIZATION.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(sheet_rows)

with open("SMARTRECRUITZ_UTILIZATION.tsv", "w", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(header)
    w.writerows(sheet_rows)

print(f"wrote SMARTRECRUITZ_UTILIZATION.csv and .tsv ({len(sheet_rows)} rows)")
