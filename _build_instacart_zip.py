"""
Build standalone zip for Instacart Refill Intelligence.
Includes data CSVs, notebook, HTML dashboard, utilities, and README.
"""
import zipfile, os, sys, json, copy, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_SRC = os.path.join(
    os.path.expanduser("~"),
    ".cache", "kagglehub", "datasets",
    "psparks", "instacart-market-basket-analysis", "versions", "1"
)
OUT_ZIP = os.path.join(ROOT, "instacart-refill-intelligence.zip")

CSVS = [
    "aisles.csv",
    "departments.csv",
    "order_products__prior.csv",
    "order_products__train.csv",
    "orders.csv",
    "products.csv",
]

# ── Patch notebook: replace kagglehub download with local data/ load ──

def patch_notebook():
    nb_path = os.path.join(ROOT, "notebooks", "13_instacart_refill_intelligence.ipynb")
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    patched = copy.deepcopy(nb)

    # Clear all outputs to keep the zip small
    for cell in patched["cells"]:
        if cell["cell_type"] == "code":
            cell["outputs"] = []
            cell["execution_count"] = None

    # Cell 1: remove kagglehub from pip install
    for cell in patched["cells"]:
        src = "".join(cell.get("source", []))
        if "pip install" in src and "kagglehub" in src:
            cell["source"] = ["!pip install -q pandas numpy matplotlib seaborn"]
            break

    # Cell 3: replace kagglehub download with local data/ path
    for cell in patched["cells"]:
        src = "".join(cell.get("source", []))
        if "kagglehub.dataset_download" in src:
            cell["source"] = [
                "# Load data from local data/ folder (included in this zip)\n",
                "import glob\n",
                "path = os.path.join(os.path.dirname(os.path.abspath('__file__')), 'data')\n",
                "print(f'Dataset path: {path}')\n",
                "\n",
                "csvs = glob.glob(os.path.join(path, '*.csv'))\n",
                "for f in sorted(csvs):\n",
                "    print(f'  {os.path.basename(f)}')\n",
            ]
            break

    return patched


def build_readme():
    return """# Instacart Refill Intelligence

A data analysis POC demonstrating three churn intelligence signals
from the Instacart Market Basket dataset (3.4M orders, 206K users).

## Contents

```
instacart-refill-intelligence/
├── README.md
├── data/                          # Instacart CSVs (~713 MB uncompressed)
│   ├── aisles.csv
│   ├── departments.csv
│   ├── order_products__prior.csv
│   ├── order_products__train.csv
│   ├── orders.csv
│   └── products.csv
├── 13_instacart_refill_intelligence.ipynb   # Analysis notebook
├── insight_utils.py                         # Shared utilities
└── instacart-refill-intelligence.html       # Dark-theme 3-tab dashboard
```

## Quick Start

### 1. View the Dashboard (no setup needed)
Open `instacart-refill-intelligence.html` in any browser.
All data is already baked into the HTML.

### 2. Run the Notebook

```bash
pip install pandas numpy matplotlib seaborn jupyter
jupyter notebook 13_instacart_refill_intelligence.ipynb
```

Run all cells. The notebook loads CSVs from the `data/` folder.
Expect ~2-5 minutes for the full run (32M-row dataset).

## Three Modules

| # | Module | What it finds |
|---|--------|---------------|
| 1 | **Replenishment Gap** | 148K users overdue on habitual products |
| 2 | **Reorder Abandonment** | 1.5M products dropped; 36% of users never return |
| 3 | **Basket Degradation** | 17.6K users losing department diversity |

## Data Source

Instacart Market Basket Analysis dataset by Jeremy Stanley,
available on Kaggle: https://www.kaggle.com/c/instacart-market-basket-analysis

## Built With

- Python 3.10+ / pandas / matplotlib / seaborn
- Tasknova dark-theme design system (HTML/CSS/JS)
"""


def main():
    print("Building standalone zip...")

    # Verify data exists
    for csv in CSVS:
        p = os.path.join(DATA_SRC, csv)
        if not os.path.exists(p):
            print(f"ERROR: Missing {p}")
            sys.exit(1)

    patched_nb = patch_notebook()

    prefix = "instacart-refill-intelligence"

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # Data CSVs
        for csv in CSVS:
            src = os.path.join(DATA_SRC, csv)
            sz = os.path.getsize(src) / 1e6
            print(f"  Adding data/{csv} ({sz:.1f} MB)...")
            zf.write(src, f"{prefix}/data/{csv}")

        # Patched notebook
        print("  Adding notebook (patched for local data)...")
        nb_json = json.dumps(patched_nb, indent=1, ensure_ascii=False)
        zf.writestr(f"{prefix}/13_instacart_refill_intelligence.ipynb", nb_json)

        # insight_utils.py
        print("  Adding insight_utils.py...")
        zf.write(
            os.path.join(ROOT, "notebooks", "insight_utils.py"),
            f"{prefix}/insight_utils.py",
        )

        # HTML dashboard
        print("  Adding HTML dashboard...")
        zf.write(
            os.path.join(ROOT, "instacart-refill-intelligence.html"),
            f"{prefix}/instacart-refill-intelligence.html",
        )

        # README
        print("  Adding README.md...")
        zf.writestr(f"{prefix}/README.md", build_readme())

    final_sz = os.path.getsize(OUT_ZIP) / 1e6
    print(f"\nDone: {OUT_ZIP}")
    print(f"Size: {final_sz:.1f} MB")


if __name__ == "__main__":
    main()
