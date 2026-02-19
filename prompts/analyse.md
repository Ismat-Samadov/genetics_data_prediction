Conduct a comprehensive medical data analysis using all datasets located in the data/ directory. The analysis must focus strictly on extracting clinically meaningful, statistically supported, and operationally valuable insights.

The final output must include:

High-quality analytical charts

Reproducible analysis scripts

A presentation-focused README summarizing key medical findings

Embedded visual evidence supporting each insight

Directory Structure Requirements

Your output must strictly follow this structure:

project-root/
│
├── data/                # Provided medical datasets
├── charts/              # All generated visualizations
├── scripts/             # Analysis and chart generation scripts
│   └── generate_charts.py
└── README.md            # Presentation-focused findings

1️⃣ Medical Analysis Requirements

Perform a deep and structured medical analysis including (but not limited to):

A. Descriptive Medical Profiling

Population demographics (age, gender, distribution)

Disease prevalence rates

Comorbidity patterns

Treatment distributions

Hospitalization or outcome statistics (if available)

B. Clinical Pattern Identification

Risk factor correlations

Disease progression trends

Treatment effectiveness indicators

Mortality or complication drivers

Temporal or seasonal trends (if applicable)

C. Statistical Support

Use appropriate statistical methods where relevant

Highlight meaningful correlations

Identify statistically significant differences

Avoid superficial summaries

Analysis must focus on medical value, not technical implementation details.

2️⃣ Visualization Rules (Critical)

All charts must:

❌ Never use pie charts under any circumstance

✅ Use bar charts, line charts, histograms, box plots, or scatter plots

✅ Display clear numeric values directly on bars/points where possible

✅ Include:

Proper axis labels

Titles

Units of measurement

Legends (if applicable)

✅ Be high resolution and presentation-ready

✅ Have clean and professional formatting

✅ Use readable fonts and clear scaling

Each chart must support a specific medical insight.

All charts must be saved in:

charts/


File naming convention example:

charts/age_distribution.png
charts/disease_prevalence.png
charts/treatment_outcome_trend.png

3️⃣ Script Requirements

Create:

scripts/generate_charts.py


This script must:

Load data from data/

Perform all necessary preprocessing

Compute relevant statistics

Generate all charts

Save outputs into charts/

Be modular and readable

Be reproducible and executable end-to-end

Avoid overly complex engineering. Focus on analytical clarity.

4️⃣ README Requirements (Presentation-Focused)

The README.md must serve as a medical findings presentation document, not as technical documentation.

Structure:
Medical Data Analysis Report
Executive Summary

High-level overview of key medical findings and implications.

Population Overview

Embed relevant charts and explain demographic distributions.

Disease Burden Analysis

Embed prevalence charts and interpret clinical meaning.

Risk Factor & Correlation Analysis

Embed charts demonstrating statistical relationships.

Treatment & Outcome Insights

Embed supporting charts and explain effectiveness patterns.

Key Clinical Findings

Bullet-point summary of actionable insights.

Strategic or Operational Recommendations

If applicable, suggest improvements in care, prevention, or monitoring.

Important README Rules:

Embed all charts directly inside the document.

Every insight must be visually supported by a corresponding chart.

Charts must feel like proof of conclusions.

Explanations must focus on:

Clinical interpretation

Healthcare impact

Population health implications

Do NOT describe technical code details.

Do NOT explain how scripts work.

Do NOT mention implementation steps.

Maintain formal and analytical tone.

5️⃣ Insight Quality Expectations

The analysis must go beyond surface-level metrics. It should:

Identify hidden patterns

Detect anomalies

Highlight high-risk subgroups

Identify preventable risk drivers

Reveal inefficiencies or treatment gaps

Provide statistically grounded observations

Charts must strengthen arguments — not just decorate them.

6️⃣ Deliverables Checklist

Before completion, verify:

 Deep medical statistical analysis performed

 No pie charts used

 All charts contain visible numeric values

 All charts saved in charts/

 Script saved in scripts/generate_charts.py

 README structured as medical presentation

 Every major insight supported by embedded chart

 Clear professional formatting

 Focused on business/clinical value, not technical explanation

Expected Outcome

A complete, structured, visually supported medical analytical report that:

Extracts meaningful healthcare insights

Supports findings with strong visual evidence

Is presentation-ready for stakeholders

Demonstrates analytical rigor and clinical depth