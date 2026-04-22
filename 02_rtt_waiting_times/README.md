# 02 — Referral to Treatment (RTT) Waiting Times

**Status:** 🔄 In progress  
**Standard:** 92% of patients should start treatment within 18 weeks of referral  
**Data:** NHS England — https://www.england.nhs.uk/statistics/statistical-work-areas/rtt-waiting-times/

---

## What this analysis will cover

RTT data tracks the wait between a GP referring a patient to a specialist and that patient starting treatment. The 18-week standard has been consistently missed since 2016, and the backlog grew sharply during and after the COVID-19 pandemic.

This analysis will answer:

- Which specialties have the highest proportions of patients waiting over 18 weeks?
- How many patients have been waiting over 52 weeks (one year)?
- Is the backlog growing or shrinking — and at what pace?
- Are there trusts or specialties showing genuine, sustained improvement?

## Why this connects to the A&E data (Project 01)

Long RTT waits and poor A&E performance are not independent problems. When patients cannot access outpatient care or elective treatment in time, conditions deteriorate. Those patients then attend A&E — often at a more acute stage than if they had been seen earlier. RTT failure upstream creates A&E demand downstream.

## Planned approach

- Load NHS England RTT monthly provider-level data
- Calculate per-specialty 18-week performance (weighted by waiting list size)
- Identify the ten worst-performing specialties nationally
- Flag trusts with more than X% of their waiting list over 52 weeks
- Compare current backlog to pre-pandemic baseline (March 2020)
- Produce: specialty comparison chart, trust scatter plot, trend line

## Data source

Monthly provider-level RTT data, available as Excel files:  
https://www.england.nhs.uk/statistics/statistical-work-areas/rtt-waiting-times/

→ [Back to portfolio](../README.md)
