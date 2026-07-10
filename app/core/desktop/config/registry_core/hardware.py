import sys
import platform

_os_suffix = "win" if sys.platform.startswith('win') else ("macos" if sys.platform.startswith('darwin') else "linux")

class RegistryHardware:
    def __init__(self, registry_mixin):
        self.rm = registry_mixin

    def machine_fingerprint(self):
        try:
            return f"{platform.node()}|{platform.machine()}|{_os_suffix}"
        except Exception:
            return _os_suffix

    def optimize_profiles_once(self):
        try:
            studio = getattr(self.rm, "studio_config", None)
            oldsession = getattr(self.rm, "oldsession_config", None)
            if not isinstance(oldsession, dict):
                return

            fingerprint = self.machine_fingerprint()
            if oldsession.get("registry_optimized_for") == fingerprint:
                return

            total_changes = []

            if isinstance(studio, dict):
                default_settings = studio.get("default_settings")
                if isinstance(default_settings, dict):
                    if hasattr(self.rm, 'sweep_settings'):
                        changes = self.rm.sweep_settings(default_settings)
                        if changes:
                            total_changes.extend(("<defaults>", k, o, n) for (k, o, n) in changes)

            oldsession["registry_optimized_for"] = fingerprint
            try:
                self.rm.save_oldsession_config()
            except Exception as e:
                print(f"[Registry] optimize: could not persist oldsession_config: {e}")

            if total_changes:
                print(f"[Registry] optimize: repaired {len(total_changes)} model field(s):")
                for entry in total_changes:
                    print(f"           {entry[0]}: {entry[1]} -> {entry[2]} ({entry[3] if len(entry) > 3 else ''})")
            else:
                print("[Registry] optimize: all model fields valid for this machine.")
        except Exception as e:
            print(f"[Registry] optimize_profiles_once failed (non-fatal): {e}")
