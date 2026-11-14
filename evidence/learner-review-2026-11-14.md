# Independent bilingual learner review — 2026-11-14

## Scope and evidence boundary

Reviewed the current Vietnamese Console and Terraform learning paths, their convergence at build/deploy/baseline, reruns, optional CLI examples, downloaded ZIP contents and available English translations. No AWS commands, SDK calls, provisioning or mutations were run: the reference AWS environment is stopped. Checks below are local/static only.

At the first pass, 36 of 46 English pages existed; preparation 4–9, cleanup, summary and validation were still being translated. Across the existing 36 English pages, executable bash blocks matched Vietnamese exactly after comments were removed. All 15 Python scripts parsed successfully, all six shell scripts passed `bash -n`, and existing Terraform source files passed `terraform fmt -check infrastructure/terraform`.

Prior live evidence is distinct: stored network-before results are dated 2026-11-13T15:10:30Z (4 tests), after results 15:11:25Z (5 tests), full verification 15:17:07Z (25 tests), and scan evidence 15:12:17Z (BLOCK). These are reference artifacts read today, not a new 2026-11-14 execution or proof that Console provisioning has been walked through live.

## Findings

### 1. P1 — Downloaded ZIP cannot save learner evidence

**Confirmed by reading the actual downloadable archive.** The ZIP contains 40 entries and no `evidence/` entry. `scripts/package_lab.py:4–8` only packages README/gitignore/requirements plus app/scripts/k8s/Terraform. However, `scripts/network-proof.py:42`, `scripts/verify.py:184` and `scripts/scan-gate.py:28` write files under `evidence/` without creating the parent directory.

A fresh ZIP learner therefore runs the AWS/Kubernetes test work and then gets FileNotFoundError when its report is written. This affects both Console and Terraform users choosing the documented ZIP alternative, while a Git checkout hides the problem because evidence/ already exists.

**Correction:** make every evidence-producing entry point create its output directory before writing. Including a small evidence/README in the ZIP also communicates the directory's purpose, but scripts should be robust if it is absent. Repackage and inspect the actual downloadable ZIP afterward. The archive's scan-gate.py matched current source at review time, so this is an actual packaged defect, not an assumption about an old archive.

### 2. P2 — Copied Terraform input example fails the required formatting check

**Locally reproduced without AWS or file mutation.** Preparation copies `infrastructure/terraform/terraform.tfvars.example` to terraform.tfvars and then requires `terraform fmt -check`. The example has inconsistent assignment alignment, e.g. lines 1–2 and 4–6. Feeding those exact contents through `terraform fmt -check -` returned exit 3. Existing checked-in .tf files passed, explaining why the repository-wide check can miss the new user's failure.

**Learner effect:** an otherwise correct first Terraform run stops at a required check before validate/plan, with no instruction explaining how to fix formatting. Both languages inherit the same source example and step order.

**Correction:** format the example contents before distribution, or explicitly run `terraform fmt` once after editing inputs and before `fmt -check`. Recheck the copied-example path rather than only the already-prepared working directory.

### 3. P3 — Optional CLI alternatives still need explicit variable acquisition

**Static usability issue, not a blocker on the main Console/Terraform baseline.** The optional API association in `workshop/content/4-identity/5-workload-identity/_index.en.md:56` uses `$API_ROLE_ARN` without defining it. The optional database SG rule in `2-network-security/4-security-groups/_index.en.md:26` uses `$DB_SG_ID`; the public-route example in `2-network-security/2-vpc/_index.en.md:47` uses `$PUBLIC_ROUTE_TABLE_ID`/`$INTERNET_GATEWAY_ID`. The same gaps exist in Vietnamese. These examples assume the reader obtains/exports values independently; the standard Console baseline already created the resources, so the normal path can skip them.

**Correction:** show read-only acquisition commands or precisely say which Console field to copy into each export immediately before the optional command. Keep the existing instruction not to create duplicate resources.

## Strengths and closure from prior review

Both paths now choose provisioning early and clearly converge on the same metadata/build/deploy sequence. KMS is correctly deferred for Console baseline while WAF discovery is required. Observer JSON and ARN inputs are concrete, Terraform observers/keys are reused, probes are controller-owned and excluded from serving selectors, TCP refusal is distinguished from policy timeout, and candidate scan/sign/deploy has a coherent predeployment gate with separate evidence. Completed bootstrap Job replacement and ordered cleanup are documented.

The current source therefore has no newly identified application-security correctness blocker beyond the distribution/output issue above. The copied tfvars formatting issue is a reproducible preparation failure rather than a cloud-permissions concern. Language navigation/browser checks and final translation completion are being handled by the primary agent; this report does not claim those checks are complete.

## English completion review

All **46 English pages** are now present and were included in the follow-up. I read the added preparation 4–9, cleanup, summary, verification and observed-results pages against Vietnamese and current scripts. The added preparation sequence supplies the same resource names, master-secret/IAM database requirements, Pod Identity trust/permissions, domain/WAF prerequisites and branch convergence. Candidate update ordering and deferred KMS handling remain consistent.

A second local comparison across all 46 language pairs found **zero executable bash differences** after removing comment-only lines, and **zero JSON/YAML fenced-block differences**. Some English shell comments were still Vietnamese during review; the primary agent owns that translation sweep. No additional substantive learner-order or permission blocker was found in the new English pages.

The formatting correction should also cover the displayed editable HCL examples, or add `terraform fmt` before the required check: pasting the unaligned HCL block recreates the same failure even if the downloadable example is formatted. Fixes for the two confirmed findings and optional CLI inputs are in progress; closure will be recorded after inspecting the actual output/package.

### Additional P2 — README lab-validation sequence invokes an unprepared website checker

The README's “Supply chain và validation” shell block includes `python3 scripts/check_site.py`, but no preceding command builds the Hugo site at its default `.local/site` input. `scripts/check_site.py:7` immediately parses `.local/site/sitemap.xml`. A fresh Git learner lacks that build; a ZIP learner additionally has no workshop source by design. The command therefore fails for reasons unrelated to lab success. The website lessons themselves do not require it.

Separate site-author validation from the learner lab sequence, with a full-clone prerequisite and explicit Hugo build command, or omit this command from the lab quickstart. This is a source/order finding, not an AWS execution result.

## Final closure — fresh source and downloadable archive checked

All findings above are now **closed** in the current reviewed files:

- All three report writers create evidence/ before writing. The regenerated ZIP has **43 entries**, including evidence/README.md, and its scan-gate.py, verify.py and network-proof.py match current source byte-for-byte. The archive contains no unexpected sensitive-path entries.
- The exact terraform.tfvars.example now passes `terraform fmt -check -` with exit 0. Both language pages run ordinary fmt after editing and before fmt -check, covering copied/pasted input as well.
- Optional API_ROLE_ARN, database SG, public route-table/IGW and ALB target-group inputs now have acquisition commands in both languages.
- README separates website-author checks from learner lab validation and provides the Hugo build prerequisite. The regenerated archive also contains that corrected README and formatted input example.

Fresh final checks still report all **46 English pages**, zero executable bash differences between VN/EN (comments excluded), successful parsing of all 15 Python scripts and bash syntax for all six shell scripts. JSON/YAML block parity was also checked across all 46 pairs.

**Final assessment:** no concrete unresolved source/order/package blocker remains from this review. Both provisioning paths are statically coherent and converge on the same application baseline. This is a local learner walkthrough and code/package review; no AWS was accessed today, and it does not add a fresh live Console-provisioning claim to the historical 2026-11-13 Terraform/CLI evidence.
