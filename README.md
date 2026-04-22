# Real-World Health Data Analysis

Exploratory analyses of publicly available NHS England datasets. Each folder is a self-contained project with its own data pipeline, findings, and charts.

All data is sourced from **NHS England's open statistics portal**:  
https://www.england.nhs.uk/statistics/statistical-work-areas/

---

## Projects

| # | Dataset | Status | Key question |
|---|---|---|---|
| [01](./01_ae_attendances/) | A&E Attendances and Emergency Admissions | ✅ Complete | How is England performing against the 95% four-hour A&E standard? |
| [02](./02_rtt_waiting_times/) | Referral to Treatment (RTT) Waiting Times | 🔄 In progress | Which specialties have the longest waits, and is the backlog improving? |
| [03](./03_ambulance_quality/) | Ambulance Quality Indicators | 📋 Planned | Are ambulance response times and hospital handover delays improving? |
| [04](./04_discharge_delays/) | Discharge Delays | 📋 Planned | How much of the A&E crisis is driven by patients stuck waiting for discharge? |
| [05](./05_cancer_waiting_times/) | Cancer Waiting Times | 📋 Planned | How many cancer patients are waiting beyond the 62-day target? |

---

## 01 — A&E Attendances (Complete)

**Period:** April 2025 to March 2026  
**Scope:** 125 Type 1 (major, consultant-led) emergency departments in England

### Headline findings

- National 4-hour performance: **60.5%** against a 95% target
- **7.1 million patients** waited more than 4 hours across the year
- **120 of 121** trusts below target in March 2026
- The monthly performance line is almost **completely flat** across the year — this is a structural, year-round problem, not a seasonal winter spike
- **45 trusts worsening** between first and second half of the year; only 15 improving
- **Princess Alexandra Hospital (Harlow)** achieved the largest improvement nationally: +10.6 percentage points through winter

![National A&E trend](./01_ae_attendances/output/ae_national_trend.png)

![Trust league table](./01_ae_attendances/output/ae_trust_league_march2026.png)

![Worst trend trusts](./01_ae_attendances/output/ae_worst_trend_trusts.png)

→ [Full findings and analysis](./01_ae_attendances/FINDINGS.md)  
→ [Analysis script](./01_ae_attendances/real_nhs_ae_full_year.py)

---

## 02 — RTT Waiting Times (In progress)

**Referral to Treatment** measures how long patients wait from GP referral to starting treatment.  
The standard is **92% of patients treated within 18 weeks**.

Questions this analysis will answer:
- Which specialties have the highest proportion of patients waiting over 18 weeks?
- How has the backlog changed over time?
- Are there trusts showing genuine improvement — and what are they doing differently?

**Data source:** https://www.england.nhs.uk/statistics/statistical-work-areas/rtt-waiting-times/

---

## 03 — Ambulance Quality Indicators (Planned)

Ambulance data captures response times by category (Category 1 life-threatening, Category 2 emergency) and — crucially — **hospital handover delays**: the time ambulance crews spend waiting outside A&E before they can hand a patient over.

This is directly connected to the A&E findings in Project 01. Long handover times mean ambulances are unavailable for new calls, and patients sit on stretchers in ambulance bays rather than receiving care inside. Understanding ambulance data is essential to understanding *why* A&E is failing.

**Data source:** https://www.england.nhs.uk/statistics/statistical-work-areas/ambulance-quality-indicators/

---

## 04 — Discharge Delays (Planned)

Discharge delay data measures how many patients are medically fit to leave hospital but cannot, because social care packages, CHC assessments, or community beds are not in place.

This is **exit block** — widely considered the primary driver of long A&E waits. A patient who cannot leave a ward frees no bed; a patient in a bed means no bed for the A&E patient waiting to be admitted; a patient waiting to be admitted means a long A&E wait. The chain runs directly from social care commissioning to the A&E four-hour figure.

**Data source:** https://www.england.nhs.uk/statistics/statistical-work-areas/discharge-delays-acute-data/

---

## 05 — Cancer Waiting Times (Planned)

Cancer waiting time standards include the 62-day referral-to-treatment target for urgent suspected cancer referrals, and the 28-day Faster Diagnosis Standard.

Late diagnosis and delayed treatment are directly associated with poorer cancer outcomes — particularly for cancers where stage at diagnosis drives survival rates (colorectal, lung, ovarian). This analysis will examine which cancer pathways are most at risk and which trusts are most off-track.

**Data source:** https://www.england.nhs.uk/statistics/statistical-work-areas/cancer-waiting-times/

---

## Technical approach

Each project follows the same seven-stage pipeline:

1. **Load** — read raw data from NHS England CSVs or Excel files
2. **Clean** — remove aggregate rows, fix data types, handle inconsistencies
3. **Validate** — structured sense checks before any analysis
4. **Summarise** — weighted national and trust-level metrics
5. **Trend** — compare first and second half of the year, flag worsening trusts
6. **Visualise** — charts saved as PNG files
7. **Report** — written findings with clinical context and recommendations

All scripts are written in Python using pandas and matplotlib. No proprietary tools required.

```
python >= 3.8
pandas
matplotlib
openpyxl   # for Excel files
```

---

## Why open NHS data matters

NHS England publishes this data under the Open Government Licence, meaning anyone can download, analyse, and share it. That is not true of every healthcare system in the world.

The numbers in these datasets are not abstract. Each four-hour breach is a person sitting in a waiting room. Each 52-week RTT wait is a patient in pain who has been waiting more than a year. Working with this data is a useful reminder of what healthcare analytics is actually for.

---

*Author: Iressa Cheng | Oxford DPhil | April 2026*  
*Data: NHS England open statistics | github.com/[your-username]/nhs-health-data-analysis*
