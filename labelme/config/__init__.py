import os
import os.path as osp
import shutil
import yaml
from labelme.logger import logger

here = osp.dirname(osp.abspath(__file__))


def update_dict(target_dict, new_dict, validate_item=None):
    for key, value in new_dict.items():
        if validate_item:
            validate_item(key, value)
        if key not in target_dict:
            logger.warn("Skipping unexpected key in config: {}".format(key))
            continue
        if isinstance(target_dict[key], dict) and isinstance(value, dict):
            update_dict(target_dict[key], value, validate_item=validate_item)
        else:
            target_dict[key] = value


# -----------------------------------------------------------------------------


def get_default_config():
    config_file = osp.join(here, "default_config.yaml")
    with open(config_file) as f:
        config = yaml.safe_load(f)

    # save default config to ~/.labelmerc
    user_config_file = osp.join(osp.expanduser("~"), ".labelmerc")
    if not osp.exists(user_config_file):
        try:
            shutil.copy(config_file, user_config_file)
        except Exception:
            logger.warn("Failed to save config: {}".format(user_config_file))

    return config

def get_app_version():
    config_file = osp.join(here, "default_config.yaml")
    appv = '20220918'
    with open(config_file) as f:
        config = yaml.safe_load(f)
    if 'app_version' in config:
        appv = config['app_version']
    return appv

def copy_to_version():
    config_file = osp.join(here, "default_config.yaml")
    user_config_file = osp.join(osp.expanduser("~"), ".labelmerc")
    if osp.isfile(user_config_file):
        try:
            os.remove(user_config_file)
        except Exception:
            logger.warn("Failed to remove config: {}".format(user_config_file))
        pass

    try:
        shutil.copy(config_file, user_config_file)
    except Exception:
        logger.warn("Failed to save config: {}".format(user_config_file))
    pass


def get_app_origin_val(config_file_or_yaml=None, key=None):
    if config_file_or_yaml is None:
        return None
    if key is None:
        return None
    if not osp.exists(config_file_or_yaml):
        return None
    config_from_yaml = yaml.safe_load(config_file_or_yaml)
    if not isinstance(config_from_yaml, dict):
        with open(config_from_yaml) as f:
            config_from_yaml = yaml.safe_load(f)
        if key in config_from_yaml:
            return config_from_yaml[key]
        return None

    return None

def validate_config_item(key, value):
    if key == "validate_label" and value not in [None, "exact"]:
        raise ValueError(
            "Unexpected value for config key 'validate_label': {}".format(
                value
            )
        )
    if key == "shape_color" and value not in [None, "auto", "manual"]:
        raise ValueError(
            "Unexpected value for config key 'shape_color': {}".format(value)
        )
    if key == "labels" and value is not None and len(value) != len(set(value)):
        raise ValueError(
            "Duplicates are detected for config key 'labels': {}".format(value)
        )


def get_config(config_file_or_yaml=None, config_from_args=None):
    # 1. default config
    config = get_default_config()

    # 2. specified as file or yaml
    if config_file_or_yaml is not None:
        config_from_yaml = yaml.safe_load(config_file_or_yaml)
        if not isinstance(config_from_yaml, dict):
            with open(config_from_yaml) as f:
                logger.info(
                    "Loading config file from: {}".format(config_from_yaml)
                )
                config_from_yaml = yaml.safe_load(f)
        update_dict(
            config, config_from_yaml, validate_item=validate_config_item
        )

    # 3. command line argument or specified config file
    if config_from_args is not None:
        update_dict(
            config, config_from_args, validate_item=validate_config_item
        )

    return config