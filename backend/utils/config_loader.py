from pathlib import Path

import yaml  # type: ignore[import-untyped]

from models.portal_config import PortalConfig


def load_portal_configs(configs_dir: Path | None = None) -> dict[str, PortalConfig]:
    """
    Scans the portal_configs directory for all .yaml or .yml files,
    parses them, validates them against the PortalConfig Pydantic model,
    and returns a dictionary keyed by the portal's unique 'portal_id'.

    Args:
        configs_dir: Optional path to the directory containing portal configs.
                     If not provided, defaults to 'backend/portal_configs'.

    Returns:
        A dictionary mapping portal_id to PortalConfig objects.

    Raises:
        FileNotFoundError: If the configs directory does not exist.
        ValueError: If a YAML file is invalid or fails Pydantic schema validation.
    """
    if configs_dir is None:
        # Default path relative to this file: c:\Users\...\backend\utils\..\portal_configs
        configs_dir = Path(__file__).resolve().parent.parent / "portal_configs"

    if not configs_dir.exists():
        raise FileNotFoundError(f"Portal configurations directory does not exist at: {configs_dir}")

    configs: dict[str, PortalConfig] = {}

    # Scan for both .yaml and .yml extensions
    yaml_files = list(configs_dir.glob("*.yaml")) + list(configs_dir.glob("*.yml"))

    for file_path in yaml_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                raw_data = yaml.safe_load(f)

            if raw_data is None:
                continue  # Skip empty files

            # Validate raw dict against Pydantic schema
            portal_config = PortalConfig(**raw_data)

            # Key by portal_id (e.g. 'nobroker', '99acres')
            configs[portal_config.portal_id] = portal_config

        except Exception as e:
            raise ValueError(f"Failed to parse or validate config file '{file_path.name}': {e}") from e

    return configs
