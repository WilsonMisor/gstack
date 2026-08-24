# Human Authority and AI Boundary

AI may analyse, propose, implement approved scope, test, measure, generate evidence, recommend, document, monitor and escalate. AI may not accept material risk, waive failed tests/controls, approve its own security/privacy/legal/financial exception, silently add paid vendors, silently expand scope/architecture, declare compliance, approve financial custody, infer missing/past approval, approve irreversible production-data mutation, or declare `PRODUCTION APPROVED`.

Decision authority must be explicit in the Project Contract. Typical authority classes: product scope PDM/PO/SP; architecture PSA/STAFF/SA; production security exception SEC/APPSEC; privacy DPO/PRIV; legal interpretation LEGAL; financial exposure/custody FIN/PAY/LEGAL as applicable; launch designated release authority; emergency shutdown IC/SRE/authorized executive; destructive data action designated data/business authority; risk acceptance designated accountable human. These are defaults, not inferred authorizations.

Every approval record carries approval ID, decision/scope, authority, status, timestamp and where relevant expiration/review trigger. A crash never converts PENDING into APPROVED. A missing qualified role remains `ROLE GAP`.
