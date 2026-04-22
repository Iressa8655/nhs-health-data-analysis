# ================================================================
# REAL NHS DATA -- A&E Full Year: April 2025 to March 2026
# Folder: NHS data\1. A&E Attendances and Emergency Admissions 2025-26
# 12 monthly CSV files downloaded from NHS England
# ================================================================
# Run with Ctrl+F5 in VS Code, or cell by cell with Shift+Enter
# ================================================================

# My general approach for any NHS dataset I haven't seen before:
#   1. Load it and look at the raw shape before touching anything
#   2. Ask: what does each row represent? One trust? One month?
#   3. Find the catch -- NHS data almost always has one (aggregate
#      rows, wrong units, a column that sounds like X but means Y)
#   4. Only then do the numbers

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os
import glob

# ── CONFIG ──────────────────────────────────────────────────────
# Keeping all file paths at the top so I only have to change
# one place if I move the data or rerun on a different machine.
DATA_FOLDER = (
    r"C:\Users\iress\Dropbox\Iressa's note\Career & Applications"
    r"\JOB\EDGE UK\NHS scenario runthrough"
    r"\1. A&E Attendances and Emergency Admissions 2025-26"
)
OUTPUT_DIR  = (
    r"C:\Users\iress\Dropbox\Iressa's note\Career & Applications"
    r"\JOB\EDGE UK\NHS scenario runthrough\output"
)
TARGET = 0.95     # 95% four-hour standard -- the headline political target

os.makedirs(OUTPUT_DIR, exist_ok=True)


# %%
# ================================================================
# STAGE 1 -- LOAD ALL 12 FILES AND COMBINE
# ================================================================
# NHS England publishes A&E data as one CSV per month, not as a
# single annual file. So I have 12 separate CSVs, one per month.
#
# Rather than loading each file manually (copy-paste 12 times),
# I use glob to find all CSVs in the folder automatically.
# That way the code still works if I add more months later.
# ================================================================

print("=" * 65)
print("STAGE 1 -- LOAD ALL 12 FILES AND COMBINE")
print("=" * 65)

# glob.glob returns a list of file paths matching the pattern.
# sorted() ensures April comes before August, etc.
csv_files = sorted(glob.glob(os.path.join(DATA_FOLDER, "*.csv")))
print(f"\n  Files found: {len(csv_files)}")
for f in csv_files:
    print(f"    {os.path.basename(f)}")

# I always print the file list first -- if glob finds 0 files it
# means the path is wrong, and I want to catch that immediately
# rather than getting a confusing error three stages later.

# Load each month into a list, then stack them all at once.
# pd.concat is cleaner than repeatedly appending to a DataFrame.
frames = []
for fpath in csv_files:
    monthly = pd.read_csv(fpath)
    frames.append(monthly)

raw = pd.concat(frames, ignore_index=True)
# ignore_index=True resets the row numbers (0, 1, 2 ...)
# without it you'd get duplicate index values from each file.

print(f"\n  Combined shape: {raw.shape[0]} rows x {raw.shape[1]} columns")

# First thing I check: what does the Period column actually contain?
# It should be "MSitAE-APRIL-2025" style strings -- one value per file.
# If I see something unexpected here I want to know before going further.
print("\n  Unique Period values (checking for surprises):")
for p in sorted(raw["Period"].unique()):
    print(f"    '{p}'")
# NOTE: when I first ran this I spotted that the TOTAL summary row
# has Period = "TOTAL" (or "Total" or "TOTAL " with a trailing space
# depending on the file). That caused a crash in Stage 2 the first time.
# Fixed by removing TOTAL rows BEFORE parsing dates -- see STEP B below.


# %%
# ================================================================
# STAGE 2 -- CLEAN & PREPARE
# ================================================================
# Five preparation steps. Order matters -- I learned the hard way
# that parsing dates before removing TOTAL rows crashes the script
# because "TOTAL".split("-") only gives one element, not three.
#
# STEP B first: remove TOTAL rows  (crash prevention)
# STEP A next:  parse Period string into a proper date column
# STEP C:       keep only Type 1 (major A&E) trusts
# STEP D:       calculate within_4hrs  (the file gives BREACHES)
# STEP E:       rename columns to something readable
# ================================================================

