# Phase 1.4.2.2.1 Test Execution Audit Evidence

This directory contains the original, unedited test execution artifacts exported from the execution environment for **Phase 1.4.2.2.1: Independent Audit Discrepancy Resolution**.

All files are exact, byte-for-byte copies preserved from the underlying execution task store.

---

## Artifact Inventory & Provenance

### 1. Structural Engineering & Governance Suite (106 Tests)
- **Exported File:** [`task-7615.log`](file:///Users/karthik/tneb-account-extractor/audit_evidence/phase_1_4_2_2_1/task-7615.log)
- **Original Source Artifact:** `/Users/karthik/.gemini/antigravity-cli/brain/dd275a14-3e0a-41cc-be99-7b5230151074/.system_generated/tasks/task-7615.log`
- **Execution Command:** `cd /Users/karthik/tneb-account-extractor && python3 -m unittest discover -s tests -p 'test*.py' -v`
- **Execution Timestamp:** `2026-11-07T12:21:09Z` to `2026-11-07T12:21:24Z` (17:51:09 – 17:51:24 IST)
- **Exit Code:** `0` (Success)
- **Test Count:** 106 tests (106 passed, 0 failed, 0 errors, 0 skipped)
- **File Size:** 23,529 bytes
- **SHA-256 Checksum:** `54b2bd7cadc94d91f2a60bf3521129231d9de1367f8854690d19b51fae751cc2`

### 2. TNEB Account Extractor Exact Matching & Portal Protection Suite (23 Tests)
- **Exported File:** [`task-7620.log`](file:///Users/karthik/tneb-account-extractor/audit_evidence/phase_1_4_2_2_1/task-7620.log)
- **Original Source Artifact:** `/Users/karthik/.gemini/antigravity-cli/brain/dd275a14-3e0a-41cc-be99-7b5230151074/.system_generated/tasks/task-7620.log`
- **Execution Command:** `cd /Users/karthik/tneb-account-extractor && python3 -m unittest -v test_exact_matching.py`
- **Execution Timestamp:** `2026-11-07T12:21:26Z` to `2026-11-07T12:22:23Z` (17:51:26 – 17:52:23 IST)
- **Exit Code:** `0` (Success)
- **Test Count:** 23 tests (23 passed, 0 failed, 0 errors, 0 skipped)
- **File Size:** 8,520 bytes
- **SHA-256 Checksum:** `8577f72b20c1dc437c40fecc0103f5eb0b91d4de7e67da19f2f2132a58435162`

### 3. Commercial Solar Quotation Isolated Suite (20 Tests)
- **Exported File:** [`output.txt`](file:///Users/karthik/tneb-account-extractor/audit_evidence/phase_1_4_2_2_1/output.txt)
- **Original Source Artifact:** `/Users/karthik/.gemini/antigravity-cli/brain/dd275a14-3e0a-41cc-be99-7b5230151074/.system_generated/steps/7626/output.txt`
- **Execution Command:**
  ```bash
  python3 -c '
  import os, sys, sqlite3, tempfile, unittest, shutil

  with tempfile.TemporaryDirectory(prefix="rensun_test_") as tmp:
      source = sqlite3.connect("quotations.db")
      target_path = os.path.join(tmp, "quotations.db")
      target = sqlite3.connect(target_path)
      source.backup(target)
      target.close()
      source.close()

      settings_path = os.path.join(tmp, "quotation_settings.json")
      shutil.copy2("quotation_settings.json", settings_path)

      pdf_dir = os.path.join(tmp, "generated_quotations")
      os.makedirs(pdf_dir)

      import quotation.quotation_history as qh
      import quotation.settings_manager as sm
      import quotation.pdf_generator as pg

      qh.DB_PATH = target_path
      sm.SETTINGS_FILE = settings_path
      pg.OUTPUT_PDF_DIR = pdf_dir

      import test_quotation_system

      suite = unittest.TestLoader().loadTestsFromModule(test_quotation_system)
      result = unittest.TextTestRunner(verbosity=2).run(suite)
      sys.exit(0 if result.wasSuccessful() else 1)
  '
  ```
- **Execution Timestamp:** `2026-11-07T12:22:06Z` to `2026-11-07T12:22:13Z` (17:52:06 – 17:52:13 IST)
- **Exit Code:** `0` (Success)
- **Test Count:** 20 tests (20 passed, 0 failed, 0 errors, 0 skipped)
- **File Size:** 2,917 bytes
- **SHA-256 Checksum:** `3c268d6116637f803b96879bceea2b39c13e21e1537cacf3ce7701c87cb1e279`

---

## Verification & Integrity Safeguards

- **Total Automated Tests:** 149 / 149 PASSED (100% pass rate)
- **Rerun Operations:** Zero tests rerun during export.
- **Git State:** No files staged or committed; branch and HEAD remain at `df8d5da966b6506c1eada7093db2a140cbc0b9dc`.
- **Database & Settings Integrity:** Production `quotations.db` and `quotation_settings.json` remain untouched.
