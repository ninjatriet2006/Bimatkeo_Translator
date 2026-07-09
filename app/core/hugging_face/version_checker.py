"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.hugging_face.version_checker
- RESPONSIBILITY: Queries HuggingFace API to get the latest Git Tag Version, Last Modified Date, or Commit Hash.
- CALLED BY: app.core.hugging_face.manager
- CALLS TO: None
- IN = OUT: Returns a formatted version string. Do not hardcode 'hf_latest'. Must fetch real metadata.
========================================================================
"""
import urllib.request
import json
from datetime import datetime

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
                        # Example: '2023-10-15T10:00:00.000Z'
                        dt = datetime.strptime(last_modified, "%Y-%m-%dT%H:%M:%S.%fZ")
                        date_str = dt.strftime("%Y%m%d")
                    except Exception:
                        # Fallback for different time format
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