print("\n" + "=" * 65)
print("STAGE 2 -- CLEAN AND PREPARE")
print("=" * 65)

df = raw.copy()
# Working on a copy so I can always go back to raw if something
# goes wrong without re-running Stage 1.

# ── STEP B: Remove TOTAL summary rows ───────────────────────────
# Each monthly file appends one aggregate TOTAL row at the bottom.
# 12 files = 12 TOTAL rows to drop.
#
# Gotcha: the spelling is inconsistent across files --
#   "TOTAL", "TOTAL " (trailing space), "Total"
# Using .str.strip().str.upper() to catch all variants at once.
# Filtering on Period rather than Org Code because the Period
# column is what I'm about to parse -- I want it clean first.
before = len(df)
df = df[df["Period"].str.strip().str.upper() != "TOTAL"].copy()
print(f"\n  STEP B: Removed TOTAL rows: {before} --> {len(df)} rows")
# Expecting to remove exactly 12 rows (one per file).
# If more than 12 are removed something else matched -- worth checking.

# ── STEP A: Convert Period to date ──────────────────────────────
# The Period field looks like "MSitAE-APRIL-2025".
# pandas can't plot that on a time axis -- I need a real date.
#
# My approach: split on "-", take parts[1] (month name) and
# parts[2] (year), then build a first-of-month Timestamp.
#
# I briefly considered pd.to_datetime() but the "MSitAE-" prefix
# confuses it. Simpler to just split manually.

def period_to_date(period_str):
    """Convert 'MSitAE-APRIL-2025' --> Timestamp('2025-04-01')."""
    parts     = period_str.split("-")
    month_str = parts[1].capitalize()   # "APRIL" -> "April"
    year_str  = parts[2]                # "2025"
    return pd.Timestamp(f"01 {month_str} {year_str}")

df["month"] = df["Period"].apply(period_to_date)
print(f"  STEP A: Date range: {df['month'].min().strftime('%b %Y')} "
      f"to {df['month'].max().strftime('%b %Y')}")
# Good to check: should span exactly April 2025 to March 2026.

# ── STEP C: Filter to Type 1 trusts only ────────────────────────
# The combined file includes three types of A&E provider:
#   Type 1 = major emergency departments (resus bay, consultants 24/7)
#   Type 2 = single specialty (e.g. eye casualty, orthopaedic walk-in)
#   Other  = walk-in centres, urgent treatment centres
#
# The 95% four-hour target formally applies to Type 1 only.
# Including Types 2 and Other would dilute the analysis -- many of
# those departments see only minor cases and routinely hit 99%+,
# which would make the national picture look better than it is.
#
# Filtering on "A&E attendances Type 1 > 0" removes rows where the
# trust has no Type 1 activity at all (i.e. it's purely a walk-in).
before = len(df)
df = df[df["A&E attendances Type 1"] > 0].copy()
print(f"  STEP C: Filtered to Type 1 trusts: {before} --> {len(df)} rows")

# ── STEP D: Calculate within_4hrs ───────────────────────────────
# This is the key gotcha in NHS A&E data:
# The file gives "Attendances over 4hrs" (= BREACHES, patients who
# MISSED the target). It does NOT give "seen within 4hrs" directly.
#
# Formula: within_4hrs = total Type 1 attendances - those over 4hrs
#
# I always do this calculation explicitly and then check the result
# is never negative -- if it is, either the source data is wrong
# or I've mixed up columns.
df["total_type1"] = df["A&E attendances Type 1"]
df["over_4hrs"]   = df["Attendances over 4hrs Type 1"]
df["within_4hrs"] = df["total_type1"] - df["over_4hrs"]
df["perf_rate"]   = df["within_4hrs"] / df["total_type1"]

bad = df[df["within_4hrs"] < 0]
if bad.empty:
    print("  STEP D: PASS -- within_4hrs is never negative")
