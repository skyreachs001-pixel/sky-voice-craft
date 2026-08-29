import os
import json
import time
import uuid
import threading
import urllib.request
import urllib.error

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PROFILES_FILE = os.path.join(DATA_DIR, "api_profiles.json")
LOCK = threading.Lock()

def mask_api_key(key: str) -> str:
    """Mask key for safe display: e.g. AIzaSy...9xQ2"""
    if not key:
        return ""
    clean = key.strip().strip('"\'')
    if len(clean) <= 10:
        return clean[:3] + "..."
    return f"{clean[:6]}...{clean[-4:]}"

def test_google_api_key(api_key: str) -> tuple[bool, str]:
    """Tests if a Google AI Studio API key is valid and active."""
    if not api_key:
        return False, "API key is empty"
    clean_key = api_key.strip().strip('"\'')
    if len(clean_key) < 10:
        return False, "API key too short"

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={clean_key}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VoiceCraftStudio/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                return True, "API Key is Active & Valid! 🟢"
            return False, f"HTTP Status: {resp.status}"
    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            pass
        if "API_KEY_INVALID" in err_body or e.code in (400, 403):
            return False, "Invalid API Key. Please verify in Google AI Studio."
        if e.code == 429:
            return False, "Rate limit reached (429). Key is valid but temporarily throttled."
        return False, f"API Error (HTTP {e.code}): {e.reason}"
    except Exception as e:
        return False, f"Network error: {str(e)}"

