# Reference comparison and maintenance checklist

Reviewed 2026-11-15. This comparison concerns documentation structure and study usability, not a claim that external commands are safe, current, permitted or verified against the exam.

| Reference | Observed structure or strength | What this repository adopts |
| --- | --- | --- |
| [0xsyr0/OSCP](https://github.com/0xsyr0/OSCP) | Broad cheat-sheet collection with separate resources and examples | Fast topic lookup, clear command context and short examples |
| [dudisamarel/OSCP-Notes](https://github.com/dudisamarel/OSCP-Notes) | Separate information-gathering, Linux, Windows and web chapters; GitBook-oriented organization | Topic-separated documentation and a navigation index |
| [OWASP WSTG](https://owasp.org/www-project-web-security-testing-guide/) | Structured web security testing methodology | Distinguish observation, test conditions, evidence and interpretation |
| [OffSec Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide) | Authoritative exam scope, restrictions, proof and reporting rules | Dedicated exam checklist; official guidance overrides community notes |

## Practical gap review

| Area | Existing repository | Added improvement |
| --- | --- | --- |
| Service coverage | Extensive service-specific chapter | [Fast reference index](../00-Quick-Reference/reference-index.md) |
| Command recall | Commands in detailed chapters | [Local hands-on drills](../09-Lab-Writeups/hands-on-terminal-drills.md) with prerequisites, output and cleanup |
| Authentication concepts | AD and password chapters | Kerberos glossary, error interpretation and distinction between tickets and hashes |
| Troubleshooting | Distributed across chapters | Consolidated error-to-layer table |
| Evidence | Exam methodology and reporting | Dummy evidence exercise, private worksheet and reproducibility checklist |
| Verification | General practice recommendations | Self-contained local test script and readiness rubric |

## Template for every new command reference

- Purpose: what question does this command answer?
- Scope and prerequisites: where does it run, with what identity and version?
- Example: clearly identify placeholders and use safe sample data.
- Expected output: include a minimal example, not a guarantee.
- Interpretation: explain what the result establishes and what it does not.
- Troubleshooting: common errors, version differences and when to stop.
- Cleanup: remove temporary practice data and stop local services.
- Evidence: record observed results rather than copying imagined output.
- Verification date: distinguish live test, documentation review and untested example.

## Official scoring update

Per [OffSec's scaled-scoring FAQ](https://help.offsec.com/hc/en-us/articles/54589877508884-OSCP-Equated-Scaled-Scoring-FAQ):
- Exam starts before 2026-12-01 08:00 GMT: 70 raw points required.
- Exam starts at or after that instant: 400 on a 100–500 scaled score range; raw threshold varies by exam set.
- Continue working toward all assigned objectives and submit the report even if you think your score is too low.

The exam guide and control panel are the source of truth. Do not assume a community tool is permitted. The [official AI policy](https://help.offsec.com/hc/en-us/articles/35549468971156-AI-Usage-Policy-in-OffSec-Exams) prohibits interactive AI assistance during OSCP exams; use these notes independently and do not share exam content.

## Maintenance checks before exam day

- [ ] Pull the latest notes and save an offline copy on the monitored machine.
- [ ] Verify that Markdown links open and local search works.
- [ ] Run the harmless local drills before the exam; review every failure.
- [ ] Check installed versions and local help for tools you have independently practiced.
- [ ] Complete authorized course exercises without walkthroughs or AI.
- [ ] Read the current official guide, FAQ and scoring rules.
- [ ] Keep actual exam material and credentials out of Git.
- [ ] Verify proof screenshot requirements and report package before submission.

No repository guarantees an OSCP pass. This comparison does not validate existing exploitation examples or certify tool compatibility.