else:
    print(f"  STEP D: FLAG -- {len(bad)} rows where within_4hrs < 0 -- investigate")

# ── STEP E: Standardise column names ────────────────────────────
# "Org name" is fine for Excel but awkward to type repeatedly.
# Renaming to trust_name and org_code for the rest of the script.
df = df.rename(columns={"Org name": "trust_name", "Org Code": "org_code"})

print(f"\n  perf_rate range: {df['perf_rate'].min():.1%} to {df['perf_rate'].max():.1%}")
print(f"  Unique trusts across all months: {df['trust_name'].nunique()}")
print(f"  Months: {df['month'].nunique()}")
print(f"  Nulls remaining: {df.isnull().sum().sum()}")


# %%
# ================================================================
# STAGE 3 -- SENSE CHECK
# ================================================================
# I never skip this step, even when the data looks clean.
# In my experience NHS data tends to have at least one plausibility
# issue -- a miskeyed zero, an impossible value, a field that means
# something slightly different than you'd expect.
#
# Running structured checks now means any chart I produce later
# is based on verified numbers, which matters if I'm presenting
# findings to a clinical or operational audience.
# ================================================================

print("\n" + "=" * 65)
print("STAGE 3 -- SENSE CHECK")
print("=" * 65)

checks_passed = 0
checks_failed = 0

# Check A: logical impossibility -- can't have more breaches than attendances
# If over_4hrs > total_type1 then something is wrong with the source data.
bad = df[df["over_4hrs"] > df["total_type1"]]
if bad.empty:
    print("  PASS  over_4hrs never exceeds total_type1")
    checks_passed += 1
else:
    print(f"  FLAG  {len(bad)} rows where over_4hrs > total_type1")
    print(bad[["trust_name", "month", "total_type1", "over_4hrs"]].to_string())
    checks_failed += 1

# Check B: perf_rate must be a proportion (between 0 and 1)
# If it's outside this range it usually means someone stored it as a
# percentage (e.g. 75 instead of 0.75) -- a common data quality issue.
bad_rate = df[(df["perf_rate"] < 0) | (df["perf_rate"] > 1)]
if bad_rate.empty:
    print("  PASS  perf_rate always between 0 and 1")
    checks_passed += 1
else:
    print(f"  FLAG  {len(bad_rate)} rows with rate outside [0, 1]")
    checks_failed += 1

# Check C: statistical outliers using 2 SD threshold
# I chose 2 SD rather than 3 SD because I want to surface edge cases
# for investigation, not just catch extreme errors. A trust performing
# at 3 SD below the mean is likely already known to be in crisis --
# it's the 2 SD ones that might be early warning signals.
#
# Important caveat: a genuine performance collapse WILL look like an
# outlier statistically. That's not a reason to exclude it -- it's
# the most important finding. The FLAG here means "look at this",
# not "discard this".
mean_p   = df["perf_rate"].mean()
std_p    = df["perf_rate"].std()
outliers = df[
    (df["perf_rate"] < mean_p - 2*std_p) |
    (df["perf_rate"] > mean_p + 2*std_p)
]
if outliers.empty:
    print("  PASS  no statistical outliers in perf_rate (2 SD threshold)")
    checks_passed += 1
else:
    print(f"  FLAG  {len(outliers)} statistical outlier(s) -- worth investigating:")
    print(outliers[["trust_name", "month", "perf_rate"]].to_string())
    checks_failed += 1

# Check D: volume plausibility
# For a Type 1 A&E in England, I'd expect roughly 5,000–20,000
# attendances per month. Setting the bounds at 2,000 and 40,000
# gives plenty of headroom for smaller district generals and large
# London teaching hospitals respectively.
# Anything outside those bounds isn't necessarily wrong -- it might
# be a genuine outlier -- but I want to know about it.
low_vol  = df[df["total_type1"] < 2000]
high_vol = df[df["total_type1"] > 40000]
if low_vol.empty and high_vol.empty:
    print("  PASS  all Type 1 volumes look plausible (2,000–40,000 range)")
    checks_passed += 1
