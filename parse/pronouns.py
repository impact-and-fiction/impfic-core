import pandas as pd
import numpy as np


def get_pronoun_features(feature_string: str):
    feature_parts = feature_string.split("|")
    feature_map = {
        "pron_case": np.nan,
        "pron_poss": False,
        "pron_type": np.nan,
        "pron_pers": "0",
        "pron_card": "na",
        "pron_refl": False
    }
    num_features = len(feature_map)
    for feature in feature_parts:
        feature_name, feature_value = feature.lower().split("=")
        if feature_value == "yes":
            feature_value = True
        if feature_value == "no":
            feature_value = False
        if feature_name == "person":
            feature_name = "pron_pers"
        elif feature_name == "prontype":
            feature_name = "pron_type"
        elif feature_name == "reflex":
            feature_name = "pron_refl"
        else:
            feature_name = f"pron_{feature_name}"
        feature_map[feature_name] = feature_value
    if len(feature_map) != num_features:
        raise ValueError(f"unexpected number of features: {feature_string}")
    return list(feature_map.values())


def do_main():
    feature_string = "Case=Gen|Person=3|PronType=Prs|Card=evmo"
    pron = get_pronoun_features(feature_string)
    print(pron)


if __name__ == "__main__":
    do_main()