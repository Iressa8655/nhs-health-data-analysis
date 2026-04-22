# ================================================================
# REAL NHS DATA -- A&E March 2026
# File: March-2026-CSV-G49lw.csv (downloaded from NHS England)
# ================================================================
# Run with Ctrl+F5 in VS Code, or cell by cell with Shift+Enter
# ================================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

DATA_FILE  = (
    r"C:\Users\iress\Dropbox\Iressa's note\Career & Applications"
    r"\JOB\EDGE UK\NHS scenario runthrough"
    r"\1. A&E Attendances and Emergency Admissions 2025-26"
    r"\March-2026-CSV-G49lw.csv"
)
OUTPUT_DIR = (
    r"C:\Users\iress\Dropbox\Iressa's note\Career & Applications"
    r"\JOB\EDGE UK\NHS scenario runthrough\output"
)
TARGET     = 0.95

os.makedirs(OUTPUT_DIR, exist_ok=True)


# %%
# ================================================================
# STAGE 1 -- LOAD AND LOOK
# ================================================================

print("=" * 60)
print("STAGE 1 -- LOAD AND LOOK")
print("=" * 60)

df = pd.read_csv(DATA_FILE)

print(f"\n-- Shape: {df.shape[0]} rows x {df.shape[1]} columns --")
print("\n-- Column names --")
for i, col in enumerate(df.columns):
    print(f"  [{i:2d}]  {col}")

print("\n-- First 3 rows --")
print(df.head(3).to_string())

print("\n-- Last 2 rows (check for TOTAL row) --")
print(df.tail(2).to_string())

print("\n-- Missing values --")
print(df.isnull().sum().to_string())

print("\n-- Unique values in Period column --")
print(df["Period"].unique())
# Expect: just one value "MSitAE-MARCH-2026"
# This is ONE month only -- no trend analysis possible


# %%
# ================================================================
# STAGE 2 -- CLEAN & PREPARE
# ================================================================
# The real NHS file needs 3 preparation steps before analysis:
#
# STEP A: Remove the TOTAL summary row at the bottom
# STEP B: Filter to Type 1 (major A&E) trusts only
#         -- many rows are walk-in centres with 0 in Type 1
# STEP C: Calculate within_4hrs = Type1_total - Type1_over4hrs
#         -- the file gives BREACHES (over 4hrs), not WITHIN 4hrs
# ================================================================

print("\n" + "=" * 60)
print("STAGE 2 -- CLEAN AND PREPARE")
print("=" * 60)

# STEP A: Remove the TOTAL summary row
before = len(df)
df = df[df["Org Code"] != "TOTAL"]
print(f"\n  Removed TOTAL row: {before} --> {len(df)} rows")

# STEP B: Filter to Type 1 trusts only (real A&E departments)
# Type 1 = major emergency departments (resus, doctors 24/7)
# Type 2 = single specialty (e.g. eye hospitals)
# Type 3 = walk-in centres, urgent treatment centres
# We focus on Type 1 because that's what the 4-hour target applies to.
before = len(df)
df = df[df["A&E attendances Type 1"] > 0].copy()
print(f"  Filtered to Type 1 trusts: {before} --> {len(df)} rows")
print(f"  These are the {len(df)} major A&E departments in England")

# STEP C: Calculate within_4hrs
# The file gives "Attendances over 4hrs Type 1" (= breaches)
# We need: seen within 4hrs = total Type 1 - those over 4hrs
df["total_type1"]   = df["A&E attendances Type 1"]
df["over_4hrs"]     = df["Attendances over 4hrs Type 1"]
df["within_4hrs"]   = df["total_type1"] - df["over_4hrs"]
df["perf_rate"]     = df["within_4hrs"] / df["total_type1"]

# Rename for clarity
df = df.rename(columns={"Org name": "trust_name"})

print(f"\n  Calculated within_4hrs = total_type1 - over_4hrs")
print(f"  perf_rate range: {df['perf_rate'].min():.1%} to {df['perf_rate'].max():.1%}")

# Quick check: any impossible values?
bad = df[df["within_4hrs"] < 0]
if bad.empty:
    print("  PASS  within_4hrs is never negative")
else:
    print(f"  FLAG  {len(bad)} rows where within_4hrs is negative -- investigate")
    print(bad[["trust_name", "total_type1", "over_4hrs", "within_4hrs"]].to_string())

print(f"\n  Nulls remaining: {df.isnull().sum().sum()}")


# %%
# ================================================================
# STAGE 3 -- SENSE CHECK
# ================================================================

print("\n" + "=" * 60)
print("STAGE 3 -- SENSE CHECK")
print("=" * 60)

checks_passed = 0
checks_failed = 0

