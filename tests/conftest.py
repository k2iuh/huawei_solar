"""Make the repository importable as custom_components.huawei_solar.

The repository root is the integration package itself, and it is named like the huawei_solar
library. Linking it into a temporary custom_components directory gives it the import path Home
Assistant uses, without shadowing the library.
"""

import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_PACKAGES = Path(tempfile.mkdtemp())
(_PACKAGES / "custom_components").mkdir()
(_PACKAGES / "custom_components" / "__init__.py").touch()
(_PACKAGES / "custom_components" / "huawei_solar").symlink_to(_ROOT)
sys.path.insert(0, str(_PACKAGES))
