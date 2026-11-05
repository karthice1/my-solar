# TNEB Account Extractor & Solar Sizing Tool

Standalone automation tool for **TNPDCL / TNEB** portal (`https://www.tnebnet.org/awp/login?locale=ta`):
1. Solves the 5-digit optical captcha automatically using OCR.
2. Authenticates using dynamically entered user credentials (**User ID** and **Password**).
3. Takes any consumer number as input, adds it to the account, and confirms verification.
4. Navigates to **Account Summary** and loads the detailed billing ledger (`detconws.php`).
5. Extracts all 24 past billing cycles, dues, and connection specifications.
6. Calculates required **Solar Capacity (kW)**:
   $$\text{Solar Capacity (kW)} = \frac{\text{Past 6 Cycles Total Units (kWh)}}{1,500}$$
7. Automatically **deletes** the consumer number from the portal using the delete number option.
8. Provides both a **Web UI Dashboard** (port 8090) and a **Terminal CLI**.

---

## Tool Location (Absolute Path)

```bash
/Users/karthik/tneb-account-extractor
```

---

## How to Start the Tool

### Option 1: Start the Web UI Dashboard (Recommended)

In your terminal, run:

```bash
cd /Users/karthik/tneb-account-extractor
./start_ui.sh
```

*(or run `python3 server.py` directly)*

Then open your browser at:
👉 **[http://127.0.0.1:8090](http://127.0.0.1:8090)**

On the Web UI:
- Enter your **TNEB User ID**
- Enter your **TNEB Password** (with show/hide toggle and optional "Remember credentials" checkbox)
- Enter the **12-digit Consumer Number**
- Click **"Extract & Sizing Analysis"**

---

### Option 2: Run via Terminal CLI

#### Interactive Mode (prompts for User ID, Password, and Consumer Number):
```bash
cd /Users/karthik/tneb-account-extractor
./cli.sh
```
*(or `python3 tneb_tool.py`)*

#### Direct Command Line Arguments:
```bash
cd /Users/karthik/tneb-account-extractor
./cli.sh -u YOUR_USER_ID -p YOUR_PASSWORD -c 044060072111
```
*(or `python3 tneb_tool.py -u YOUR_USER_ID -p YOUR_PASSWORD -c 044060072111`)*

#### Keep connection without auto-deleting:
```bash
./cli.sh -u YOUR_USER_ID -p YOUR_PASSWORD -c 044060072111 --keep
```

---

## Key Files & Outputs

* **Web UI Server**: [`server.py`](file:///Users/karthik/tneb-account-extractor/server.py)
* **Automation Engine**: [`tneb_tool.py`](file:///Users/karthik/tneb-account-extractor/tneb_tool.py)
* **Web Template**: [`templates/index.html`](file:///Users/karthik/tneb-account-extractor/templates/index.html)
* **Saved Reports (JSON)**: `tneb_report_<consumer_no>.json`
* **Saved Reports (Markdown)**: `tneb_report_<consumer_no>.md`
* **Portal Snapshots (PNG)**: `tneb_detail_<consumer_no>.png`
