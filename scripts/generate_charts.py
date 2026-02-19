import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    p_values = np.asarray(p_values)
    n = p_values.size
    order = np.argsort(p_values)
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, n + 1)
    q_values = p_values * n / ranks
    q_values[order] = np.minimum.accumulate(q_values[order][::-1])[::-1]
    return np.clip(q_values, 0, 1)


def load_expression(df: pd.DataFrame):
    expr_cols = [c for c in df.columns if c.isdigit()]
    expr_cols = sorted(expr_cols, key=lambda x: int(x))
    X = df[expr_cols].T
    gene_names = df['Gene Description'].values
    gene_accession = df['Gene Accession Number'].values
    return X, expr_cols, gene_names, gene_accession


def label_lookup(labels_df: pd.DataFrame) -> pd.Series:
    df = labels_df.copy()
    df['patient'] = df['patient'].astype(int)
    return df.set_index('patient')['cancer']


def add_bar_labels(ax, fmt='{:.1f}', padding=3):
    for p in ax.patches:
        value = p.get_width() if p.get_width() != 0 else p.get_height()
        if p.get_width() != 0:
            ax.annotate(fmt.format(value),
                        (value, p.get_y() + p.get_height() / 2.),
                        ha='left', va='center',
                        fontsize=9, xytext=(padding, 0),
                        textcoords='offset points')
        else:
            ax.annotate(fmt.format(value),
                        (p.get_x() + p.get_width() / 2., value),
                        ha='center', va='bottom',
                        fontsize=9, xytext=(0, padding),
                        textcoords='offset points')


def add_value_labels(ax, fmt='{:.0f}', padding=3):
    for p in ax.patches:
        value = p.get_height()
        ax.annotate(fmt.format(value),
                    (p.get_x() + p.get_width() / 2., value),
                    ha='center', va='bottom',
                    fontsize=9, xytext=(0, padding),
                    textcoords='offset points')


def shorten_labels(labels, max_len=28):
    out = []
    for label in labels:
        if len(label) <= max_len:
            out.append(label)
        else:
            out.append(label[:max_len - 1] + '?')
    return out