else:
    if not low_vol.empty:
        print(f"  FLAG  {len(low_vol)} rows with unusually low volume (<2,000)")
        print(low_vol[["trust_name", "month", "total_type1"]].to_string())
    if not high_vol.empty:
        print(f"  FLAG  {len(high_vol)} rows with unusually high volume (>40,000)")
        print(high_vol[["trust_name", "month", "total_type1"]].to_string())
    checks_failed += 1

print(f"\n  Sense checks: {checks_passed} passed, {checks_failed} flagged")


# %%
# ================================================================
# STAGE 4 -- SUMMARY METRICS
# ================================================================
# Two levels of summary:
#   (a) Full year aggregate -- one headline figure for 2025-26
#   (b) Monthly national performance -- how did each month compare?
#   (c) Latest month (March 2026) league table -- which trusts?
#
# The key methodological choice here is WEIGHTED average.
# A simple average would treat a 5,000-attendance district general
# the same as a 25,000-attendance teaching hospital. That's wrong --
# the teaching hospital has five times the patient exposure and
# should carry five times the weight in the national figure.
# ================================================================

print("\n" + "=" * 65)
print("STAGE 4 -- SUMMARY METRICS")
print("=" * 65)

# ── (a) Full year aggregate ──────────────────────────────────────
# Weighted performance = sum of all patients seen within 4hrs
# divided by sum of all Type 1 attendances across the year.
total_within   = df["within_4hrs"].sum()
total_all      = df["total_type1"].sum()
overall_perf   = total_within / total_all
total_breaches = int(df["over_4hrs"].sum())

print(f"\n  FULL YEAR (April 2025 – March 2026)")
print(f"  Overall 4-hour performance: {overall_perf:.1%}")
print(f"  National target:            {TARGET:.0%}")
print(f"  Gap:                        {overall_perf - TARGET:.1%}")
print(f"  Total breaches:             {total_breaches:,}")
print(f"  Trust-months analysed:      {len(df)}")

# ── (b) Monthly national performance ────────────────────────────
# Grouping by month and applying the same weighted formula to each.
# I'm using a lambda inside groupby.apply rather than agg() because
# I need to divide one column's sum by another column's sum --
# that's not a single-column operation, so agg() won't do it neatly.
monthly_nat = (
    df.groupby("month")
    .apply(lambda g: g["within_4hrs"].sum() / g["total_type1"].sum(), include_groups=False)
    .reset_index(name="nat_perf")
    .sort_values("month")
)

# Quick ASCII bar chart in the terminal -- useful for a fast eyeball
# of the seasonal pattern before committing to a full matplotlib chart.
print(f"\n  Monthly national 4-hour performance:")
for _, row in monthly_nat.iterrows():
    bar    = "█" * int(row["nat_perf"] * 40)
    flag   = " ▼ BELOW TARGET" if row["nat_perf"] < TARGET else ""
    print(f"    {row['month'].strftime('%b %Y')}  {row['nat_perf']:.1%}  {bar}{flag}")

# ── (c) Latest month league table ───────────────────────────────
# Sorted worst to best so the most urgent cases are at the top.
latest_month = df["month"].max()
df_latest    = df[df["month"] == latest_month].copy()
trust_perf   = (
    df_latest[["trust_name", "total_type1", "within_4hrs", "over_4hrs", "perf_rate"]]
    .sort_values("perf_rate")
    .reset_index(drop=True)
)

n_below        = (trust_perf["perf_rate"] < TARGET).sum()
latest_overall = df_latest["within_4hrs"].sum() / df_latest["total_type1"].sum()
print(f"\n  {latest_month.strftime('%B %Y').upper()} -- {n_below} of {len(trust_perf)} "
      f"trusts below {TARGET:.0%} target  (national: {latest_overall:.1%})")

print(f"\n  Bottom 10 (worst performers in {latest_month.strftime('%B %Y')}):")
for _, row in trust_perf.head(10).iterrows():
    gap      = row["perf_rate"] - TARGET
    breaches = int(row["over_4hrs"])
    print(f"    {row['perf_rate']:.1%}  {row['trust_name']:<55}  "
          f"({breaches:,} breaches, {gap:.1%} vs target)")

