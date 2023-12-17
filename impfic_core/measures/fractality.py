from typing import List, Union

import numpy as np


def generate_window_sizes(series, s_0: int = 16, min_windows: int = 3):
    s_max = len(series) / min_windows
    s = [s_0]
    s_i = s_0
    i = 1
    while s_i < s_max:
        index = i-1 if len(s) % 2 == 1 else i-2
        s_i = s[i-1] + np.power(2, (np.log(s[index])/np.log(2))-1)
        if s_i > s_max:
            break
        s.append(s_i)
        i += 1
    return s


def compute_series_profile(series: List[Union[float, int]]):
    series = series if isinstance(series, np.ndarray) else np.array(series)
    mean_dists = series - series.mean()
    return np.array([mean_dists[:k+1].sum() for k in range(0, len(mean_dists))])

def detrended_fluctuation_analysis(series: List[Union[float, int]]):
    # 1. Subtract the mean and compute the cumulative sum, called the profile, of the series: Y(i)=∑ik=1[xk−〈x〉],i=1,⋯,N
    # 2. Divide the profile of the signal into Ns = N/s windows for different values of s
    #
    # 3. Compute the local trend, Y′, which is the best fitting line (or polynomial), in each window
    #
    # 4. Calculate the mean square fluctuation of the detrended profile in each window v, v = 1, ⋯ , Ns : F2(s,v)=1s∑si=1[Y(s×(v−1)+i)−Y′(s×(v−1)+i)]2
    # 5. Calculate the qth order of the mean square fluctuation: Fq(s)={1Ns∑Nsv=1[F2(s,v)]q/2}1/q
    # 6. Determine the scaling behavior of Fq(s) vs. s: Fq(s)~sh(q)
    profile = compute_series_profile(series)