# Check A: over_4hrs must never exceed total_type1
bad = df[df["over_4hrs"] > df["total_type1"]]
if bad.empty:
    print("  PASS  over_4hrs never exceeds total_type1")
    checks_passed += 1
else:
    print(f"  FLAG  {len(bad)} rows where over_4hrs > total_type1")
    print(bad[["trust_name", "total_type1", "over_4hrs"]].to_string())
    checks_failed += 1

# Check B: perf_rate between 0 and 1
bad_rate = df[(df["perf_rate"] < 0) | (df["perf_rate"] > 1)]
if bad_rate.empty:
    print("  PASS  perf_rate is always between 0 and 1")
    checks_passed += 1
else:
    print(f"  FLAG  {len(bad_rate)} rows with rate outside 0-1")
    checks_failed += 1

# Check C: statistical outliers (> 2 SD from mean)
mean_p   = df["perf_rate"].mean()
std_p    = df["perf_rate"].std()
outliers = df[(df["perf_rate"] < mean_p - 2*std_p) | (df["perf_rate"] > mean_p + 2*std_p)]
if outliers.empty:
    print("  PASS  no statistical outliers in perf_rate")
    checks_passed += 1
else:
    print(f"  FLAG  {len(outliers)} statistical outlier(s):")
    print(outliers[["trust_name", "perf_rate"]].to_string())
    checks_failed += 1

# Check D: attendance volume (expect 5,000-35,000 for major trusts in a month)
low_vol  = df[df["total_type1"] < 2000]
high_vol = df[df["total_type1"] > 40000]
if low_vol.empty and high_vol.empty:
    print("  PASS  all Type 1 volumes look plausible (2,000-40,000 range)")
    checks_passed += 1
else:
    if not low_vol.empty:
        print(f"  FLAG  {len(low_vol)} trusts with unusually low Type 1 volume (<2,000)")
        print(low_vol[["trust_name", "total_type1"]].to_string())
    if not high_vol.empty:
        print(f"  FLAG  {len(high_vol)} trusts with unusually high Type 1 volume (>40,000)")
        print(high_vol[["trust_name", "total_type1"]].to_string())
    checks_failed += 1

print(f"\n  Sense checks: {checks_passed} passed, {checks_failed} flagged")


# %%
# ================================================================
# STAGE 4 -- SUMMARY METRICS
# ================================================================

print("\n" + "=" * 60)
print("STAGE 4 -- SUMMARY METRICS")
print("=" * 60)

# Overall weighted performance
# (weighted: large trust counts more than small trust)
overall_perf = df["within_4hrs"].sum() / df["total_type1"].sum()
total_breaches = int(df["over_4hrs"].sum())
print(f"\n  Overall 4-hour performance (March 2026): {overall_perf:.1%}")
print(f"  National target:                          {TARGET:.0%}")
print(f"  Gap:                                      {overall_perf - TARGET:.1%}")
print(f"  Total breaches this month:                {total_breaches:,}")
print(f"  Trusts analysed:                          {len(df)}")

# League table: ranked worst to best
trust_perf = (
    df[["trust_name", "total_type1", "within_4hrs", "over_4hrs", "perf_rate"]]
    .sort_values("perf_rate")
    .reset_index(drop=True)
)

n_below = (trust_perf["perf_rate"] < TARGET).sum()
print(f"\n  Trusts below {TARGET:.0%} target: {n_below} of {len(trust_perf)}")

print(f"\n  Bottom 10 (worst performers):")
for _, row in trust_perf.head(10).iterrows():
    gap      = row["perf_rate"] - TARGET
    breaches = int(row["over_4hrs"])
    print(f"    {row['perf_rate']:.1%}  {row['trust_name']:<55}  ({breaches:,} breaches, {gap:.1%} vs target)")

print(f"\n  Top 5 (best performers):")
for _, row in trust_perf.tail(5).iterrows():
    gap      = row["perf_rate"] - TARGET
    breaches = int(row["over_4hrs"])
    sign     = "+" if gap >= 0 else ""
    print(f"    {row['perf_rate']:.1%}  {row['trust_name']:<55}  ({breaches:,} breaches, {sign}{gap:.1%} vs target)")


# %%
# ================================================================
# STAGE 5 -- TREND ANALYSIS
# ================================================================
# Only one month of data in this file, so no 6-month trend possible.
# To do trend analysis, download the TIME SERIES file from the same
# NHS England page: "Monthly A&E Time Series March 2026" (XLS, 433KB)
# That file has all months back to 2010 in one spreadsheet.
# ================================================================