print(f"\n  Top 5 (best performers in {latest_month.strftime('%B %Y')}):")
for _, row in trust_perf.tail(5).iterrows():
    gap      = row["perf_rate"] - TARGET
    breaches = int(row["over_4hrs"])
    sign     = "+" if gap >= 0 else ""
    print(f"    {row['perf_rate']:.1%}  {row['trust_name']:<55}  "
          f"({breaches:,} breaches, {sign}{gap:.1%} vs target)")


# %%
# ================================================================
# STAGE 5 -- TREND ANALYSIS
# ================================================================
# This is where having 12 months of data really pays off.
# A single snapshot tells you who's struggling right now.
# Trend tells you who's getting worse -- which is the early
# warning signal that matters for intervention planning.
#
# My approach: split the year into two halves (H1 and H2)
# and compare each trust's weighted performance between them.
#
# Why halves rather than monthly regression?
# With 12 data points per trust a linear regression would be
# technically possible but hard to explain to a non-technical
# audience. "Performance fell 4 percentage points between the
# first and second half of the year" is immediately actionable.
# A regression slope of -0.003 is not.
#
# Threshold: I flagged a change of >2 percentage points (0.02)
# as meaningful. Below that it's within normal month-to-month
# variation and not worth escalating.
# ================================================================

print("\n" + "=" * 65)
print("STAGE 5 -- TREND ANALYSIS")
print("=" * 65)

# ── (a) National trend summary ───────────────────────────────────
print("\n  (a) National monthly descriptive stats:")
print(f"  Best month:  {monthly_nat.loc[monthly_nat['nat_perf'].idxmax(), 'month'].strftime('%B %Y')}  "
      f"({monthly_nat['nat_perf'].max():.1%})")
print(f"  Worst month: {monthly_nat.loc[monthly_nat['nat_perf'].idxmin(), 'month'].strftime('%B %Y')}  "
      f"({monthly_nat['nat_perf'].min():.1%})")
print(f"  Year-on-year range: {monthly_nat['nat_perf'].max() - monthly_nat['nat_perf'].min():.1%}")
months_above = (monthly_nat["nat_perf"] >= TARGET).sum()
print(f"  Months meeting {TARGET:.0%} target: {months_above} of {len(monthly_nat)}")

# ── (b) Trust-level H1 vs H2 comparison ─────────────────────────
sorted_months = sorted(df["month"].unique())
h1_months     = sorted_months[:6]    # Apr – Sep 2025
h2_months     = sorted_months[6:]    # Oct 2025 – Mar 2026

# Note: winter months are almost always worse than summer months
# for A&E -- so any trust that's worsening in H2 is worsening
# on top of the seasonal headwind. That makes the deterioration
# more significant, not less.

def half_perf(sub_df, months):
    """Return weighted performance per trust for a given set of months."""
    g = sub_df[sub_df["month"].isin(months)]
    return g.groupby("trust_name").apply(
        lambda x: x["within_4hrs"].sum() / x["total_type1"].sum(),
        include_groups=False
    ).rename("perf")

h1 = half_perf(df, h1_months).reset_index()
h2 = half_perf(df, h2_months).reset_index()
h1.columns = ["trust_name", "h1_perf"]
h2.columns = ["trust_name", "h2_perf"]

# Inner merge: only keep trusts present in both halves.
# A trust that opened or closed mid-year would give a misleading
# change score, so it's safer to exclude those edge cases.
trend_df = h1.merge(h2, on="trust_name")
trend_df["change"] = trend_df["h2_perf"] - trend_df["h1_perf"]
# positive change = improving, negative = worsening

trend_df["direction"] = trend_df["change"].apply(
    lambda c: "WORSENING" if c < -0.02 else ("IMPROVING" if c > 0.02 else "STABLE")
)

n_worse  = (trend_df["direction"] == "WORSENING").sum()
n_better = (trend_df["direction"] == "IMPROVING").sum()
n_stable = (trend_df["direction"] == "STABLE").sum()

