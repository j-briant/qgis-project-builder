from pathlib import Path
from typing import TextIO

import yaml


def load_config(conf_file) -> dict:
    """
    Load a configuration file after checking if the file exists.
    :rtype: dict
    :param str conf_file: path to the configuration file in yaml
    :return: a dictionary containing the parameters values
    """
    try:
        with open(conf_file) as yml:
            conf = yaml.safe_load(yml)
    except FileNotFoundError:
        raise FileNotFoundError
    return conf

