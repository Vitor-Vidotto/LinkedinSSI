# 📊 LinkedIn SSI Calculator (Open-Source)

An open-source, 100% local, privacy-first command-line tool that estimates your **LinkedIn Social Selling Index (SSI)** directly from your official LinkedIn data export package — without requiring a paid LinkedIn Sales Navigator subscription.

---

## ✨ Key Features

- **Zero Cloud / 100% Local Processing:** Reads your official LinkedIn `.zip` archive directly in memory (or from an extracted folder). No personal data, messages, connections, or search history ever leave your machine.
- **Empirically Calibrated Scoring Engine:** Mathematical weights, rolling time windows, and logarithmic saturation curves calibrated against real **LinkedIn Sales Navigator** ground-truth scores.
- **Resilient CSV Parser:** Automatically handles LinkedIn export quirks, including member-ID file suffixes (e.g., `Shares_1050344536.csv`), preamble disclaimer rows in `Connections.csv`, missing optional CSVs, malformed lines, and `UTF-8` / `Latin-1` encodings.
- **Rolling Window Temporal Analysis:** Automatically detects the exact reference timestamp of your export and evaluates activity across **30-day**, **90-day**, and **365-day** rolling windows.
- **Executive Diagnostics & Action Plan:** Highlights your top strengths, pinpoints scoring bottlenecks, recommends high-ROI actions prioritized by impact, and projects future SSI growth scenarios.
- **Rich Terminal UI & JSON Export:** Renders interactive tables, color-coded progress bars, and submetric breakdowns via `Rich` (with plain-text fallback), plus full structured JSON export.

---

## 📥 1. How to Get Your LinkedIn Data Export

1. Log in to LinkedIn and click your profile icon (**Me**) in the top navigation bar.
2. Go to **Settings & Privacy** → **Data privacy** → **Get a copy of your data**.
3. Select **Download larger data archive, including connections, verifications, contacts, account history, and information we infer about you**.
4. Click **Request archive**. LinkedIn will email you a download link (usually within a few hours to 24 hours).
5. Download the `.zip` archive (e.g., `Complete_LinkedInDataExport_MM-DD-YYYY.zip`). You **do not** even need to unzip it.

---

## 🚀 2. Installation & Usage

### Prerequisites
- Python **3.9+**

Install the required dependencies:
```bash
pip install -r requirements.txt
```

### Running the Desktop GUI (Visual Interface)

You can launch the interactive graphical application with folder & file pickers, real-time calculations, and one-click HTML report generation:

```bash
# Launch directly via Python
python app_gui.py

# Or launch via the CLI
python cli.py --gui
```

#### 📦 Standalone Executable (.EXE for Windows)
A standalone Windows `.exe` is located at:
```text
dist/LinkedIn_SSI_Calculator.exe
```
This executable is **100% portable** and can be sent to colleagues or clients without requiring Python to be installed. They simply double-click it, select their extracted LinkedIn export folder (or `.zip` file), and view/export their SSI scores and HTML reports.

To rebuild the `.exe` at any time:
```bash
pyinstaller --noconfirm --onefile --windowed --name "LinkedIn_SSI_Calculator" --icon "app_icon.ico" --add-data "src;src" --add-data "app_icon.ico;." --collect-data customtkinter app_gui.py
```

---

### Running via Command Line (CLI)

You can pass either the raw `.zip` file or an extracted folder path to `cli.py`:

```bash
# Run directly on the official LinkedIn .zip export (in-memory, no extraction needed)
python cli.py "path/to/Complete_LinkedInDataExport.zip"

# Run on an extracted directory
python cli.py "path/to/extracted_folder"

# Auto-detect data folder or .zip file in ./Dados, ./data, or current directory
python cli.py

# Generate and export the complete visual HTML report (viewable in any browser / printable to PDF)
python cli.py "path/to/extracted_folder" --export-html relatorio_ssi.html

# Verbose mode: display full submetric breakdown, raw extracted values, and algorithm explanations
python cli.py "path/to/Complete_LinkedInDataExport.zip" -v

# Export the complete SSI breakdown, raw metrics, and diagnostic report to JSON
python cli.py "path/to/Complete_LinkedInDataExport.zip" --export-json ssi_report.json

# Plain-text output mode (disables Rich colors and tables)
python cli.py "path/to/Complete_LinkedInDataExport.zip" --no-rich
```

### CLI Arguments Reference

