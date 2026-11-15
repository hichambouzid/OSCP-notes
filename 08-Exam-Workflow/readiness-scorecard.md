# OSCP+ readiness scorecard — before exam day

Use this to measure independent preparation, not as a prediction of passing. Practice only in assigned course labs or systems you own. Retest weak subjects without AI, hints or walkthroughs.

## 1. Three-level rating

0 = cannot explain or complete independently; 1 = can explain but needs reference or repeated help; 2 = can complete the assigned exercise independently, explain observations and document results.

| Skill | Score 0–2 | Evidence from private practice |
| --- | --- | --- |
| Scope, VPN and local networking | | |
| Interpret service inventory and distinguish TCP/UDP | | |
| Explain HTTP requests, responses, cookies and redirects | | |
| Explain authentication vs authorization | | |
| Identify an application and assess vendor/version information | | |
| Explain initial access prerequisites and false positives | | |
| Complete assigned initial-access course lab independently | | |
| Identify Linux user, groups, OS and permissions | | |
| Complete assigned Linux privilege-escalation course lab independently | | |
| Identify Windows account, token, OS and ACLs | | |
| Complete assigned Windows privilege-escalation course lab independently | | |
| Explain AD domain, DC, SID, SPN, TGT and service ticket | | |
| Explain Kerberos errors and password-verifier distinctions | | |
| Complete assigned AD course lab independently | | |
| Explain network routing and tunnel concepts | | |
| Capture evidence in a permitted interactive session | | |
| Write a reproducible report from private notes | | |
| Export PDF, archive and verify submission package | | |
| Explain exam tool restrictions without looking them up | | |

Maximum self-assessment score: 38. A zero on evidence, exam policy or reporting is an urgent gap regardless of total. This is a personal rubric, not OffSec scoring.

## 2. Suggested mock rehearsal

1. Choose a fresh, authorized course exercise; record scope and a time budget.
2. Work without AI, external hints or walkthroughs. Use your static notes and permitted course references.
3. Keep a timestamped private journal of decisions, observations and exact commands you actually used.
4. Practice the required proof screenshot format on an authorized exercise.
5. Write a report and check whether you can reproduce the exercise from the report alone.
6. Record missed concepts and repeat a different exercise. Do not count memorizing a walkthrough as mastery.

## 3. Example 23h45 exam budget (personal planning, not a requirement)

| Elapsed | Focus |
| --- | --- |
| 0–1 h | Proctor setup, scope, VPN, objectives, evidence folders |
| 1–7 h | Work on the best-understood assigned objectives |
| 7–8 h | Food, rest and notes review |
| 8–13 h | Remaining objectives and bounded investigation |
| 13–17 h | Sleep / substantial rest |
| 17–21 h | Revisit incomplete objectives |
| 21–23h45 | Evidence review and control-panel submissions |

Adapt to your actual objectives and energy; the clock keeps running. Report submission has its own deadline. Do not wait until the last minutes to submit proofs.

## 4. Rules to check immediately before the exam

Verified against OffSec public guidance on 2026-11-15. The official guide takes precedence.

- Open-book: personal notes, approved online resources and the OffSec Learning Platform are permitted, but no direct-prompt AI/LLM assistance or third-party hints. Conduct all activities on the monitored host.
- Duration: 23h45 exam and a further 24h for report upload.
- Three standalone machines (60 raw points) and a three-machine AD set (40 raw points). AD starts with supplied credentials. Specific objectives appear in the exam control panel.
- For starts on or after 2026-12-01 08:00 GMT, scaled scoring applies; check the current scaled-scoring FAQ rather than assuming a fixed raw passing threshold.
- Do not use prohibited automatic exploitation, mass vulnerability scanning, spoofing or commercial tools. Metasploit/Meterpreter limitations apply to the selected target, including unsuccessful attempts; verify the exceptions in the official guide.
- Proof: submit the original values in the control panel before the exam ends; screenshot the original file read with cat/type in an interactive target shell, including the target IP. A web-based shell does not meet the requirement. For full points, meet the required privileged identity on the relevant target.
- Report: PDF only within an unencrypted .7z, exact case-sensitive filenames, at most 200 MB. Verify the uploaded MD5 and click Submit File before the deadline. See the official guide for modified/unmodified code documentation.
- Do not copy exam material into this repository, share it with AI or other people, or download target files unless necessary and permitted under the guide; remove permitted downloads as required.

Official references:
- [OSCP+ Exam Guide](https://help.offsec.com/hc/en-us/articles/360040165632-OSCP-Exam-Guide)
- [OSCP+ Exam FAQ](https://help.offsec.com/hc/en-us/articles/4412170923924-OSCP-Exam-FAQ)
- [AI usage policy](https://help.offsec.com/hc/en-us/articles/35549468971156-AI-Usage-Policy-in-OffSec-Exams)

## 5. Last rehearsal: no avoidable mistakes

- [ ] Offline copy of notes opens and search works.
- [ ] All course exercises used to test readiness were authorized.
- [ ] Installed tools and local help commands verified before exam.
- [ ] Can distinguish failure of network, identity and permissions.
- [ ] Private evidence location is outside the Git repository.
- [ ] Can produce a sample PDF, test the 7z archive, and compare its checksum.
- [ ] Know the official exam support route and deadlines.

[Back to beginner desk reference](../00-Quick-Reference/beginner-desk-reference.md)
