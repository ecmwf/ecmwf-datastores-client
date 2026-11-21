# Copyright 2022, European Union.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import os
import warnings

SUPPORTED_API_VERSION = "v1"
CONFIG_PREFIX = "ecmwf_datastores"
LEGACY_RC_FILE = "~/.cdsapirc"
LEGACY_RC_ENV_VAR = "CDSAPI_RC"


def _parse_config(path: str) -> dict[str, str]:
    try:
        config = {}
        with open(path) as f:
            for line in f.readlines():
                if ":" in line:
                    key, value = line.strip().split(":", 1)
                    config[key] = value.strip()
        return config
    except FileNotFoundError:
        raise
    except Exception:
        raise ValueError(f"Failed to parse {path!r} file")


def read_config(path: str | None = None) -> dict[str, str]:
    rc_env_var = f"{CONFIG_PREFIX}_RC_FILE".upper()
    use_default = path is None and rc_env_var not in os.environ
    if path is None:
        path = os.getenv(
            rc_env_var,
            f"~/.{CONFIG_PREFIX}rc".replace("_", "").lower(),
        )
    path = os.path.expanduser(path)
    try:
        return _parse_config(path)
    except FileNotFoundError:
        # Raise if the user provided config to an rc_env_var that does not exist.
        if not use_default:
            raise

        # If using defaults, check for legacy config file and warn the user.
        legacy_from_env = LEGACY_RC_ENV_VAR in os.environ
        legacy_path = os.path.expanduser(os.getenv(LEGACY_RC_ENV_VAR, LEGACY_RC_FILE))
        if not os.path.exists(legacy_path):
            raise
        if legacy_from_env:
            warnings.warn(
                f"Using credentials from the legacy {LEGACY_RC_ENV_VAR!r} "
                f"environment variable. Please rename it to {rc_env_var!r}. "
                "Support for the legacy environment variable will be removed in version 2.0.",
                UserWarning,
                stacklevel=2,
            )
        else:
            warnings.warn(
                f"{path!r} not found; falling back to legacy credentials file "
                f"{legacy_path!r}. Please migrate your credentials to {path!r}. "
                "Support for the legacy credentials file will be removed in version 2.0.",
                UserWarning,
                stacklevel=2,
            )
        return _parse_config(legacy_path)


def get_config(key: str, config_path: str | None = None) -> str:
    return os.getenv(f"{CONFIG_PREFIX}_{key}".upper()) or read_config(config_path)[key]