| Argument | Description |
| :--- | :--- |
| `source` *(optional)* | Path to the extracted LinkedIn data directory or `.zip` archive. If omitted, `cli.py` searches `Dados/Descompilado`, `Descompilado`, `data`, `dados`, and `.zip` files in `./Dados` or `.`. |
| `--gui` | Launches the modern graphical desktop interface
, modern visual HTML report (printable as PDF with Ctrl+P). |
| `-v`, `--verbose` | Prints a detailed table of every submetric, its score vs. maximum cap, raw extracted counts, and scoring rationale. |
| `--export-json <FILE>` | Exports metadata, pillar scores, raw metrics, and strategic recommendations to a structured `.json` file. |
| `--no-rich` | Forces standard ASCII output instead of `Rich` terminal panels and tables. |

---

## 🏗️ 3. Project Architecture & Pipeline

```text
LinkedinSSI/
├── src/
│   ├── __init__.py          # Package version metadata
│   ├── parser.py            # Resilient ZIP & folder CSV reader, indexer, and sanitizer
│   ├── metrics.py           # Feature extractor: rolling windows (30d/90d/365d), profile & seniority
│   ├── ssi_engine.py        # Calibrated mathematical engine for the 4 SSI pillars (0–100)
│   ├── recommendations.py   # Diagnostic engine, prioritized action items, and growth simulations
│   └── report_generator.py  # Standalone visual HTML & PDF-printable report generator
├── app_gui.py               # Modern desktop GUI application (CustomTkinter)
├── cli.py                   # Command-line interface, Rich report renderer, and exporters
├── app_icon.ico             # Application icon
├── requirements.txt         # Python dependencies (customtkinter, pandas, rich, etc.)
└── README.md                # Project documentation
```

### End-to-End Execution Flow

```mermaid
flowchart LR
    A["LinkedIn Export (.zip or Folder)"] --> B["LinkedInDataParser (src/parser.py)"]
    B --> C["MetricsExtractor (src/metrics.py)"]
    C --> D["SSIEngine (src/ssi_engine.py)"]
    D --> E["RecommendationsGenerator (src/recommendations.py)"]
    E --> F["Terminal UI (Rich) & JSON Report"]
```

1. **Ingestion & Sanitization (`src/parser.py` — `LinkedInDataParser`):**
   - Indexes all `.csv` files inside a directory or `.zip` stream (`io.BytesIO` / `zipfile.ZipFile`).
   - Resolves file names via exact match, member-ID regex (`^<name>(_.*)?\.csv$`), or substring fallback.
   - Automatically skips the 3 warning lines at the top of `Connections.csv`, strips column whitespace, skips malformed rows, and falls back from `UTF-8` to `Latin-1` when needed.
   - Missing optional files (e.g., if a user has never created a poll or published a post) gracefully return empty DataFrames instead of crashing.

2. **Temporal & Structural Feature Extraction (`src/metrics.py` — `MetricsExtractor`):**
   - Parses heterogeneous timestamp columns into UTC (`pd.to_datetime(..., utc=True, format="mixed")`).
   - Determines the **Reference Date** (`reference_date`) dynamically from the latest timestamp recorded across your export files so historical exports are scored relative to when they were generated.
   - Computes 30-day, 90-day, and 365-day activity counts alongside static profile completeness and network seniority (`LinkedInMetrics`).

3. **Mathematical Scoring (`src/ssi_engine.py` — `SSIEngine`):**
   - Evaluates each of the 4 pillars on a `[0.0, 25.0]` scale and sums them into the consolidated SSI score `[0.0, 100.0]`, estimating both industry and network percentiles (`SSIResult`).

4. **Strategic Diagnostics (`src/recommendations.py` — `RecommendationsGenerator`):**
   - Evaluates pillar thresholds and raw activity cadences to generate strengths, bottlenecks, high/medium/low-priority action items, and projected SSI gain scenarios (`DiagnosticReport`).

---

## 🧮 4. Detailed Scoring Methodology (How Points Are Calculated)

LinkedIn's Social Selling Index ranges from **0 to 100**, divided equally across **4 pillars** worth **25 points each**:

$$\text{Total SSI} = P_1 + P_2 + P_3 + P_4 \quad \text{where } P_i \in [0, 25]$$

Because LinkedIn's algorithm heavily weights recent consistency over multi-year history, dynamic behavioral metrics focus primarily on the **90-day rolling window** prior to the export's reference date.

---

### Pillar 1: Establish Your Professional Brand (Max: 25.00 pts)
Evaluates static profile completeness ("All-Star" readiness), social proof, and recent original content creation:

