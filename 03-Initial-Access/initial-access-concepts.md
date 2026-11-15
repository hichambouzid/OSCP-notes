# Initial access — concepts for a first-time learner

Study this before attempting the assigned PEN-200 exercises. This is a terminology and evidence guide, not an executable intrusion recipe.

## 1. What is initial access?

Initial access is the first confirmed ability to interact with a system under a particular identity or execution context. In a training lab, that could be a supplied account, an application-level session, or a course exercise demonstrating a security defect. These are different capabilities. An authenticated web session does not imply an operating-system shell, and an ordinary shell does not imply administrator rights.

## 2. Recognize the type of finding

| Finding family | What it means | What it does NOT prove |
| --- | --- | --- |
| Authentication weakness | Identity checks do not meet intended security requirements. | That a particular account can be accessed. |
| Broken access control | A user can perform an operation outside intended permissions. | Operating-system command execution. |
| Injection | Untrusted input is interpreted as part of a command, query or expression. | That all injection types provide the same capability. |
| File handling flaw | File paths or content are handled outside intended boundaries. | That reading or uploading a file executes it. |
| Vulnerable component | A product or dependency has a documented weakness. | That the deployed version and configuration satisfy prerequisites. |
| Excessive exposure | A service or administrative feature is reachable more broadly than intended. | That authentication or authorization is absent. |
| Weak secret management | Sensitive authentication material is not protected as intended. | That a particular secret is valid, current or privileged. |
| Misconfiguration | Security settings differ from expected policy. | That all possible consequences have occurred. |

## 3. The evidence ladder

1. Observation: record what the service actually displayed.
2. Interpretation: explain what the observation might mean.
3. Hypothesis: state a specific security property that could be violated.
4. Verification: complete an authorized course exercise and record actual observed behavior; a hypothesis alone is not proof.
5. Context: identify which account, machine, application and permissions are involved.
6. Documentation: preserve reproducible evidence privately, including limitations.

Do not confuse a tool's output with an established finding. Avoid running unfamiliar code solely because a search result suggests it.

## 4. Prerequisite vocabulary

- Reachability: whether communication with an endpoint is possible.
- Authentication: whether an identity can be established.
- Authorization: whether an identity is allowed to perform an operation.
- Execution context: which process, account, host and permissions an operation uses.
- Architecture: processor and operating-system compatibility.
- Dependency: required software, version, feature or configuration.
- Impact: what the verified behavior actually permits, not the worst imagined outcome.

## 5. Common beginner confusions

- HTTP 200 is an application response, not proof of valid credentials.
- A file upload completing does not prove execution.
- SQL injection and OS command injection are different interpreters.
- A CVE identifier is a research reference, not a guarantee of applicability.
- A service account can have access to one service without being a system administrator.
- Local administrator, domain administrator, and root are different concepts.
- In OSCP+ documentation, distinguish the course lab's objective from the actual exam objective.

## 6. Practice independently

Use your assigned course material to complete an initial-access lab. Afterwards, explain the vulnerability class, necessary conditions, actual outcome, identity and scope without consulting a walkthrough. Record the commands you personally used in private notes. Repeat with a different lab to test understanding, not memorization.

For defensive concepts and safe training, see [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/) and [PortSwigger Web Security Academy](https://portswigger.net/web-security).

## 7. What to review next

- [Beginner desk reference](../00-Quick-Reference/beginner-desk-reference.md)
- [Troubleshooting cards](../08-Exam-Workflow/troubleshooting-cards.md)
- [Private target worksheet](../09-Lab-Writeups/target-review-worksheet.md)
- [Readiness scorecard](../08-Exam-Workflow/readiness-scorecard.md)