def main():
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / 'data'
    charts_dir = base_dir / 'charts'
    ensure_dir(charts_dir)

    sns.set_theme(style='whitegrid', context='talk', font_scale=0.9)
    plt.rcParams['figure.dpi'] = 200

    train_df = pd.read_csv(data_dir / 'data_set_ALL_AML_train.csv')
    test_df = pd.read_csv(data_dir / 'data_set_ALL_AML_independent.csv')
    labels_df = pd.read_csv(data_dir / 'actual.csv')

    X_train, train_ids, gene_names, gene_accession = load_expression(train_df)
    X_test, test_ids, _, _ = load_expression(test_df)

    labels = label_lookup(labels_df)
    y_train = labels.loc[[int(i) for i in train_ids]].values
    y_test = labels.loc[[int(i) for i in test_ids]].values

    # Disease prevalence (counts + percent)
    counts = pd.Series(y_train).value_counts().reindex(['ALL', 'AML'])
    total = counts.sum()
    counts_df = pd.DataFrame({
        'Class': counts.index,
        'Count': counts.values,
        'Percent': (counts.values / total) * 100
    })

    plt.figure(figsize=(7, 4))
    ax = sns.barplot(data=counts_df, x='Class', y='Count', hue='Class',
                     palette=['#2563eb', '#dc2626'], legend=False)
    add_value_labels(ax, fmt='{:.0f}')
    plt.title('Training Cohort Disease Prevalence (Counts)')
    plt.xlabel('Diagnosis')
    plt.ylabel('Number of Patients')
    plt.tight_layout()
    plt.savefig(charts_dir / 'disease_prevalence_counts.png')
    plt.close()

    plt.figure(figsize=(7, 4))
    ax = sns.barplot(data=counts_df, x='Class', y='Percent', hue='Class',
                     palette=['#2563eb', '#dc2626'], legend=False)
    add_value_labels(ax, fmt='{:.1f}%')
    plt.title('Training Cohort Disease Prevalence (Percent)')
    plt.xlabel('Diagnosis')
    plt.ylabel('Percent of Cohort')
    plt.tight_layout()
    plt.savefig(charts_dir / 'disease_prevalence_percent.png')
    plt.close()

    # Expression distribution
    plt.figure(figsize=(9, 4))
    values = X_train.values.flatten()
    plt.hist(values, bins=120, color='#0ea5e9', alpha=0.8, edgecolor='black')
    plt.axvline(np.median(values), color='#111827', linestyle='--', linewidth=1)
    plt.title('Distribution of Gene Expression Values (Training Set)')
    plt.xlabel('Expression Value')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.savefig(charts_dir / 'expression_distribution.png')
    plt.close()

    # Differential expression (Welch t-test)
    X_all = X_train[y_train == 'ALL']
    X_aml = X_train[y_train == 'AML']

    t_stats = []
    p_values = []
    mean_diffs = []
    cohen_d = []

    for i in range(X_train.shape[1]):
        all_expr = X_all.iloc[:, i]
        aml_expr = X_aml.iloc[:, i]
        t_stat, p_val = stats.ttest_ind(all_expr, aml_expr, equal_var=False)
        t_stats.append(t_stat)
        p_values.append(p_val)
        mean_diffs.append(all_expr.mean() - aml_expr.mean())

        s1 = all_expr.std(ddof=1)
        s2 = aml_expr.std(ddof=1)
        n1 = len(all_expr)
        n2 = len(aml_expr)
        s_pooled = np.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
        d = (all_expr.mean() - aml_expr.mean()) / s_pooled if s_pooled != 0 else 0
        cohen_d.append(d)

    t_stats = np.array(t_stats)
    p_values = np.array(p_values)
    q_values = benjamini_hochberg(p_values)

    diff_expr_df = pd.DataFrame({
        'Gene': gene_names,
        'Accession': gene_accession,
        't_stat': t_stats,
        'p_value': p_values,
        'q_value': q_values,
        'mean_diff': mean_diffs,
        'cohen_d': cohen_d,
        'abs_t': np.abs(t_stats)
    }).sort_values('q_value')

    diff_expr_df.to_csv(charts_dir / 'differential_expression_summary.csv', index=False)

    # Volcano plot with clear labeling for top signals
    min_val = X_train.values.min()
    shift = 1 - min_val if min_val <= 0 else 0
    mean_all = X_all.mean(axis=0)
    mean_aml = X_aml.mean(axis=0)
    log2fc = np.log2((mean_all + shift) / (mean_aml + shift))
    neg_log_q = -np.log10(diff_expr_df['q_value'].values + 1e-12)
    sig_mask = diff_expr_df['q_value'].values < 0.05

    plt.figure(figsize=(9, 6))
    plt.scatter(log2fc[~sig_mask], neg_log_q[~sig_mask], s=10, alpha=0.35, color='#6b7280', label='Not significant')
    plt.scatter(log2fc[sig_mask], neg_log_q[sig_mask], s=18, alpha=0.75, color='#111827', label='FDR < 0.05')
    plt.axhline(-np.log10(0.05), color='#dc2626', linestyle='--', linewidth=1)
    plt.title('Volcano Plot: Shifted log2(ALL/AML) vs -log10(FDR)')
    plt.xlabel('Shifted log2 Fold Change (ALL / AML)')
    plt.ylabel('-log10(FDR)')
    plt.legend(frameon=True, loc='upper right')

    # Annotate top 8 by absolute t-statistic with numeric FDR
    top_annotate = diff_expr_df.sort_values('abs_t', ascending=False).head(8).index
    for idx in top_annotate:
        label = shorten_labels([gene_names[idx]], 18)[0]
        fdr_val = diff_expr_df.loc[idx, 'q_value']
        plt.text(
            log2fc[idx], neg_log_q[idx],
            f"{label}\\nFDR={fdr_val:.3g}",
            fontsize=8, ha='left', va='bottom'
        )

    plt.tight_layout()
    plt.savefig(charts_dir / 'volcano_plot.png')
    plt.close()

    # Top 12 genes by effect size (Cohen's d)
    top_n = 12
    top_genes = diff_expr_df.sort_values('abs_t', ascending=False).head(top_n).copy()
    top_genes['GeneShort'] = shorten_labels(top_genes['Gene'].tolist(), 32)
    top_genes = top_genes.iloc[::-1]

    plt.figure(figsize=(10, 6))
    colors = ['#2563eb' if d > 0 else '#dc2626' for d in top_genes['cohen_d']]
    ax = plt.barh(top_genes['GeneShort'], top_genes['cohen_d'], color=colors)
    plt.axvline(0, color='#111827', linewidth=1)
    plt.title('Top 12 Genes by Effect Size (Cohen?s d)')
    plt.xlabel('Effect Size (ALL > AML positive)')
    plt.ylabel('Gene')
    for bar, val in zip(ax, top_genes['cohen_d']):
        plt.text(val, bar.get_y() + bar.get_height() / 2, f'{val:.2f}',
                 va='center', ha='left' if val >= 0 else 'right', fontsize=9)
    plt.tight_layout()
    plt.savefig(charts_dir / 'top12_effect_size.png')
    plt.close()

    # Mean +/- 95% CI for top 4 discriminative genes (more readable than boxplots)
    top4 = diff_expr_df.sort_values('abs_t', ascending=False).head(4)
    top4_idx = top4.index.tolist()
    summary_rows = []
    for idx in top4_idx:
        gene = gene_names[idx]
        for cls in ['ALL', 'AML']:
            vals = X_train.iloc[:, idx].values[y_train == cls]
            mean = np.mean(vals)
            se = stats.sem(vals)
            ci95 = 1.96 * se
            summary_rows.append({
                'Gene': shorten_labels([gene], 26)[0],
                'Class': cls,
                'Mean': mean,
                'CI95': ci95
            })
    summary_df = pd.DataFrame(summary_rows)

    plt.figure(figsize=(10, 6))
    ax = sns.pointplot(
        data=summary_df, x='Gene', y='Mean', hue='Class',
        palette=['#2563eb', '#dc2626'], dodge=0.35, linestyle='none', markers='o',
        err_kws={'linewidth': 1.2}, capsize=0.12
    )
    for _, row in summary_df.iterrows():
        x_pos = list(summary_df['Gene'].unique()).index(row['Gene'])
        offset = -0.2 if row['Class'] == 'ALL' else 0.2
        plt.text(x_pos + offset, row['Mean'], f"{row['Mean']:.0f}",
                 ha='center', va='bottom', fontsize=9)
    plt.title('Top 4 Discriminative Genes: Mean Expression (95% CI)')
    plt.xlabel('Gene')
    plt.ylabel('Expression Value')
    plt.legend(title='Diagnosis')
    plt.tight_layout()
    plt.savefig(charts_dir / 'top4_genes_means.png')
    plt.close()

    # PCA scatter
    scaler_all = StandardScaler()
    X_scaled = scaler_all.fit_transform(X_train)
    pca = PCA(n_components=2)
    pcs = pca.fit_transform(X_scaled)
    pca_df = pd.DataFrame({'PC1': pcs[:, 0], 'PC2': pcs[:, 1], 'Class': y_train})

    plt.figure(figsize=(7, 6))
    sns.scatterplot(data=pca_df, x='PC1', y='PC2', hue='Class',
                    palette=['#2563eb', '#dc2626'], s=90, edgecolor='black')
    plt.title('PCA of Training Samples')
    plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% var)')
    plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% var)')
    plt.legend(title='Diagnosis')
    plt.tight_layout()
    plt.savefig(charts_dir / 'pca_scatter.png')
    plt.close()

    # Correlation distributions (ALL-ALL, AML-AML, Cross)
    corr = np.corrcoef(X_train.values)
    labels_arr = np.array(y_train)
    pairs = []
    for i in range(corr.shape[0]):
        for j in range(i + 1, corr.shape[1]):
            if labels_arr[i] == 'ALL' and labels_arr[j] == 'ALL':
                grp = 'ALL-ALL'
            elif labels_arr[i] == 'AML' and labels_arr[j] == 'AML':
                grp = 'AML-AML'
            else:
                grp = 'ALL-AML'
            pairs.append({'PairType': grp, 'Correlation': corr[i, j]})
    corr_df = pd.DataFrame(pairs)

    plt.figure(figsize=(8, 5))
    ax = sns.boxplot(data=corr_df, x='PairType', y='Correlation', hue='PairType',
                     palette=['#2563eb', '#dc2626', '#111827'], legend=False)
    plt.title('Inter-sample Correlation by Pair Type')
    plt.xlabel('Pair Type')
    plt.ylabel('Correlation')

    # Add median labels
    med = corr_df.groupby('PairType')['Correlation'].median()
    for i, grp in enumerate(['ALL-ALL', 'AML-AML', 'ALL-AML']):
        plt.text(i, med[grp], f'{med[grp]:.2f}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(charts_dir / 'correlation_by_pair.png')
    plt.close()

    # Save summary
    summary_path = charts_dir / 'analysis_summary.txt'
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write('Gene Expression Analysis Summary\n')
        f.write('===============================\n')
        f.write(f'Genes: {X_train.shape[1]}\n')
        f.write(f'Training samples: {X_train.shape[0]}\n')
        f.write(f'Test samples: {X_test.shape[0]}\n')
        f.write(f'Train class counts: {counts.to_dict()}\n')
        f.write(f'Test class counts: {pd.Series(y_test).value_counts().to_dict()}\n')
        f.write(f'FDR < 0.05 genes: {(diff_expr_df["q_value"] < 0.05).sum()}\n')


if __name__ == '__main__':
    main()
