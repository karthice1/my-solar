# PHASE 1.5.3.2B.2A — PRODUCTION FILE INTEGRITY & MANIFEST AUDIT PLAN

**Project ID:** RS-STR-RENSUN-2026-0059  
**Quotation:** RENSUN/2026/0059  
**Repository:** `/Users/karthik/tneb-account-extractor`  
**Branch:** `feature/phase1-structural-foundation`  
**Baseline HEAD:** `df8d5da966b6506c1eada7093db2a140cbc0b9dc`  
**Platform:** Google Antigravity  
**Statutory Watermark:** `PRELIMINARY — FOR REVIEW ONLY — NOT FOR CONSTRUCTION`  
**Construction Status:** `BLOCKED_AFC_LOCKED` (`is_approved_for_construction = false`)  
**Mandatory Final Status:** `ENGINEERING REVIEW INCOMPLETE — AWAITING INDEPENDENT ENGINEER AND PHYSICAL SITE EVIDENCE`  

---

## 1. Executive Summary

This plan defines the cryptographic architecture and operational protocol required to guarantee zero-mutation invariance across all production databases, configuration files, CAD drawings, and quotation documents.

Previous phases verified file non-interference primarily through directory file counts (e.g., verifying that `generated_drawings/` contains 5 files and `generated_quotations/` contains 33 PDFs). As identified in the Phase 1.5.3.2B.2A audit, **directory count verification alone is insufficient**: a compromised test or faulty script could overwrite an existing production drawing or PDF in-place without altering the directory file count.

This plan establishes:
1. Individual file-level SHA-256 cryptographic manifests for all existing production assets.
2. Complete reconciliation of the historical 34 files vs 33 PDFs inventory discrepancy.
3. Enhanced runtime assertion mechanisms to be embedded in `tests/test_isolation_helper.py`.

---

## 2. Protected Production Core Assets

The three primary operational and structural state files must remain bit-for-bit invariant across all test and audit executions:

```text
====================================================================================================
PRIMARY PRODUCTION STATE FILES — CRYPTOGRAPHIC BASELINE
====================================================================================================
1. Database: quotations.db
   Canonical Path: /Users/karthik/tneb-account-extractor/quotations.db
   File Size:      106,496 bytes
   SHA-256 Hash:   3586bf382d5ae4ccfc1beab6fefb475e8d7d48c6b8e76088cdbe2786a66448bf
   Integrity Rule: ZERO byte mutation; connections intercepted and blocked by ConnectionAuditor.

2. Database: structural/structural_runs.db
   Canonical Path: /Users/karthik/tneb-account-extractor/structural/structural_runs.db
   File Size:      86,016 bytes
   SHA-256 Hash:   ff234f0d9c2c3a274749ad35a60dbaf18e844cbfadd9e7c714baf1f779220bff
   Integrity Rule: ZERO byte mutation; preserves exactly 20 historical calculation runs.

3. Configuration: quotation_settings.json
   Canonical Path: /Users/karthik/tneb-account-extractor/quotation_settings.json
   File Size:      78 bytes
   SHA-256 Hash:   26be49f673e1cd43cfda083b61cde0cf46e53462cdcfe69b0c2f2de9f312b0a1
   Integrity Rule: Read-only; isolated environment creates temporary copy in sandbox.
====================================================================================================
```

---

## 3. Production CAD Drawings Inventory Manifest

All production DXF drawings residing in `/Users/karthik/tneb-account-extractor/generated_drawings/` are inventoried with individual SHA-256 hashes:

