import os

import pytest

from routing_monitor.app import load_config

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.yaml")


@pytest.fixture
def config():
    return load_config(CONFIG_PATH)
