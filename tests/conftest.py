import importlib.util
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def load_source():
    def load(module_name, relative_path):
        spec = importlib.util.spec_from_file_location(
            module_name, PROJECT_ROOT / relative_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return load