| Submetric | Max Pts | Formula & Criteria |
| :--- | :---: | :--- |
| **1. Profile Completeness (All-Star)** | `10.0` | • Headline length > 10 chars: **+2.50 pts**<br>• Summary ≥ 500 chars: **+2.50 pts** *(or **+1.50 pts** if > 100 chars)*<br>• ≥ 3 positions listed with ≥ 2 containing descriptions: **+2.50 pts**<br>• ≥ 1 education entry: **+1.00 pt**<br>• ≥ 1 certification or project: **+1.00 pt** |
| **2. Credibility & Recommendations** | `5.0` | `min(4.0, recommendations_received × 0.50) + skill_bonus`<br>• `skill_bonus`: **+1.0 pt** if ≥ 50 skills, **+0.5 pt** if ≥ 10 skills, else `0.0` |
| **3. Feed Publications (90d)** | `10.0` | `min(10.0, shares_90d × 0.444)`<br>• Reaches full 10-point cap at ~23 posts in 90 days (~2 posts/week). |

---

### Pillar 2: Find the Right People (Max: 25.00 pts)
Uses **base-10 logarithmic scaling** (`log10`) to reward consistent prospecting while preventing bulk automation or spam from artificially maxing out the pillar without high acceptance/filter usage:

| Submetric | Max Pts | Formula & Criteria |
| :--- | :---: | :--- |
| **1. Platform Searches (90d)** | `12.0` | `min(12.0, (log10(search_queries_90d + 1) / log10(1000)) × 3.82)` *(0 if no searches)* |
| **2. Outbound Invitations (90d)** | `9.0` | `min(9.0, (log10(invitations_sent_90d + 1) / log10(1000)) × 2.47)` *(counts `OUTGOING` invites)* |
| **3. Company & Sector Monitoring** | `0.7` | `min(0.70, (company_follows_count / 100.0) × 0.70)` *(following target accounts carries modest weight compared to active search & profile views)* |

---

### Pillar 3: Engage with Insights (Max: 25.00 pts)
Measures meaningful participation in industry conversations over the last 90 days. Comments carry **~7× more weight** per action than passive reactions:

| Submetric | Max Pts | Formula & Criteria |
| :--- | :---: | :--- |
| **1. Feed Reactions (90d)** | `8.0` | `min(8.0, reactions_90d × 0.040)` *(caps at 200 reactions in 90 days)* |
| **2. Constructive Comments (90d)** | `12.0` | `min(12.0, comments_90d × 0.2737)` *(caps at ~44 comments in 90 days)* |
| **3. Polls & Reposts Participation** | `5.0` | `vote_pts + share_pts`<br>• `vote_pts`: **1.0 pt** if ≥ 5 poll votes, else **0.5 pt**<br>• `share_pts`: **+0.5 pt** if ≥ 1 share in the last 90 days |

---

### Pillar 4: Build Relationships (Max: 25.00 pts)
Evaluates first-degree network scale, concentration of senior decision-makers, and active two-way private conversations:

| Submetric | Max Pts | Formula & Criteria |
| :--- | :---: | :--- |
| **1. Network Volume** | `10.0` | Scales linearly up to 500 connections: `(connections_total / 500) × 8.50`, capping at **8.50 pts** for ≥ 500 connections. |
| **2. Decision-Maker Ratio** | `7.0` | `min(7.0, decision_maker_ratio × 0.22976)`<br>• Scans `Position` titles in `Connections.csv` (EN/PT) for leadership keywords: `director`, `diretor`, `ceo`, `founder`, `fundador`, `co-founder`, `vp`, `vice president`, `head`, `manager`, `gerente`, `partner`, `sócio`, `owner`, `lead`, `cto`, `cfo`, `cio`, `cmo`, `coo`, `cpo`, `cro`, `chief`.<br>• Reaches full 7.0-point cap at ~30.5% decision-makers. |
| **3. Active DM Conversations (90d)** | `8.0` | `min(8.0, message_threads_90d × 0.0444)`<br>• Counts **unique active conversation threads** (`CONVERSATION ID`), not raw message count. Caps at ~180 active threads in 90 days. |

---

### Pillar Classifications & Percentile Thresholds

Each pillar is classified according to its score out of 25:
- **20.0 – 25.0:** Excellent
- **15.0 – 19.99:** Good
- **10.0 – 14.99:** Moderate
- **0.0 – 9.99:** Needs Attention

