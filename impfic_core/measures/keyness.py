from typing import Dict, Iterable, Set, Tuple, Union
from collections import Counter

import numpy as np
import pandas as pd


_SMALL = 1e-20


def get_group_keyness(group_freq, group_totals, groups=None):
    group_keyness = pd.DataFrame()
    if groups is None:
        groups = group_freq.columns
    for group in groups:
        group_keyness[group] = group_freq.apply(lambda x: compute_log_likelihood_from_row(x, group, group_totals),
                                                axis=1)
    return group_keyness


def calculate_group_totals(reviews, group_col, count_col):
    group_totals = get_totals_from_df(reviews, group_col, count_col)
    group_totals.loc['Total'] = [group_totals.target_freq.sum(), 0]
    group_totals['total_freq'] = group_totals.sum(axis=1)
    return group_totals


def calculate_group_freqs(occurrences, group_col, count_col):
    group_occurrences = occurrences.groupby([group_col])[count_col].value_counts()
    group_occurrences = group_occurrences.unstack().T.fillna(0.0)
    group_occurrences['Total'] = group_occurrences.sum(axis=1)
    return group_occurrences


def calculate_percentage_diff(group_frac, groups):
    group_frac[groups].div(group_frac.Total, axis=0)
    return (group_frac[groups].T - group_frac.Total).T.div(group_frac.Total, axis=0) * 100


def get_percentage_diff(reviews, occurrences, group_col, total_count_col, occurrence_count_col):
    # determine groups
    groups = list(reviews[group_col].unique())
    # add group totals
    group_totals = calculate_group_totals(reviews, group_col, total_count_col)
    # calculate group frequencies
    group_occurrences = calculate_group_freqs(occurrences, group_col, occurrence_count_col)
    # calculate group fractions
    group_occurrences_frac = group_occurrences / group_totals.target_freq

    # calculate group differences
    return calculate_percentage_diff(group_occurrences_frac, groups)


def get_totals_from_df(df, category_column, freq_column):
    totals = df.groupby(category_column)[freq_column].sum()
    totals = totals.reset_index().rename(columns={freq_column: 'target_freq'})
    n_total = totals.target_freq.sum()
    totals['ref_freq'] = n_total - totals.target_freq
    totals = totals.set_index(category_column)
    return totals


def get_observed_from_columns(row, target_col, ref_col, totals):
    t_target = row[target_col]
    # print('t_target:', t_target)
    t_ref = row[ref_col]
    # print('t_ref:', t_ref)
    # print('total target:', totals.loc[target_col])
    nt_target = totals.loc[target_col] - t_target
    nt_ref = totals.loc[ref_col] - t_ref
    # print('nt_target:', nt_target)
    # print('nt_ref:', nt_ref)
    observed = np.array([
        [t_target, t_ref],
        [nt_target, nt_ref]
    ])
    return observed


def get_observed_from_row(row, source, totals):
    t_target = row[source]
    t_ref = get_complement_from_row(row, source)
    nt_target = totals.loc[source].target_freq - t_target
    nt_ref = totals.loc[source].ref_freq - t_ref
    observed = np.array([
        [t_target, t_ref],
        [nt_target, nt_ref]
    ])
    return observed


def get_complement_from_row(row, source):
    return row['Total'] - row[source]


def get_observed_from_counter(token: str, target_counter: Counter, target_total: int,
                              reference_counter: Counter, reference_total: int):
    """Computes the contingency table of the observed values given a target token, and
    target and reference analysers and counters."""
    # a: word in target corpus
    t_target = target_counter[token] if token in target_counter else 0
    # b: word in ref corpus
    t_ref = reference_counter[token] if token in reference_counter else 0
    # c: other words in target corpus
    nt_target = target_total - t_target
    # d: other words in ref corpus
    nt_ref = reference_total - t_ref

    observed = np.array([
        [t_target, t_ref],
        [nt_target, nt_ref]
    ])
    return observed


def compute_expected(observed: np.array) -> np.array:
    """Computes the contingency table of the expected values given a contingency table
    of the observed values."""
    expected = np.array([
        [
            observed[0, :].sum() * observed[:, 0].sum() / observed.sum(),
            observed[0, :].sum() * observed[:, 1].sum() / observed.sum()
        ],
        [
            observed[1, :].sum() * observed[:, 0].sum() / observed.sum(),
            observed[1, :].sum() * observed[:, 1].sum() / observed.sum()
        ]
    ])
    return expected


def compute_log_likelihood_from_columns(row, target_col, ref_col, totals):
    observed = get_observed_from_columns(row, target_col, ref_col, totals)
    # print(observed)
    ll, sign = compute_log_likelihood_from_observed(observed)
    return ll
    # return ll if sign == 'more' else -ll


def compute_log_likelihood_from_row(row, source, totals):
    observed = get_observed_from_row(row, source, totals)
    ll, sign = compute_log_likelihood_from_observed(observed)
    # row[f'keyness_{source}'] = ll if sign == 'more' else -ll
    return ll if sign == 'more' else -ll
    # return row


def compute_log_likelihood_from_counter(token: str, target_counter: Counter, target_total: int,
                                        reference_counter: Counter, reference_total: int) -> Tuple[float, str]:
    observed = get_observed_from_counter(token, target_counter, target_total, reference_counter,
                                         reference_total)
    return compute_log_likelihood_from_observed(observed)


def compute_log_likelihood_from_observed(observed: np.array) -> Tuple[float, str]:
    """Computes the log likelihood ratio for given a target token, and target and
    reference analysers and counters."""
    sum_likelihood = 0
    expected = compute_expected(observed)
    for i in [0, 1]:
        for j in [0, 1]:
            sum_likelihood += observed[i, j] * np.log((observed[i, j] + _SMALL) / (expected[i, j] + _SMALL))
    return 2 * sum_likelihood, 'more' if observed[0, 0] > expected[0, 0] else 'less'


def get_keyness_vocab(target_counter: Counter, reference_counter: Counter) -> Set[str]:
    return set(list(target_counter.keys()) + list(reference_counter.keys()))


def compute_keyness_from_counter(target_counter: Counter, reference_counter: Counter,
                                 vocab: Iterable[str] = None):
    """Compute the keyness score of each token in vocabulary for a given target
    counter and reference counter (available counters are 'all', 'start', 'mid'
    or 'end).

    The return value is a dictionary with two properties, 'less' and 'more', each
    with a Counter object. The 'less' counter contains the log likelihood ratio
    for tokens that are less common in the target counter than in the reference
    counter. The 'more' counter contains the log likelihood ratio for tokens that
    are more common in the target counter than in the reference counter.

    :param target_counter: the counter used for token frequencies of the target
    corpus (possible values: 'all', 'start', 'mid' or 'end')
    :type target_counter: str
    :param reference_counter: the counter used for token frequencies of the
    reference corpus (possible values: 'all', 'start', 'mid' or 'end')
    :param vocab: an optional vocabulary for which to compute keyness values.
    :type vocab: Iterable[str]
    """
    log_likelihood = {
        'less': Counter(),
        'more': Counter()
    }
    if vocab is None:
        vocab = set(list(target_counter.keys()) +
                    list(reference_counter.keys()))
    target_total = sum(target_counter.values())
    reference_total = sum(reference_counter.values())
    for token in vocab:
        ll, pref = compute_log_likelihood_from_counter(token, target_counter, target_total,
                                                       reference_counter, reference_total)
        log_likelihood[pref][token] = ll
    return log_likelihood