print("\n" + "=" * 60)
print("STAGE 5 -- TREND ANALYSIS")
print("=" * 60)
print("\n  Only one month in this file (March 2026).")
print("  For trend analysis, download the time series file from:")
print("  NHS England > A&E Waiting Times > Monthly A&E Time Series March 2026")
print("\n  Descriptive stats for this month instead:")
print(f"  Mean performance:   {df['perf_rate'].mean():.1%}")
print(f"  Median performance: {df['perf_rate'].median():.1%}")
print(f"  Std deviation:      {df['perf_rate'].std():.1%}")
print(f"  Min:                {df['perf_rate'].min():.1%}  ({df.loc[df['perf_rate'].idxmin(), 'trust_name']})")
print(f"  Max:                {df['perf_rate'].max():.1%}  ({df.loc[df['perf_rate'].idxmax(), 'trust_name']})")


# %%
# ================================================================
# STAGE 6 -- VISUALISE
# ================================================================
# Showing top 20 worst + best -- 130 trusts would be unreadable.
# In a real submission you'd show the most relevant subset.
# ================================================================

print("\n" + "=" * 60)
print("STAGE 6 -- VISUALISE")
print("=" * 60)

# Show bottom 15 (worst) + top 5 (best) for a readable chart
bottom15 = trust_perf.head(15)
top5     = trust_perf.tail(5)
chart_df = pd.concat([bottom15, top5]).drop_duplicates()

fig, ax = plt.subplots(figsize=(11, 10))

colors = ["#d73027" if p < TARGET else "#1a9850" for p in chart_df["perf_rate"]]

ax.barh(
    chart_df["trust_name"],
    chart_df["perf_rate"],
    color=colors, edgecolor="white", height=0.7,
)

ax.axvline(TARGET, color="black", linestyle="--", linewidth=1.5, label=f"{TARGET:.0%} target")

ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0%}"))

for i, (_, row) in enumerate(chart_df.iterrows()):
    ax.text(
        row["perf_rate"] - 0.005, i,
        f"{row['perf_rate']:.1%}",
        va="center", ha="right",
        color="white", fontweight="bold", fontsize=8,
    )

n_below = (trust_perf["perf_rate"] < TARGET).sum()
ax.set_title(
    f"{n_below} of {len(trust_perf)} Type 1 A&E trusts below {TARGET:.0%} target in March 2026\n"
    f"(showing 15 worst + 5 best | overall performance: {overall_perf:.1%})",
    fontsize=10, fontweight="bold", pad=12,
)
ax.set_xlabel("4-hour performance rate")
ax.set_xlim(0, 1.05)
ax.legend(loc="lower right")
plt.tight_layout()

chart_path = os.path.join(OUTPUT_DIR, "real_ae_march2026.png")
plt.savefig(chart_path, dpi=150, bbox_inches="tight")
print(f"\n  Chart saved --> {chart_path}")
plt.show()


# %%
# ================================================================
# STAGE 7 -- WRITTEN SUMMARY
# ================================================================

print("\n" + "=" * 60)
print("STAGE 7 -- WRITTEN SUMMARY")
print("=" * 60)

worst  = trust_perf.iloc[0]
second = trust_perf.iloc[1]
third  = trust_perf.iloc[2]

summary = f"""
HEADLINE FINDING
In March 2026, {n_below} of {len(trust_perf)} Type 1 A&E departments in England
are performing below the 95% 4-hour standard, with an overall weighted
performance of {overall_perf:.1%} -- {overall_perf - TARGET:.1%} below the national target.
A total of {total_breaches:,} patients waited more than 4 hours in Type 1 departments
this month alone.

TOP 3 PRIORITIES
1. {worst['trust_name']}
   Performance: {worst['perf_rate']:.1%}  |  Breaches: {int(worst['over_4hrs']):,}  |  Gap: {worst['perf_rate'] - TARGET:.1%}

2. {second['trust_name']}
   Performance: {second['perf_rate']:.1%}  |  Breaches: {int(second['over_4hrs']):,}  |  Gap: {second['perf_rate'] - TARGET:.1%}

3. {third['trust_name']}
   Performance: {third['perf_rate']:.1%}  |  Breaches: {int(third['over_4hrs']):,}  |  Gap: {third['perf_rate'] - TARGET:.1%}

RECOMMENDATIONS
- Commission an immediate operational review at {worst['trust_name']}.
  At {worst['perf_rate']:.1%}, performance is {TARGET - worst['perf_rate']:.1%} below the national target --
  the highest patient harm risk in this dataset.
- Investigate the {n_below} trusts persistently below 80% performance.
  These represent systemic rather than temporary pressures and likely
  require structural capacity intervention, not short-term support.

DATA QUALITY NOTE
Analysis restricted to Type 1 (major A&E) departments only ({len(df)} trusts).
Type 2 and Type 3 organisations excluded as the 4-hour standard applies
primarily to Type 1. Single-month snapshot -- trend analysis requires the
NHS England monthly time series file.
"""
print(summary)

print("=" * 60)
print("Analysis complete. Chart saved to:", OUTPUT_DIR)
print("=" * 60)