h1_label = f"{pd.Timestamp(h1_months[0]).strftime('%b')}–{pd.Timestamp(h1_months[-1]).strftime('%b %Y')}"
h2_label = f"{pd.Timestamp(h2_months[0]).strftime('%b')}–{pd.Timestamp(h2_months[-1]).strftime('%b %Y')}"

print(f"\n  (b) Trust trend: {h1_label} vs {h2_label}")
print(f"  Worsening (>2 pp decline):  {n_worse} trusts")
print(f"  Improving (>2 pp gain):     {n_better} trusts")
print(f"  Stable (+/- 2 pp):          {n_stable} trusts")

worst_trend = trend_df[trend_df["direction"] == "WORSENING"].sort_values("change").head(5)
if not worst_trend.empty:
    print(f"\n  Top 5 MOST WORSENING trusts:")
    for _, row in worst_trend.iterrows():
        print(f"    {row['trust_name']:<55}  "
              f"{row['h1_perf']:.1%} --> {row['h2_perf']:.1%}  "
              f"(change: {row['change']:+.1%})")

best_trend = trend_df[trend_df["direction"] == "IMPROVING"].sort_values("change", ascending=False).head(5)
if not best_trend.empty:
    print(f"\n  Top 5 MOST IMPROVING trusts:")
    for _, row in best_trend.iterrows():
        print(f"    {row['trust_name']:<55}  "
              f"{row['h1_perf']:.1%} --> {row['h2_perf']:.1%}  "
              f"(change: {row['change']:+.1%})")


# %%
# ================================================================
# STAGE 6 -- VISUALISE (3 charts)
# ================================================================
# Chart design decisions:
#
# Chart 1: Line chart for national trend.
#   -- I added a red shaded area below the 95% line so it's
#      immediately obvious in a presentation that the standard
#      is being missed every single month.
#
# Chart 2: Horizontal bar chart for trust league table.
#   -- Horizontal not vertical: trust names are long and vertical
#      bars would require 45-degree labels that are hard to read.
#   -- Showing bottom 15 + top 5 only. All 130 trusts on one chart
#      is unreadable. I chose 15+5 to give enough context without
#      noise -- anyone presenting this to a board would do the same.
#
# Chart 3: Side-by-side bars for H1 vs H2 worst-trend trusts.
#   -- This makes the deterioration visually obvious even to
#      someone who doesn't read numbers carefully.
# ================================================================

print("\n" + "=" * 65)
print("STAGE 6 -- VISUALISE")
print("=" * 65)

# ── Chart 1: National monthly trend ─────────────────────────────
fig1, ax1 = plt.subplots(figsize=(11, 5))

ax1.plot(
    monthly_nat["month"], monthly_nat["nat_perf"],
    marker="o", linewidth=2, color="#1f77b4", markersize=7,
    label="National performance"
)
ax1.axhline(TARGET, color="red", linestyle="--", linewidth=1.5,
            label=f"{TARGET:.0%} target")

# Red shading below the target line -- makes the miss immediately visible
ax1.fill_between(
    monthly_nat["month"], monthly_nat["nat_perf"], TARGET,
    where=(monthly_nat["nat_perf"] < TARGET),
    alpha=0.15, color="red", label="Below target"
)

ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0%}"))
ax1.set_title("National A&E 4-Hour Performance: April 2025 – March 2026",
              fontweight="bold")
ax1.set_ylabel("% seen within 4 hours (Type 1)")
ax1.set_xlabel("")
ax1.tick_params(axis="x", rotation=30)
ax1.legend(loc="lower left")
ax1.set_ylim(0.5, 1.0)
# y-axis starts at 50% not 0% -- starting at 0 would make the
# variation look tiny and flatten out the seasonal pattern.
plt.tight_layout()

chart1_path = os.path.join(OUTPUT_DIR, "ae_national_trend.png")
plt.savefig(chart1_path, dpi=150, bbox_inches="tight")
print(f"\n  Chart 1 saved --> {chart1_path}")
plt.show()