| # | Drawing Filename | File Size | SHA-256 Checksum | Drawing Scope / Project |
|:---:|:---|:---:|:---|:---|
| 1 | `Structural_Layout_RENSUN_2026_0078.dxf` | 41,245 bytes | `d6418f2631f0e2696b7d302c25d50a285f819a13e72f7ef518bdb4c1572594c6` | System A Canopy Layout (Quotation 0078) |
| 2 | `Structural_Layout_RENSUN_2026_TEST01.dxf` | 47,499 bytes | `8170e3cca794596524f4012420cb249c55c54024bae2c459bfa25787089c4a73` | Test Baseline Drawing Layout |
| 3 | `Structural_Layout_RS_STR_RENSUN_2026_0059.dxf` | 41,246 bytes | `3b199756007c0ea28e40c9a3645ea6fa0160b6d1efa07b8cc928e7a96761c37a` | Project RS-STR-RENSUN-2026-0059 System A |
| 4 | `Structural_Layout_RS_STR_TEST_SYS_B.dxf` | 47,584 bytes | `04fc2563521e58b37ff577174966c56012d6184ddcb8309d4046ad0a8585a6ec` | System B Low-Height Aluminium Rail Layout |
| 5 | `Structural_Layout_RS_STR_TEST_SYS_D.dxf` | 43,586 bytes | `3f4d972c827b198e9a5cc73409c2d3182e5e00d3e1a8925ac939c33a7ffb3bec` | System D Ballasted Layout |

**Total Production Drawings:** Exactly 5 DXF files.

---

## 4. Production PDF Quotations Inventory & Reconciliation

### 4.1 Reconciliation of Historical 34 Files vs 33 PDFs Discrepancy

In the Phase 1.5.1 Baseline Protection Report, the directory was recorded as containing **34 files**. In subsequent test assertions, the PDF count was verified as **33 PDFs**. The audit reconciles this conclusively:

1. **Filesystem Listing (`ls -A generated_quotations/`):** Exactly **34 entries**:
   - 33 `.pdf` files (Commercial proposal documents from `quotation_RENSUN_2026_0001.pdf` through `quotation_RENSUN_2026_0090.pdf`).
   - 1 hidden tracking file: `.gitkeep` (0 bytes, SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`).
2. **PDF Extension Listing (`ls generated_quotations/*.pdf`):** Exactly **33 files**.
3. **Repository-Wide PDF Search (`find . -name "*.pdf"`):** Exactly **33 files**.

**Conclusion:** Zero PDFs were lost or modified. The discrepancy was entirely semantic: counting total directory entries (including `.gitkeep`) vs counting files matching the `*.pdf` extension filter.

---

## 5. Enhanced Test Isolation Implementation Plan

To eliminate the gaps identified in `PHASE_1_5_3_2B2A_TEST_ISOLATION_GAP_MATRIX.csv`, the following enhancements are specified for `tests/test_isolation_helper.py`:

### 5.1 Realpath and Symlink Resolution
Update `ConnectionAuditor.intercept_connect` to resolve paths via `os.path.realpath(os.path.abspath(db_path))` before checking against blocked paths:
```python
def resolve_canonical_path(path: str) -> str:
    # Strip SQLite URI prefix and query strings if present
    if path.startswith("file:"):
        path = path[5:].split("?")[0]
    return os.path.realpath(os.path.abspath(path))
```

### 5.2 SQLite Connection Class Patching
In addition to patching `sqlite3.connect`, patch `sqlite3.Connection.__init__` directly to trap connection instances instantiated via alternative mechanisms or pre-imported aliases.

### 5.3 Cryptographic Pre- and Post-Test Manifest Verification
Extend `IsolatedTestEnvironment` to compute and store a full dictionary of SHA-256 hashes of all files in `generated_drawings/` and `generated_quotations/` during `setUpClass()`, and assert 100% hash identity during `tearDownClass()`, rather than relying solely on file counts.

```python
def capture_directory_manifest(directory: str) -> Dict[str, str]:
    manifest = {}
    for root, _, files in os.walk(directory):
        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            manifest[fpath] = get_file_sha256(fpath)
    return manifest
```

---

## 6. Execution Protocol & Governance Verification

Prior to any future test or calculation phase:
1. Pre-execution hash check confirms all production assets match this baseline manifest.
2. `IsolatedTestEnvironment` redirects all runtime outputs to ephemeral sandbox directories.
3. Post-execution hash check verifies bit-for-bit invariance across all 3 primary state files, 5 DXF drawings, 33 proposal PDFs, and 1 `.gitkeep` file.
4. Construction status remains permanently locked at `BLOCKED_AFC_LOCKED`.
