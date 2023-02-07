import numpy as np


def round_log(i, bins_per_log_unit: int = 2):
    """Return the logarithm of a number rounded by a number of bins per unit"""
    return np.floor((np.log(i) * bins_per_log_unit)) / bins_per_log_unit


def get_round_log_range(log_bin, bins_per_log_unit: int = 2):
    exp_bin_min = np.ceil(np.exp(log_bin))
    exp_bin_max = np.floor(np.exp(log_bin + 1/bins_per_log_unit))
    return exp_bin_min, exp_bin_max