# ── Chart 2: Trust league table (latest month) ──────────────────
# Deliberately not showing all trusts -- 130 bars is noise, not insight.
# The bottom 15 shows the trusts that need attention.
# The top 5 provides contrast and shows the spread is genuine.
bottom15 = trust_perf.head(15)
top5     = trust_perf.tail(5)
chart_df = pd.concat([bottom15, top5]).drop_duplicates()

fig2, ax2 = plt.subplots(figsize=(11, 10))

colors = ["#d73027" if p < TARGET else "#1a9850" for p in chart_df["perf_rate"]]
# Red for below-target, green for above -- traffic light is universally
# understood and doesn't need a legend to interpret.

ax2.barh(
    chart_df["trust_name"], chart_df["perf_rate"],
    color=colors, edgecolor="white", height=0.7,
)
ax2.axvline(TARGET, color="black", linestyle="--", linewidth=1.5,
            label=f"{TARGET:.0%} target")
ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0%}"))

# Label each bar with its value -- saves the reader having to
# trace a line from bar to axis, especially for bars near the middle.
for i, (_, row) in enumerate(chart_df.iterrows()):
    ax2.text(
        row["perf_rate"] - 0.005, i,
        f"{row['perf_rate']:.1%}",
        va="center", ha="right",
        color="white", fontweight="bold", fontsize=8,
    )

ax2.set_title(
    f"{n_below} of {len(trust_perf)} Type 1 A&E trusts below {TARGET:.0%} target "
    f"in {latest_month.strftime('%B %Y')}\n"
    f"(showing 15 worst + 5 best | national: {latest_overall:.1%})",
    fontsize=10, fontweight="bold", pad=12,
)
ax2.set_xlabel("4-hour performance rate")
ax2.set_xlim(0, 1.05)
ax2.legend(loc="lower right")
plt.tight_layout()

chart2_path = os.path.join(OUTPUT_DIR, "ae_trust_league_march2026.png")
plt.savefig(chart2_path, dpi=150, bbox_inches="tight")
print(f"  Chart 2 saved --> {chart2_path}")
plt.show()

# ── Chart 3: Worst-trend trusts (H1 vs H2) ──────────────────────
# Side-by-side bars make the direction of change immediately obvious.
# Blue = H1 (summer), red = H2 (winter). The colour choice is
# intentional: winter pressure is conventionally red in NHS reporting.
top10_worse = trend_df[trend_df["direction"] == "WORSENING"].sort_values("change").head(10)

if not top10_worse.empty:
    fig3, ax3 = plt.subplots(figsize=(11, 7))

    y         = range(len(top10_worse))
    bar_width = 0.35

    ax3.barh(
        [i + bar_width/2 for i in y], top10_worse["h1_perf"],
        height=bar_width, color="#74add1", label=h1_label
    )
    ax3.barh(
        [i - bar_width/2 for i in y], top10_worse["h2_perf"],
        height=bar_width, color="#d73027", label=h2_label
    )
    ax3.axvline(TARGET, color="black", linestyle="--", linewidth=1.2,
                label=f"{TARGET:.0%} target")

    ax3.set_yticks(list(y))
    ax3.set_yticklabels(top10_worse["trust_name"], fontsize=8)
    ax3.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0%}"))
    ax3.set_title(
        f"Top 10 Most Worsening Trusts: {h1_label} vs {h2_label}\n"
        f"(sorted by biggest decline -- these are early warning signals)",
        fontsize=10, fontweight="bold", pad=12
    )
    ax3.set_xlabel("4-hour performance rate")
    ax3.legend(loc="lower right")
    plt.tight_layout()

    chart3_path = os.path.join(OUTPUT_DIR, "ae_worst_trend_trusts.png")
    plt.savefig(chart3_path, dpi=150, bbox_inches="tight")
    print(f"  Chart 3 saved --> {chart3_path}")
    plt.show()
else:
    print("  No worsening trusts to plot in Chart 3.")


# %%
# ================================================================
# STAGE 7 -- WRITTEN SUMMARY
# ================================================================
# I deliberately limit the recommendations to 3 points.
# The temptation is to flag every trust below target, but that's
# not prioritisation -- it's just a longer list.
# Three clear priorities are actionable. Ten are not.
# ================================================================

