import matplotlib.ticker as mticker
import numpy as np


def set_log_words_labels(ax, N: int = 8):
    ax.xaxis.set_major_locator(mticker.MaxNLocator(N))
    ticks_loc = ax.get_xticks().tolist()
    ax.xaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
    ax.set_xticklabels([f"{np.exp(x): >.0f}" for x in ticks_loc])


def set_no_corr_line(ax):
    ax.axhline(y=0.0, linestyle='--', color="black", linewidth=0.3)


def set_log_ticks(grid = None, ax = None):
    if grid:
        ticks_loc = grid.ax.get_xticks().tolist()
        ticks_loc = [i for i in range(int(ticks_loc[0]), int(ticks_loc[-1]) + 1)]
        lengths = [int(np.exp(t)) for t in ticks_loc]
        grid.ax.xaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
        grid.ax.set_xticklabels([f"{x}" for x in lengths])
    elif ax:
        ticks_loc = ax.get_xticks().tolist()
        ticks_loc = [i for i in range(int(ticks_loc[0]), int(ticks_loc[-1]) + 1)]
        lengths = [int(np.exp(t)) for t in ticks_loc]
        ax.xaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
        ax.set_xticklabels([f"{x}" for x in lengths])


