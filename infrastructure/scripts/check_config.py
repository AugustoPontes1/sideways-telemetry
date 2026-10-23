"""Static checks not requiring Docker, suitable for WSL before deploying."""
from pathlib import Path
import sys
try:
    import yaml
except ImportError:
    sys.exit("Install PyYAML: pip install pyyaml")

root = Path(__file__).resolve().parents[2]
compose = yaml.safe_load((root / "infrastructure" / "compose.yaml").read_text())
services = compose["services"]
assert set(["db", "redis", "backend", "frontend", "haproxy"]).issubset(services)
for name in ("db", "redis", "backend", "frontend"):
    assert "ports" not in services[name], f"Do not expose {name} to host"
assert services["backend"]["build"]["context"] == ".."
assert services["haproxy"]["ports"]
assert compose["networks"]["data"]["internal"] is True
cfg = (root / "infrastructure" / "haproxy" / "haproxy.cfg").read_text()
assert "bind :443 ssl crt" in cfg
assert "timeout tunnel" in cfg
assert "http-request set-header X-Forwarded-Proto https" in cfg
nginx = (root / "frontend" / "deploy" / "nginx.conf").read_text()
assert "proxy_pass http://backend:8000" in nginx
assert "location /ws/" in nginx
print("Static Compose/HAProxy/Nginx integration checks passed")