print("\n" + "=" * 65)
print("STAGE 7 -- WRITTEN SUMMARY")
print("=" * 65)

worst  = trust_perf.iloc[0]
second = trust_perf.iloc[1]
third  = trust_perf.iloc[2]

# Threshold of 80% for "persistently struggling" -- this is well below
# the 95% target, so it captures trusts with systemic problems rather
# than those just missing by a small margin.
persist_below80 = (trust_perf["perf_rate"] < 0.80).sum()

if not worst_trend.empty:
    worst_trend_trust = worst_trend.iloc[0]
    wtt_name   = worst_trend_trust["trust_name"]
    wtt_change = worst_trend_trust["change"]
else:
    wtt_name   = "N/A"
    wtt_change = 0.0

summary = f"""
HEADLINE FINDING
Analysis of NHS England A&E data for April 2025 – March 2026 (12 months)
shows England's Type 1 A&E departments are consistently missing the 95%
four-hour standard. Across the full year, the weighted national performance
was {overall_perf:.1%} -- {overall_perf - TARGET:.1%} below target -- with a cumulative
{total_breaches:,} patients waiting more than 4 hours in Type 1 departments.

In the most recent month ({latest_month.strftime('%B %Y')}), {n_below} of {len(trust_perf)} trusts
are below the 95% target. National performance stands at {latest_overall:.1%}.

TREND
No month in 2025-26 met the 95% target.
Best month:  {monthly_nat.loc[monthly_nat['nat_perf'].idxmax(), 'month'].strftime('%B %Y')} ({monthly_nat['nat_perf'].max():.1%})
Worst month: {monthly_nat.loc[monthly_nat['nat_perf'].idxmin(), 'month'].strftime('%B %Y')} ({monthly_nat['nat_perf'].min():.1%})
{n_worse} trusts deteriorated by more than 2 percentage points
between the first half ({h1_label}) and second half ({h2_label}).

TOP 3 PRIORITIES FOR MARCH 2026
1. {worst['trust_name']}
   Performance: {worst['perf_rate']:.1%}  |  Breaches: {int(worst['over_4hrs']):,}  |  Gap: {worst['perf_rate'] - TARGET:.1%}

2. {second['trust_name']}
   Performance: {second['perf_rate']:.1%}  |  Breaches: {int(second['over_4hrs']):,}  |  Gap: {second['perf_rate'] - TARGET:.1%}

3. {third['trust_name']}
   Performance: {third['perf_rate']:.1%}  |  Breaches: {int(third['over_4hrs']):,}  |  Gap: {third['perf_rate'] - TARGET:.1%}

RECOMMENDATIONS
1. Commission an immediate operational review at {worst['trust_name']}.
   At {worst['perf_rate']:.1%}, this is the highest patient-harm risk trust
   in the current dataset and the most urgent priority.

2. Investigate the {persist_below80} trusts persistently below 80%
   performance. These are likely facing systemic capacity pressures --
   beds, staffing levels, ambulance handover delays -- that cannot be
   resolved with short-term operational support alone.

3. Monitor the {n_worse} trusts with a worsening trajectory in H2.
   The largest single decline was at {wtt_name}
   ({wtt_change:+.1%} change between {h1_label} and {h2_label}).
   Deterioration in winter is expected, but a decline of this magnitude
   warrants an early conversation before next winter.

DATA QUALITY NOTE
Analysis restricted to Type 1 (major A&E) departments only
({df['trust_name'].nunique()} trusts across 12 months).
Type 2 and Type 3 organisations excluded as the 95% four-hour standard
applies primarily to Type 1. Monthly totals are weighted by attendance
volume so larger trusts carry proportionally more weight in the national
figure. Source: NHS England A&E Attendances and Emergency Admissions
2025-26, published monthly at england.nhs.uk.
"""

print(summary)

print("=" * 65)
print("Analysis complete. Charts saved to:", OUTPUT_DIR)
print("=" * 65)