Estimated ranking tiers based on Total SSI (`0–100`):
- **Industry Rank:** `≥ 80` Top 1% | `≥ 70` Top 5% | `≥ 60` Top 10% | `≥ 45` Top 25% | `< 45` Top 50%
- **Network Rank:** `≥ 70` Top 5% | `≥ 50` Top 15% | `≥ 40` Top 30% | `< 40` Top 50%

---

## 🎯 5. Official Sales Navigator Calibration (Ground Truth)

The scoring engine was calibrated directly against an official **LinkedIn Sales Navigator** SSI report extracted at the same timestamp as the user's LinkedIn data archive:

| Pillar | Official Name | Ground-Truth Score | Progress |
| :--- | :--- | :---: | :---: |
| **Pillar 1** | Establish your professional brand | **14.72** / 25.00 | 58.9% |
| **Pillar 2** | Find the right people | **6.10** / 25.00 | 24.4% |
| **Pillar 3** | Engage with insights | **9.50** / 25.00 | 38.0% |
| **Pillar 4** | Build relationships | **16.70** / 25.00 | 66.8% |
| **TOTAL** | **Consolidated Social Selling Index** | **47.02** / 100.00 | **Top 25%** |

---

## 📂 6. LinkedIn Export CSVs Used

Below is the complete list of files inspected inside your LinkedIn export package (all optional — missing files default safely to `0`):

| CSV File Pattern | Target Pillar(s) | Extracted Signals |
| :--- | :---: | :--- |
| `Profile.csv` | P1 | First/last name, headline length, summary character count |
| `Positions.csv` | P1 | Total work experiences and count of positions with descriptions |
| `Education.csv` | P1 | Academic background entries |
| `Skills.csv` | P1 | Total listed skills |
| `Certifications.csv` / `Projects.csv` | P1 | Credentials and portfolio projects |
| `Recommendations_Received.csv` / `Given.csv` | P1 | Social proof and peer endorsements |
| `Endorsement_Received_Info.csv` / `Rich_Media.csv` | P1 | Skill endorsements and uploaded media items |
| `Shares.csv` | P1, P3 | Original posts & reposts (30d, 90d, 365d, total) |
| `SearchQueries.csv` | P2 | Search query timestamps and frequency (30d, 90d, 365d, total) |
| `Invitations.csv` | P2 | `OUTGOING` vs. `INCOMING` connection requests (30d, 90d, total) |
| `Company Follows.csv` / `Member_Follows.csv` | P2 | Followed organizations and creators |
| `Reactions.csv` | P3 | Reactions given and breakdown by reaction type (`LIKE`, `PRAISE`, etc.) |
| `Comments.csv` | P3 | Comments written on posts (30d, 90d, 365d, total) |
| `Votes.csv` | P3 | Poll participation count |
| `Connections.csv` | P4 | First-degree network size, recent growth, and decision-maker title ratio |
| `messages.csv` | P4 | Message volume and unique `CONVERSATION ID` threads active in 90d |

---

## 📄 7. JSON Export Schema

Running with `--export-json report.json` generates a structured file containing three top-level keys:

```json
{
  "metadata": {
    "generated_at": "2026-11-02T17:30:00",
    "source": "/path/to/export.zip"
  },
  "ssi_result": {
    "total_score": 47.02,
    "industry_percentile": "Top 25% no seu setor",
    "network_percentile": "Top 30% na sua rede",
    "pillars": {
      "pillar_1": { "score": 14.72, "max_score": 25.0, "percentage": 58.9, "submetrics": [...] },
      "pillar_2": { "score": 6.10,  "max_score": 25.0, "percentage": 24.4, "submetrics": [...] },
      "pillar_3": { "score": 9.50,  "max_score": 25.0, "percentage": 38.0, "submetrics": [...] },
      "pillar_4": { "score": 16.70, "max_score": 25.0, "percentage": 66.8, "submetrics": [...] }
    },
    "metrics_summary": { "...raw extracted counts..." }
  },
  "diagnostic_report": {
    "headline_diagnostic": "...",
    "strengths": [...],
    "bottlenecks": [...],
    "actions": [...],
    "simulations": [...]
  }
}
```

---

## 🔒 8. Privacy & Data Protection (GDPR / LGPD)

- **100% Offline Execution:** This tool makes **zero** network requests.
- **Git Protection:** Personal export directories (`Dados/`, `dados/`, `data/`, `Descompilado/`) and `.zip` archives are excluded by `.gitignore` to prevent accidental commits of private LinkedIn archives.
