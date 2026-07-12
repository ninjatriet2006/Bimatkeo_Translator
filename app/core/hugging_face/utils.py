"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.hugging_face.utils
- RESPONSIBILITY: Handle YAML config updates and querying HuggingFace API for versions.
- CALLED BY: app.core.hugging_face.manager
- CALLS TO: None
- IN = OUT: Helper methods for config writing and version checking.
=============================================================================
"""
import os
import urllib.request
import json
from datetime import datetime
from ruamel.yaml import YAML

class HFConfigUpdater:
    def __init__(self):
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.default_flow_style = False

    def update_local_version(self, local_versions_file: str, key: str, model_name: str, version: str):
        """Records the downloaded version in local_versions.yaml."""
        local_versions = {}
        if os.path.exists(local_versions_file):
            with open(local_versions_file, "r", encoding="utf-8") as lf:
                local_versions = self.yaml.load(lf) or {}

        if key not in local_versions:
            local_versions[key] = {}

        local_versions[key][model_name] = version

        with open(local_versions_file, "w", encoding="utf-8") as lf:
            self.yaml.dump(local_versions, lf)

class HFVersionChecker:
    def __init__(self):
        pass

    def get_latest_version(self, repo_id: str) -> str:
        """
        Returns the latest version string.
        Format: v_{Date}_{ShortHash} to satisfy user-readable requirements.
        """
        hf_endpoint = "https://huggingface.co"
        url = f"{hf_endpoint}/api/models/{repo_id}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                sha = data.get("sha", "")
                last_modified = data.get("lastModified", "")

                short_sha = sha[:7] if sha else "unknown"
                date_str = ""
                if last_modified:
                    try:
                        dt = datetime.strptime(last_modified, "%Y-%m-%dT%H:%M:%S.%fZ")
                        date_str = dt.strftime("%Y%m%d")
                    except Exception:
                        try:
                            dt = datetime.strptime(last_modified, "%Y-%m-%dT%H:%M:%S%z")
                            date_str = dt.strftime("%Y%m%d")
                        except Exception:
                            date_str = "unknown"

                if date_str and short_sha != "unknown":
                    return f"v_{date_str}_{short_sha}"
                return short_sha
        except Exception as e:
            raise RuntimeError(f"Error fetching HuggingFace version for {repo_id}: {e}")
