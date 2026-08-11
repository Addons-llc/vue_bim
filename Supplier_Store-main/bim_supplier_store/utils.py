import re
from urllib.parse import urlsplit


STORE_CODE_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize_store_code(value: str | None) -> str:
	value = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower())
	return value.strip("-")


def validate_store_code(value: str | None) -> bool:
	return bool(STORE_CODE_PATTERN.fullmatch(value or ""))


def normalize_hostname(value: str | None) -> str:
	value = (value or "").strip().lower()
	if not value:
		return ""
	parsed = urlsplit(value if "://" in value else f"//{value}")
	hostname = (parsed.hostname or "").rstrip(".")
	try:
		return hostname.encode("idna").decode("ascii")
	except UnicodeError:
		return ""