class KeyVaultManager:
    """Thread-safe Multi-Key Profile & Auto-Rotation Manager."""

    def __init__(self, storage_path=PROFILES_FILE):
        self.storage_path = storage_path
        self._current_index = 0
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self._ensure_storage()

    def _ensure_storage(self):
        with LOCK:
            if not os.path.exists(self.storage_path):
                default_data = {
                    "auto_switch_enabled": True,
                    "profiles": []
                }
                # Check if there is an existing key from SkyReachsAutomation config
                legacy_config = os.path.join(
                    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                    "SkyReachsAutomation", "voice_maker_config.json"
                )
                if os.path.exists(legacy_config):
                    try:
                        with open(legacy_config, "r", encoding="utf-8") as f:
                            c = json.load(f)
                            legacy_keys = [k.strip().strip('"\'') for k in str(c.get("api_key", "")).split(",") if k.strip()]
                            for i, lk in enumerate(legacy_keys, 1):
                                default_data["profiles"].append({
                                    "id": str(uuid.uuid4()),
                                    "name": f"Default Studio Key {i}" if len(legacy_keys) > 1 else "Primary Studio Key",
                                    "key": lk,
                                    "enabled": True,
                                    "status": "ACTIVE",
                                    "cooldown_until": 0,
                                    "requests_today": 0,
                                    "total_requests": 0,
                                    "last_error": None,
                                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
                                })
                    except Exception:
                        pass

                with open(self.storage_path, "w", encoding="utf-8") as f:
                    json.dump(default_data, f, indent=2)

    def _read_data(self) -> dict:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"auto_switch_enabled": True, "profiles": []}

    def _write_data(self, data: dict):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_all_profiles(self) -> list[dict]:
        """Returns all profiles with dynamic status and masked keys for safe UI rendering."""
        with LOCK:
            data = self._read_data()
            profiles = data.get("profiles", [])
            now = time.time()

            changed = False
            result = []
            for p in profiles:
                # Check cooldown recovery
                cooldown_until = p.get("cooldown_until", 0)
                if p.get("status") == "RATE_LIMITED" and now >= cooldown_until:
                    p["status"] = "ACTIVE"
                    p["cooldown_until"] = 0
                    p["last_error"] = None
                    changed = True

                cooldown_remaining = max(0, int(cooldown_until - now)) if cooldown_until > now else 0

                safe_p = {
                    "id": p["id"],
                    "name": p["name"],
                    "masked_key": mask_api_key(p["key"]),
                    "raw_key_preview": p["key"][:8] + "..." if p.get("key") else "",
                    "enabled": p.get("enabled", True),
                    "status": p.get("status", "ACTIVE"),
                    "cooldown_remaining": cooldown_remaining,
                    "requests_today": p.get("requests_today", 0),
                    "total_requests": p.get("total_requests", 0),
                    "last_error": p.get("last_error"),
                    "created_at": p.get("created_at", "")
                }
                result.append(safe_p)

            if changed:
                self._write_data(data)

            return result

    def get_metrics(self) -> dict:
        """Returns live banner metrics for the UI."""
        profiles = self.get_all_profiles()
        total = len(profiles)
        active = sum(1 for p in profiles if p["enabled"] and p["status"] == "ACTIVE" and p["cooldown_remaining"] == 0)
        cooling = sum(1 for p in profiles if p["enabled"] and (p["status"] == "RATE_LIMITED" or p["cooldown_remaining"] > 0))
        error = sum(1 for p in profiles if p["status"] == "ERROR")

        data = self._read_data()
        return {
            "total_keys": total,
            "active_keys": active,
            "cooling_keys": cooling,
            "error_keys": error,
            "auto_switch_enabled": data.get("auto_switch_enabled", True)
        }

    def set_auto_switch(self, enabled: bool):
        with LOCK:
            data = self._read_data()
            data["auto_switch_enabled"] = bool(enabled)
            self._write_data(data)

    def add_profile(self, name: str, key: str, validate: bool = True) -> tuple[bool, str, dict]:
        """Add a new API Profile. Validates with Google first if validate=True."""
        clean_name = (name or "New Key Profile").strip()
        clean_key = key.strip().strip('"\'')
        if not clean_key:
            return False, "API key cannot be empty", {}

        if validate:
            is_valid, msg = test_google_api_key(clean_key)
            if not is_valid:
                return False, f"Validation Failed: {msg}", {}

        with LOCK:
            data = self._read_data()
            # Check duplicate keys
            for p in data.get("profiles", []):
                if p.get("key") == clean_key:
                    return False, f"This API Key is already added under profile '{p.get('name')}'", {}

            new_profile = {
                "id": str(uuid.uuid4()),
                "name": clean_name,
                "key": clean_key,
                "enabled": True,
                "status": "ACTIVE",
                "cooldown_until": 0,
                "requests_today": 0,
                "total_requests": 0,
                "last_error": None,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            data["profiles"].append(new_profile)
            self._write_data(data)

            return True, "API Key Profile saved & verified successfully! 🟢", new_profile

    def update_profile(self, profile_id: str, name: str = None, key: str = None, enabled: bool = None) -> tuple[bool, str]:
        with LOCK:
            data = self._read_data()
            target = None
            for p in data.get("profiles", []):
                if p["id"] == profile_id:
                    target = p
                    break
            if not target:
                return False, "Profile not found"

            if name is not None:
                target["name"] = name.strip() or target["name"]
            if key is not None and key.strip():
                clean_key = key.strip().strip('"\'')
                is_valid, msg = test_google_api_key(clean_key)
                if not is_valid:
                    return False, f"Validation Failed: {msg}"
                target["key"] = clean_key
                target["status"] = "ACTIVE"
                target["cooldown_until"] = 0
                target["last_error"] = None
            if enabled is not None:
                target["enabled"] = bool(enabled)

            self._write_data(data)
            return True, "Profile updated successfully"

    def delete_profile(self, profile_id: str) -> tuple[bool, str]:
        with LOCK:
            data = self._read_data()
            original_len = len(data.get("profiles", []))
            data["profiles"] = [p for p in data.get("profiles", []) if p["id"] != profile_id]
            if len(data["profiles"]) == original_len:
                return False, "Profile not found"
            self._write_data(data)
            return True, "Profile deleted successfully"

    def test_profile(self, profile_id: str) -> tuple[bool, str]:
        """Test a specific saved profile by ID and update its status."""
        with LOCK:
            data = self._read_data()
            target = None
            for p in data.get("profiles", []):
                if p["id"] == profile_id:
                    target = p
                    break
            if not target:
                return False, "Profile not found"
            key = target["key"]

        is_valid, msg = test_google_api_key(key)

        with LOCK:
            data = self._read_data()
            for p in data.get("profiles", []):
                if p["id"] == profile_id:
                    if is_valid:
                        p["status"] = "ACTIVE"
                        p["cooldown_until"] = 0
                        p["last_error"] = None
                    else:
                        if "429" in msg or "Rate limit" in msg:
                            p["status"] = "RATE_LIMITED"
                            p["cooldown_until"] = time.time() + 60
                        else:
                            p["status"] = "ERROR"
                        p["last_error"] = msg
                    break
            self._write_data(data)

        return is_valid, msg

    def test_all_profiles(self) -> dict:
        """Tests all saved profiles and updates their statuses."""
        with LOCK:
            data = self._read_data()
            profiles = list(data.get("profiles", []))

        results = {}
        for p in profiles:
            is_valid, msg = test_google_api_key(p["key"])
            results[p["id"]] = {"valid": is_valid, "message": msg}

        with LOCK:
            data = self._read_data()
            for p in data.get("profiles", []):
                if p["id"] in results:
                    res = results[p["id"]]
                    if res["valid"]:
                        p["status"] = "ACTIVE"
                        p["cooldown_until"] = 0
                        p["last_error"] = None
                    else:
                        if "429" in res["message"]:
                            p["status"] = "RATE_LIMITED"
                            p["cooldown_until"] = time.time() + 60
                        else:
                            p["status"] = "ERROR"
                        p["last_error"] = res["message"]
            self._write_data(data)

        return results

    def get_candidate_keys_for_generation(self) -> list[dict]:
        """
        Returns active, healthy keys sorted by round-robin priority.
        If all active keys are in cooldown, returns available keys with their cooldown info.
        """
        with LOCK:
            data = self._read_data()
            profiles = data.get("profiles", [])
            now = time.time()

            changed = False
            for p in profiles:
                if p.get("status") == "RATE_LIMITED" and now >= p.get("cooldown_until", 0):
                    p["status"] = "ACTIVE"
                    p["cooldown_until"] = 0
                    p["last_error"] = None
                    changed = True

            if changed:
                self._write_data(data)

            # Filter enabled
            enabled_profiles = [p for p in profiles if p.get("enabled", True)]
            if not enabled_profiles:
                return []

            # Separate fully active vs cooling down
            active_profiles = [p for p in enabled_profiles if p.get("status") == "ACTIVE" and now >= p.get("cooldown_until", 0)]

            if active_profiles:
                # Rotate starting from current index
                count = len(active_profiles)
                idx = self._current_index % count
                self._current_index = (self._current_index + 1) % count
                ordered = active_profiles[idx:] + active_profiles[:idx]
                return ordered

            # All enabled profiles are cooling down; return sorted by earliest cooldown expiry
            cooling_profiles = sorted(enabled_profiles, key=lambda x: x.get("cooldown_until", 0))
            return cooling_profiles

    def mark_rate_limited(self, profile_id: str, cooldown_seconds: int = 45):
        """Called when an API call returns HTTP 429."""
        with LOCK:
            data = self._read_data()
            for p in data.get("profiles", []):
                if p["id"] == profile_id:
                    p["status"] = "RATE_LIMITED"
                    p["cooldown_until"] = time.time() + cooldown_seconds
                    p["last_error"] = "Google API Rate Limit (HTTP 429) - In Cooldown"
                    break
            self._write_data(data)

    def mark_success(self, profile_id: str):
        """Called when an API call successfully completes."""
        with LOCK:
            data = self._read_data()
            for p in data.get("profiles", []):
                if p["id"] == profile_id:
                    p["status"] = "ACTIVE"
                    p["cooldown_until"] = 0
                    p["last_error"] = None
                    p["requests_today"] = p.get("requests_today", 0) + 1
                    p["total_requests"] = p.get("total_requests", 0) + 1
                    break
            self._write_data(data)
