# Real-data mode: public e-commerce A/B experiment

## Included workflow

In the Varianta sidebar, choose **Public e-commerce A/B dataset**. The app downloads the CSV at runtime, so the computer running Streamlit needs internet access. Alternatively, download the source CSV separately and choose **Upload CSV**.

- Dataset source: Udacity/Kaggle-style e-commerce landing-page A/B test.
- Public GitHub mirror: https://github.com/beery4010/Analyze-AB-Test-Results
- Kaggle dataset page: https://www.kaggle.com/datasets/zhangluyuan/ab-testing
- Direct CSV: https://raw.githubusercontent.com/beery4010/Analyze-AB-Test-Results/master/ab_data.csv
- Common source fields: `user_id`, `timestamp`, `group`, `landing_page`, `converted`.

This is an educational dataset whose provenance and experiment implementation cannot be independently verified from the file alone. Do not describe it as production company data.

## Cleaning applied

1. Normalize source field names and group labels.
2. Exclude rows with missing IDs or non-binary conversion outcomes.
3. Exclude records where group and landing page disagree (control must map to `old_page`; treatment to `new_page`).
4. Exclude invalid timestamps.
5. Retain the earliest valid row for each user to enforce one observation per user.
6. Show counts for the source and cleaning steps in the app's **Public dataset provenance and cleaning audit** expander.

The app reports conversion rates and a fixed-horizon two-proportion test on the cleaned user-level dataset. Cleaning decisions can change the analysed population; inspect the audit before interpreting results.

## What the dataset does not contain

The source does not provide revenue/order value, checkout starts, refund events, page performance, device type, acquisition channel, or customer-newness. Varianta intentionally suppresses revenue and contribution projections in this mode. Fields required internally for the shared dashboard are marked with neutral placeholders and must not be interpreted as observed measurements. Segment exploration is limited to visit day because richer user attributes are absent.

## Reproduce locally

From the project root:

```powershell
python scripts/download_public_dataset.py
```

The file is saved to `data/raw/ab_data.csv`. The app can also load the dataset directly from the source URL.
