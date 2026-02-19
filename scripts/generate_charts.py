#!/usr/bin/env python3
"""
Acute Leukemia Gene Expression Analysis
Golub et al. (1999) ALL vs AML Classification Study
Affymetrix HG-U95Av2 Microarray — 7,129 genes, 72 patients
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────
# PATHS
# ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

# ──────────────────────────────────────────────
# VISUAL STYLE
# ──────────────────────────────────────────────
ALL_COLOR = "#2563eb"   # blue  — Acute Lymphoblastic Leukemia
AML_COLOR = "#dc2626"   # red   — Acute Myeloid Leukemia
TRAIN_COLOR = "#3b82f6"
TEST_COLOR = "#8b5cf6"

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 200,
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "axes.facecolor": "#f9fafb",
    "grid.color": "white",
    "grid.linewidth": 1.2,
    "axes.grid": True,
    "axes.grid.axis": "y",
})


# ──────────────────────────────────────────────
# DATA LOADING
# ──────────────────────────────────────────────
def load_labels():
    """Load patient diagnosis labels from actual.csv."""
    df = pd.read_csv(os.path.join(DATA_DIR, "actual.csv")).dropna()
    df["patient"] = df["patient"].astype(int)
    return df.set_index("patient")["cancer"].to_dict()


def load_expression_and_calls(filepath, labels):
    """
    Parse microarray CSV.
    Returns:
        expr_df  — DataFrame[samples x genes + 'diagnosis']
        call_map — {patient_id: np.array of 'P'/'A'/'M' strings}
        gene_names — list of gene description strings
    """
    df = pd.read_csv(filepath)
    all_cols = list(df.columns)

    # Numeric column names = patient sample IDs
    expr_col_names = [c for c in all_cols if str(c).strip().isdigit()]
    gene_names = df["Gene Description"].tolist()

    # Build sample x gene matrix
    expr_matrix = df[expr_col_names].T.copy()
    expr_matrix.columns = gene_names
    expr_matrix.index = expr_matrix.index.astype(int)
    expr_matrix["diagnosis"] = expr_matrix.index.map(labels)
    expr_matrix = expr_matrix.dropna(subset=["diagnosis"])

    # Build call map: each numeric column is followed by its call column
    call_map = {}
    for col in expr_col_names:
        col_pos = all_cols.index(col)
        if col_pos + 1 < len(all_cols):
            call_col = all_cols[col_pos + 1]
            call_map[int(col)] = df[call_col].values

    return expr_matrix, call_map, gene_names


# ──────────────────────────────────────────────
# STATISTICS
# ──────────────────────────────────────────────
def benjamini_hochberg(p_values):
    """Benjamini-Hochberg FDR correction."""
    n = len(p_values)
    order = np.argsort(p_values)
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, n + 1)
    q = p_values * n / ranks
    q_adj = np.minimum.accumulate(q[order][::-1])[::-1][np.argsort(order)]
    return np.minimum(q_adj, 1.0)


def differential_expression(expr_combined, gene_cols):
    """
    Welch's t-test + BH-FDR + Cohen's d + log2FC for every gene.
    Returns DataFrame sorted by absolute Cohen's d (descending).
    """
    all_mask = expr_combined["diagnosis"] == "ALL"
    aml_mask = expr_combined["diagnosis"] == "AML"
    X_all = expr_combined.loc[all_mask, gene_cols].values.astype(float)
    X_aml = expr_combined.loc[aml_mask, gene_cols].values.astype(float)

    t_stats, p_vals, cohen_ds, mean_all, mean_aml = [], [], [], [], []

    for i in range(len(gene_cols)):
        a, b = X_all[:, i], X_aml[:, i]
        t, p = stats.ttest_ind(a, b, equal_var=False)
        t_stats.append(t)
        p_vals.append(max(p, 1e-300))
        mean_all.append(a.mean())
        mean_aml.append(b.mean())
        n1, n2 = len(a), len(b)
        pooled = np.sqrt(((n1 - 1) * a.std() ** 2 + (n2 - 1) * b.std() ** 2) / (n1 + n2 - 2))
        cohen_ds.append((a.mean() - b.mean()) / pooled if pooled > 0 else 0.0)

    p_arr = np.array(p_vals)
    q_arr = benjamini_hochberg(p_arr)
    mean_all_arr = np.array(mean_all)
    mean_aml_arr = np.array(mean_aml)

    # Log2 fold-change with shift correction for non-positive values
    shift = max(0.0, 1.0 - min(mean_all_arr.min(), mean_aml_arr.min()))
    log2fc = np.log2((mean_all_arr + shift) / (mean_aml_arr + shift + 1e-9))

    result = pd.DataFrame({
        "gene": gene_cols,
        "t_stat": t_stats,
        "p_value": p_arr,
        "fdr": q_arr,
        "mean_ALL": mean_all_arr,
        "mean_AML": mean_aml_arr,
        "log2FC": log2fc,
        "cohen_d": cohen_ds,
        "abs_cohen_d": np.abs(cohen_ds),
    }).sort_values("abs_cohen_d", ascending=False).reset_index(drop=True)

    return result


# ──────────────────────────────────────────────
# CHART 1 — Disease Prevalence
# ──────────────────────────────────────────────
def chart_disease_prevalence(labels):
    counts = pd.Series(labels.values()).value_counts()
    total = counts.sum()

    fig, ax = plt.subplots(figsize=(7, 5))
    colors = [ALL_COLOR if x == "ALL" else AML_COLOR for x in counts.index]
    bars = ax.bar(counts.index, counts.values, color=colors,
                  edgecolor="white", linewidth=1.5, width=0.45, zorder=3)

    for bar, val in zip(bars, counts.values):
        pct = val / total * 100
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.6,
                f"{val} patients\n({pct:.1f}%)",
                ha="center", va="bottom", fontweight="bold", fontsize=12)

    ax.set_title("Leukemia Subtype Distribution\nFull Study Cohort (N=72 patients)")
    ax.set_xlabel("Leukemia Subtype")
    ax.set_ylabel("Number of Patients")
    ax.set_ylim(0, counts.max() * 1.35)
    ax.set_xticklabels([
        "ALL\n(Acute Lymphoblastic)",
        "AML\n(Acute Myeloid)"
    ], fontsize=11)

    legend_patches = [
        mpatches.Patch(color=ALL_COLOR, label="ALL — Acute Lymphoblastic Leukemia"),
        mpatches.Patch(color=AML_COLOR, label="AML — Acute Myeloid Leukemia"),
    ]
    ax.legend(handles=legend_patches, loc="upper right", framealpha=0.9)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "disease_prevalence.png"), bbox_inches="tight")
    plt.close()
    print("  checkmark disease_prevalence.png")


# ──────────────────────────────────────────────
# CHART 2 — Cohort Composition (Train vs Test)
# ──────────────────────────────────────────────
def chart_cohort_composition(labels, train_ids, test_ids):
    subtypes = ["ALL", "AML"]
    train_lbl = {k: v for k, v in labels.items() if k in train_ids}
    test_lbl = {k: v for k, v in labels.items() if k in test_ids}
    tc = pd.Series(train_lbl.values()).value_counts()
    vc = pd.Series(test_lbl.values()).value_counts()

    x = np.arange(len(subtypes))
    width = 0.32

    fig, ax = plt.subplots(figsize=(8, 5))
    b1 = ax.bar(x - width / 2, [tc.get(s, 0) for s in subtypes], width,
                label=f"Training Cohort (n={len(train_ids)})",
                color=TRAIN_COLOR, alpha=0.9, zorder=3)
    b2 = ax.bar(x + width / 2, [vc.get(s, 0) for s in subtypes], width,
                label=f"Independent Test Cohort (n={len(test_ids)})",
                color=TEST_COLOR, alpha=0.9, zorder=3)

    for bars in [b1, b2]:
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.3,
                    str(int(h)), ha="center", va="bottom", fontweight="bold", fontsize=11)

    ax.set_title("Cohort Composition: Training vs Independent Test Set\nby Leukemia Subtype")
    ax.set_xticks(x)
    ax.set_xticklabels(["ALL (Lymphoblastic)", "AML (Myeloid)"], fontsize=11)
    ax.set_ylabel("Number of Patients")
    ax.set_ylim(0, max(tc.max(), vc.max()) * 1.35)
    ax.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "cohort_composition.png"), bbox_inches="tight")
    plt.close()
    print("  checkmark cohort_composition.png")


# ──────────────────────────────────────────────
# CHART 3 — Expression Distribution by Subtype
# ──────────────────────────────────────────────
def chart_expression_distribution(expr_combined, gene_cols):
    rng = np.random.default_rng(42)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    for ax, subtype, color in zip(axes, ["ALL", "AML"], [ALL_COLOR, AML_COLOR]):
        vals = expr_combined.loc[expr_combined["diagnosis"] == subtype, gene_cols].values.flatten()
        sample = rng.choice(vals, size=min(60000, len(vals)), replace=False)
        ax.hist(sample, bins=90, color=color, alpha=0.85, edgecolor="white", linewidth=0.2, zorder=3)

        med, mean_ = np.median(sample), np.mean(sample)
        ax.axvline(med, color="black", linestyle="--", linewidth=1.8, label=f"Median: {med:.0f}")
        ax.axvline(mean_, color="#374151", linestyle=":", linewidth=1.5, label=f"Mean: {mean_:.0f}")

        n_pat = int((expr_combined["diagnosis"] == subtype).sum())
        ax.set_title(f"{subtype} Expression Intensity Profile\n({n_pat} patients x 7,129 genes)")
        ax.set_xlabel("Expression Intensity (arbitrary units)")
        ax.set_ylabel("Frequency")
        ax.legend(fontsize=10)

        stats_txt = (f"IQR: {np.percentile(sample, 25):.0f}-{np.percentile(sample, 75):.0f}\n"
                     f"Min: {sample.min():.0f}  Max: {sample.max():.0f}")
        ax.text(0.97, 0.97, stats_txt, transform=ax.transAxes,
                ha="right", va="top", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.35", facecolor="white", alpha=0.85))

    plt.suptitle("Transcriptome-Wide Expression Intensity: ALL vs AML",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "expression_distribution_by_subtype.png"), bbox_inches="tight")
    plt.close()
    print("  checkmark expression_distribution_by_subtype.png")


# ──────────────────────────────────────────────
# CHART 4 — PCA Molecular Separation
# ──────────────────────────────────────────────
def chart_pca(expr_combined, gene_cols):
    X = expr_combined[gene_cols].values.astype(float)
    y = expr_combined["diagnosis"].values

    X_scaled = StandardScaler().fit_transform(X)
    pca = PCA(n_components=3)
    X_pca = pca.fit_transform(X_scaled)
    var = pca.explained_variance_ratio_ * 100

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax = axes[0]
    for subtype, color, marker in [("ALL", ALL_COLOR, "o"), ("AML", AML_COLOR, "s")]:
        mask = y == subtype
        ax.scatter(X_pca[mask, 0], X_pca[mask, 1],
                   c=color, label=f"{subtype} (n={mask.sum()})",
                   s=75, alpha=0.85, marker=marker, edgecolors="white", linewidth=0.5, zorder=3)
    ax.set_xlabel(f"PC1 — {var[0]:.1f}% variance explained", fontsize=11)
    ax.set_ylabel(f"PC2 — {var[1]:.1f}% variance explained", fontsize=11)
    ax.set_title("PCA: Molecular Subtype Separation\n(PC1 vs PC2, all 7,129 genes)")
    ax.legend(fontsize=11, framealpha=0.9)

    ax2 = axes[1]
    labels_pc = [f"PC{i+1}" for i in range(3)]
    cols_pc = ["#3b82f6", "#8b5cf6", "#10b981"]
    bars = ax2.bar(labels_pc, var, color=cols_pc, edgecolor="white", linewidth=1.5, width=0.45, zorder=3)
    for bar, v in zip(bars, var):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                 f"{v:.1f}%", ha="center", va="bottom", fontweight="bold", fontsize=12)
    ax2.set_title("PCA Variance Explained\nper Principal Component")
    ax2.set_xlabel("Principal Component")
    ax2.set_ylabel("Variance Explained (%)")
    ax2.set_ylim(0, var.max() * 1.35)

    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "pca_molecular_separation.png"), bbox_inches="tight")
    plt.close()
    print("  checkmark pca_molecular_separation.png")


# ──────────────────────────────────────────────
# CHART 5 — Volcano Plot
# ──────────────────────────────────────────────
def chart_volcano(de_results):
    df = de_results.copy()
    df["neg_log10_fdr"] = -np.log10(df["fdr"].clip(lower=1e-10))

    SIG = -np.log10(0.05)
    FC = 1.0

    df["category"] = "Non-significant"
    df.loc[(df["neg_log10_fdr"] >= SIG) & (df["log2FC"] >= FC), "category"] = "ALL upregulated"
    df.loc[(df["neg_log10_fdr"] >= SIG) & (df["log2FC"] <= -FC), "category"] = "AML upregulated"
    df.loc[(df["neg_log10_fdr"] >= SIG) & (df["log2FC"].abs() < FC), "category"] = "Significant (|FC|<2)"

    cat_cfg = {
        "Non-significant":      ("#94a3b8", 12, 0.25),
        "ALL upregulated":      (ALL_COLOR,  35, 0.80),
        "AML upregulated":      (AML_COLOR,  35, 0.80),
        "Significant (|FC|<2)": ("#f59e0b",  25, 0.75),
    }

    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#f9fafb")

    for cat, (color, size, alpha) in cat_cfg.items():
        sub = df[df["category"] == cat]
        ax.scatter(sub["log2FC"], sub["neg_log10_fdr"],
                   c=color, s=size, alpha=alpha,
                   label=f"{cat} (n={len(sub):,})",
                   zorder=3 if cat != "Non-significant" else 2)

    ax.axhline(SIG, color="#374151", linestyle="--", linewidth=1, alpha=0.6)
    ax.axvline(FC,  color="#374151", linestyle="--", linewidth=1, alpha=0.6)
    ax.axvline(-FC, color="#374151", linestyle="--", linewidth=1, alpha=0.6)

    # Annotate top 4 genes per direction
    for direction in ["ALL upregulated", "AML upregulated"]:
        top = df[df["category"] == direction].nlargest(4, "abs_cohen_d")
        for _, row in top.iterrows():
            label = str(row["gene"])[:28]
            ax.annotate(label, (row["log2FC"], row["neg_log10_fdr"]),
                        textcoords="offset points", xytext=(6, 4),
                        fontsize=7.5, color="#111827",
                        arrowprops=dict(arrowstyle="->", color="#6b7280", lw=0.8))

    n_sig = int((df["fdr"] < 0.05).sum())
    n_all_up = int((df["category"] == "ALL upregulated").sum())
    n_aml_up = int((df["category"] == "AML upregulated").sum())
    summary = (f"Total genes: {len(df):,}\n"
               f"FDR < 0.05: {n_sig:,}\n"
               f"ALL up: {n_all_up} | AML up: {n_aml_up}")
    ax.text(0.02, 0.98, summary, transform=ax.transAxes,
            ha="left", va="top", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.9))

    ax.set_xlabel("Log2 Fold Change  (ALL / AML)", fontsize=12)
    ax.set_ylabel("-log10(FDR-adjusted p-value)", fontsize=12)
    ax.set_title("Volcano Plot: Differential Gene Expression\nALL vs AML (Welch's t-test, BH-FDR, 7,129 genes)")
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)

    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "volcano_differential_expression.png"), bbox_inches="tight")
    plt.close()
    print("  checkmark volcano_differential_expression.png")


# ──────────────────────────────────────────────
# CHART 6 — Top Biomarker Genes (Effect Size)
# ──────────────────────────────────────────────
def chart_top_biomarkers(de_results):
    top_all = de_results[de_results["cohen_d"] > 0].head(10)
    top_aml = de_results[de_results["cohen_d"] < 0].head(10)
    top = pd.concat([top_all, top_aml]).sort_values("cohen_d")

    colors = [ALL_COLOR if d > 0 else AML_COLOR for d in top["cohen_d"]]
    labels = [str(g)[:42] for g in top["gene"]]

    fig, ax = plt.subplots(figsize=(10, 9))
    y_pos = range(len(top))
    bars = ax.barh(y_pos, top["cohen_d"], color=colors, alpha=0.88,
                   edgecolor="white", linewidth=0.8, height=0.68, zorder=3)

    for bar, val in zip(bars, top["cohen_d"]):
        offset = 0.06 if val >= 0 else -0.06
        ha = "left" if val >= 0 else "right"
        ax.text(val + offset, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}", ha=ha, va="center", fontweight="bold", fontsize=9)

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.axvline(0, color="#111827", linewidth=1.3)
    ax.set_xlabel("Cohen's d Effect Size\n(Positive = higher in ALL, Negative = higher in AML)", fontsize=11)
    ax.set_title("Top 20 Candidate Biomarker Genes by Discriminative Power\n(ALL vs AML, ranked by effect size)")

    legend_patches = [
        mpatches.Patch(color=ALL_COLOR, label="Higher in ALL (Lymphoblastic)"),
        mpatches.Patch(color=AML_COLOR, label="Higher in AML (Myeloid)"),
    ]
    ax.legend(handles=legend_patches, loc="lower right", fontsize=10, framealpha=0.9)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "top_biomarker_genes.png"), bbox_inches="tight")
    plt.close()
    print("  checkmark top_biomarker_genes.png")


# ──────────────────────────────────────────────
# CHART 7 — Top Genes Box Plots
# ──────────────────────────────────────────────
def chart_top_genes_boxplots(expr_combined, de_results):
    top4_all = de_results[de_results["cohen_d"] > 0].head(4)
    top4_aml = de_results[de_results["cohen_d"] < 0].head(4)
    top8 = pd.concat([top4_all, top4_aml])

    fig, axes = plt.subplots(2, 4, figsize=(16, 9))
    axes = axes.flatten()
    rng = np.random.default_rng(0)

    for i, (_, row) in enumerate(top8.iterrows()):
        ax = axes[i]
        gene = row["gene"]
        if gene not in expr_combined.columns:
            ax.axis("off")
            continue

        all_v = expr_combined.loc[expr_combined["diagnosis"] == "ALL", gene].values.astype(float)
        aml_v = expr_combined.loc[expr_combined["diagnosis"] == "AML", gene].values.astype(float)

        bp = ax.boxplot([all_v, aml_v], labels=["ALL", "AML"],
                        patch_artist=True, notch=False,
                        medianprops=dict(color="black", linewidth=2.2),
                        whiskerprops=dict(linewidth=1.5),
                        capprops=dict(linewidth=1.5),
                        flierprops=dict(marker="o", markersize=3, alpha=0.4))
        bp["boxes"][0].set_facecolor(ALL_COLOR); bp["boxes"][0].set_alpha(0.8)
        bp["boxes"][1].set_facecolor(AML_COLOR);  bp["boxes"][1].set_alpha(0.8)

        for j, (vals, color) in enumerate([(all_v, ALL_COLOR), (aml_v, AML_COLOR)]):
            jitter = rng.normal(j + 1, 0.07, len(vals))
            ax.scatter(jitter, vals, alpha=0.35, s=11, color=color, zorder=4)

        # Annotate medians
        ax.text(1, np.median(all_v), f" {np.median(all_v):.0f}", va="center", fontsize=8)
        ax.text(2, np.median(aml_v), f" {np.median(aml_v):.0f}", va="center", fontsize=8)

        _, pval = stats.ttest_ind(all_v, aml_v, equal_var=False)
        sig = "***" if pval < 0.001 else ("**" if pval < 0.01 else ("*" if pval < 0.05 else "ns"))
        y_top = max(all_v.max(), aml_v.max())
        ax.text(1.5, y_top * 1.06, sig, ha="center", fontsize=13, fontweight="bold")

        direction = "ALL up" if row["cohen_d"] > 0 else "AML up"
        ax.set_title(f"{str(gene)[:32]}\nd={row['cohen_d']:.2f}, {direction}", fontsize=8.5, fontweight="bold")
        ax.set_ylabel("Expression", fontsize=9)

    plt.suptitle("Expression Profiles of Top 8 Diagnostic Biomarker Genes\n(ALL vs AML  |  * p<0.05  ** p<0.01  *** p<0.001)",
                 fontsize=13, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "top_genes_expression_comparison.png"), bbox_inches="tight")
    plt.close()
    print("  checkmark top_genes_expression_comparison.png")


# ──────────────────────────────────────────────
# CHART 8 — Expression Heatmap (Top 40 Genes)
# ──────────────────────────────────────────────
def chart_expression_heatmap(expr_combined, de_results):
    top40_genes = [g for g in de_results["gene"].head(40)
                   if g in expr_combined.columns]

    expr_sorted = expr_combined.sort_values("diagnosis")
    diagnoses = expr_sorted["diagnosis"].values
    X = expr_sorted[top40_genes].values.T.astype(float)

    # Z-score per gene, clip outliers
    X_z = stats.zscore(X, axis=1, nan_policy="omit")
    X_z = np.clip(X_z, -3, 3)

    fig, (ax, cbar_ax) = plt.subplots(1, 2, figsize=(17, 12),
                                       gridspec_kw={"width_ratios": [22, 1]})
    im = ax.imshow(X_z, aspect="auto", cmap="RdBu_r", interpolation="nearest", vmin=-3, vmax=3)

    # Diagnosis strip above heatmap
    for j, d in enumerate(diagnoses):
        rect = plt.Rectangle((j - 0.5, -1.8), 1, 1.2,
                               color=ALL_COLOR if d == "ALL" else AML_COLOR,
                               transform=ax.transData, clip_on=False)
        ax.add_patch(rect)

    # Separator line
    n_all = int((diagnoses == "ALL").sum())
    ax.axvline(n_all - 0.5, color="#111827", linewidth=2.5)

    # Subtype labels above
    ax.text(n_all / 2 - 0.5, -2.5, "ALL", ha="center", fontsize=11,
            fontweight="bold", color=ALL_COLOR, transform=ax.transData)
    ax.text(n_all + (len(diagnoses) - n_all) / 2, -2.5, "AML", ha="center",
            fontsize=11, fontweight="bold", color=AML_COLOR, transform=ax.transData)

    ax.set_xticks(range(len(diagnoses)))
    ax.set_xticklabels(
        [f"{'A' if d == 'ALL' else 'M'}{i+1}" for i, d in enumerate(diagnoses)],
        fontsize=6.5, rotation=90)
    ax.set_yticks(range(len(top40_genes)))
    ax.set_yticklabels([str(g)[:48] for g in top40_genes], fontsize=7)

    plt.colorbar(im, cax=cbar_ax, label="Z-score (gene expression)")
    ax.set_title("Heatmap: Top 40 Differentially Expressed Genes\n"
                 "(Z-score normalized per gene | Red=high, Blue=low | Sorted by subtype)",
                 pad=22)
    ax.set_xlabel("Patient Samples (sorted: ALL then AML)", labelpad=18)
    ax.set_ylabel("Gene Probes (ranked by effect size)")

    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "expression_heatmap_top40.png"), bbox_inches="tight")
    plt.close()
    print("  checkmark expression_heatmap_top40.png")


# ──────────────────────────────────────────────
# CHART 9 — Gene Expression Activity (P/A calls)
# ──────────────────────────────────────────────
def chart_gene_expression_activity(call_maps_all, labels):
    """Proportion of genes with Present call per patient, by diagnosis."""
    all_rates, aml_rates = [], []

    for patient_id, calls in call_maps_all.items():
        if patient_id not in labels:
            continue
        p_rate = np.mean(calls == "P") * 100
        if labels[patient_id] == "ALL":
            all_rates.append(p_rate)
        else:
            aml_rates.append(p_rate)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Box plot
    ax = axes[0]
    bp = ax.boxplot([all_rates, aml_rates], labels=["ALL", "AML"],
                    patch_artist=True, notch=False,
                    medianprops=dict(color="black", linewidth=2.2),
                    whiskerprops=dict(linewidth=1.5),
                    capprops=dict(linewidth=1.5))
    bp["boxes"][0].set_facecolor(ALL_COLOR); bp["boxes"][0].set_alpha(0.8)
    bp["boxes"][1].set_facecolor(AML_COLOR);  bp["boxes"][1].set_alpha(0.8)

    rng = np.random.default_rng(1)
    for j, (rates, color) in enumerate([(all_rates, ALL_COLOR), (aml_rates, AML_COLOR)]):
        jitter = rng.normal(j + 1, 0.07, len(rates))
        ax.scatter(jitter, rates, alpha=0.55, s=20, color=color, zorder=5)

    t, p = stats.ttest_ind(all_rates, aml_rates)
    sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else f"p={p:.3f}"))
    y_top = max(max(all_rates), max(aml_rates))
    ax.text(1.5, y_top + 0.8, sig, ha="center", fontsize=14, fontweight="bold")

    for pos, rates in [(1, all_rates), (2, aml_rates)]:
        ax.text(pos, np.median(rates) - 0.9,
                f"Median: {np.median(rates):.1f}%", ha="center", fontsize=9, fontweight="bold")

    ax.set_title("Genome-Wide Transcriptional Activity\n(% Genes with Present Call, by Subtype)")
    ax.set_ylabel("% Genes Expressed (Present call)")

    # Histogram
    ax2 = axes[1]
    bins = np.linspace(min(all_rates + aml_rates) - 1, max(all_rates + aml_rates) + 1, 22)
    ax2.hist(all_rates, bins=bins, color=ALL_COLOR, alpha=0.75,
             label=f"ALL (n={len(all_rates)})", edgecolor="white", zorder=3)
    ax2.hist(aml_rates, bins=bins, color=AML_COLOR, alpha=0.75,
             label=f"AML (n={len(aml_rates)})", edgecolor="white", zorder=3)
    ax2.axvline(np.mean(all_rates), color=ALL_COLOR, linestyle="--", linewidth=2,
                label=f"ALL mean: {np.mean(all_rates):.1f}%")
    ax2.axvline(np.mean(aml_rates), color=AML_COLOR, linestyle="--", linewidth=2,
                label=f"AML mean: {np.mean(aml_rates):.1f}%")
    ax2.set_title("Distribution of Transcriptional Activity\nALL vs AML Patients")
    ax2.set_xlabel("% Genes Expressed per Patient")
    ax2.set_ylabel("Number of Patients")
    ax2.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "gene_expression_activity.png"), bbox_inches="tight")
    plt.close()
    print("  checkmark gene_expression_activity.png")


# ──────────────────────────────────────────────
# CHART 10 — Significance Landscape
# ──────────────────────────────────────────────
def chart_significance_landscape(de_results):
    thresholds = [0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2]
    counts_all_up, counts_aml_up, counts_total = [], [], []

    for t in thresholds:
        sig = de_results[de_results["fdr"] < t]
        counts_total.append(len(sig))
        counts_all_up.append(int((sig["cohen_d"] > 0).sum()))
        counts_aml_up.append(int((sig["cohen_d"] < 0).sum()))

    x = np.arange(len(thresholds))
    width = 0.32

    fig, ax = plt.subplots(figsize=(11, 6))
    b1 = ax.bar(x - width / 2, counts_all_up, width, label="ALL upregulated",
                color=ALL_COLOR, alpha=0.9, zorder=3)
    b2 = ax.bar(x + width / 2, counts_aml_up, width, label="AML upregulated",
                color=AML_COLOR, alpha=0.9, zorder=3)

    for bars in [b1, b2]:
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 2,
                    str(int(h)), ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    ax2 = ax.twinx()
    ax2.plot(x, counts_total, "o--", color="#111827", linewidth=2, markersize=8,
             label="Total significant", zorder=5)
    for xi, ct in zip(x, counts_total):
        ax2.text(xi, ct + 4, str(ct), ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax2.set_ylabel("Total Significant Genes", fontsize=11)
    ax2.spines["top"].set_visible(False)
    ax2.legend(loc="upper left", fontsize=9)

    ax.set_title("Differentially Expressed Genes by FDR Threshold\n(ALL vs AML, 7,129 genes total)")
    ax.set_xticks(x)
    ax.set_xticklabels([f"FDR < {t}" for t in thresholds], rotation=28)
    ax.set_ylabel("Number of Significant Genes")
    ax.legend(loc="upper center", fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, "significance_landscape.png"), bbox_inches="tight")
    plt.close()
    print("  checkmark significance_landscape.png")


# ──────────────────────────────────────────────
# SAVE RESULTS
# ──────────────────────────────────────────────
def save_results(de_results, labels, train_ids, test_ids):
    de_results.to_csv(
        os.path.join(CHARTS_DIR, "differential_expression_results.csv"), index=False)
    print("  checkmark differential_expression_results.csv")

    all_count = sum(1 for v in labels.values() if v == "ALL")
    aml_count = sum(1 for v in labels.values() if v == "AML")
    sig05 = de_results[de_results["fdr"] < 0.05]
    sig01 = de_results[de_results["fdr"] < 0.01]

    summary = (
        "ACUTE LEUKEMIA GENE EXPRESSION ANALYSIS -- SUMMARY\n"
        "===================================================\n"
        "Dataset: Golub et al. (1999) ALL/AML Classification Study\n"
        "Platform: Affymetrix HG-U95Av2 Microarray\n"
        f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}\n\n"
        "COHORT COMPOSITION\n"
        "------------------\n"
        f"Total Patients     : {len(labels)}\n"
        f"  ALL              : {all_count} ({all_count/len(labels)*100:.1f}%)\n"
        f"  AML              : {aml_count} ({aml_count/len(labels)*100:.1f}%)\n"
        f"Training Cohort    : {len(train_ids)} patients\n"
        f"Independent Test   : {len(test_ids)} patients\n\n"
        "DIFFERENTIAL EXPRESSION (Welch's t-test, BH-FDR)\n"
        "--------------------------------------------------\n"
        f"Total Genes Profiled: {len(de_results):,}\n"
        f"FDR < 0.05: {len(sig05):,} genes\n"
        f"  ALL upregulated : {int((sig05['cohen_d'] > 0).sum()):,}\n"
        f"  AML upregulated : {int((sig05['cohen_d'] < 0).sum()):,}\n"
        f"FDR < 0.01: {len(sig01):,} genes\n\n"
        "TOP 10 ALL-UPREGULATED GENES\n"
        "-----------------------------\n"
    )
    top_all = de_results[de_results["cohen_d"] > 0][["gene", "cohen_d", "fdr", "log2FC"]].head(10)
    top_aml = de_results[de_results["cohen_d"] < 0][["gene", "cohen_d", "fdr", "log2FC"]].head(10)
    summary += top_all.to_string(index=False)
    summary += "\n\nTOP 10 AML-UPREGULATED GENES\n-----------------------------\n"
    summary += top_aml.to_string(index=False)

    with open(os.path.join(CHARTS_DIR, "analysis_summary.txt"), "w", encoding="utf-8") as f:
        f.write(summary)
    print("  checkmark analysis_summary.txt")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    print("=" * 62)
    print("  ACUTE LEUKEMIA GENE EXPRESSION ANALYSIS")
    print("  Golub et al. (1999) -- ALL vs AML, 72 patients, 7,129 genes")
    print("=" * 62)

    print("\n[1/5] Loading patient labels ...")
    labels = load_labels()
    print(f"      {len(labels)} patients loaded")

    print("[2/5] Parsing expression matrices ...")
    train_path = os.path.join(DATA_DIR, "data_set_ALL_AML_train.csv")
    test_path  = os.path.join(DATA_DIR, "data_set_ALL_AML_independent.csv")

    expr_train, calls_train, gene_names = load_expression_and_calls(train_path, labels)
    expr_test,  calls_test,  _          = load_expression_and_calls(test_path,  labels)

    train_ids = set(expr_train.index)
    test_ids  = set(expr_test.index)

    expr_combined = pd.concat([expr_train, expr_test])
    gene_cols = [g for g in gene_names if g in expr_combined.columns]
    call_maps_all = {**calls_train, **calls_test}

    print(f"      Train: {len(expr_train)} patients | Test: {len(expr_test)} patients")
    print(f"      Genes: {len(gene_cols):,}")

    print("[3/5] Computing differential expression ...")
    de_results = differential_expression(expr_combined, gene_cols)
    n_sig = int((de_results["fdr"] < 0.05).sum())
    print(f"      Significant genes (FDR < 0.05): {n_sig:,}")

    print("\n[4/5] Generating charts ...")
    chart_disease_prevalence(labels)
    chart_cohort_composition(labels, train_ids, test_ids)
    chart_expression_distribution(expr_combined, gene_cols)
    chart_pca(expr_combined, gene_cols)
    chart_volcano(de_results)
    chart_top_biomarkers(de_results)
    chart_top_genes_boxplots(expr_combined, de_results)
    chart_expression_heatmap(expr_combined, de_results)
    chart_gene_expression_activity(call_maps_all, labels)
    chart_significance_landscape(de_results)

    print("\n[5/5] Saving results ...")
    save_results(de_results, labels, train_ids, test_ids)

    print("\n" + "=" * 62)
    print("  COMPLETE -- all charts saved to charts/")
    print("=" * 62)


if __name__ == "__main__":
    main()
