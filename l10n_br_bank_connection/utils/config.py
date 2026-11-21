# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import dataclasses
import inspect
import types
import typing

# Generic provider credentials, by the name the adapters use in their config.
GENERIC_KEYS = (
    "conta",
    "client_id",
    "client_secret",
    "usuario",
    "senha",
    "ambiente",
    "certificado_pem",
    "chave_pem",
    "perfil",
    "chave_pix",
    "refresh_token",
    # Company CNPJ, URL overrides and consent scopes.
    "cnpj_empresa",
    "url_base_override",
    "url_token_override",
    "escopos_dda",
)
# Served by the caller although not typed `Callable` (the token store).
INJECTED_KEYS = ("armazem",)
SCALAR_TYPES = (bool, int, float, str, bytes)
NONE_TYPE = types.NoneType


class ConfigError(Exception):
    """The provider values do not build the adapter configuration."""

    def __init__(self, message, missing=(), unknown=(), misplaced=()):
        super().__init__(message)
        self.missing = tuple(missing)
        self.unknown = tuple(unknown)
        self.misplaced = tuple(misplaced)


def config_class(adapter_class):
    """Return the configuration dataclass taken by the adapter constructor."""
    try:
        hints = typing.get_type_hints(adapter_class.__init__)
    except Exception:  # pylint: disable=broad-except
        hints = {}
    candidate = hints.get("config")
    if candidate is None:
        parameter = inspect.signature(adapter_class.__init__).parameters.get("config")
        candidate = parameter.annotation if parameter else None
    if not dataclasses.is_dataclass(candidate):
        raise ConfigError(
            f"adapter {adapter_class.__name__} has no dataclass configuration"
        )
    return candidate


def _scalar_type(annotation):
    """The scalar type behind `annotation` (`int | None` -> `int`), or None."""
    if annotation in SCALAR_TYPES:
        return annotation
    arguments = [a for a in typing.get_args(annotation) if a is not NONE_TYPE]
    scalars = [a for a in arguments if a in SCALAR_TYPES]
    if len(arguments) == 1 and scalars:
        return scalars[0]
    return None


def describe(config_cls):
    """Describe the keys of a configuration dataclass (name, type, required, secret)."""
    hints = typing.get_type_hints(config_cls)
    result = []
    for field in dataclasses.fields(config_cls):
        if not field.init:
            continue
        required = (
            field.default is dataclasses.MISSING
            and field.default_factory is dataclasses.MISSING
        )
        if field.default is not dataclasses.MISSING:
            default = field.default
        elif field.default_factory is not dataclasses.MISSING:
            default = field.default_factory()
        else:
            default = None
        result.append(
            {
                "name": field.name,
                "type": _scalar_type(hints.get(field.name)),
                "default": default,
                "required": required,
                "secret": not field.repr,
                "generic": field.name in GENERIC_KEYS,
                "callable": "Callable" in str(hints.get(field.name))
                or field.name in INJECTED_KEYS,
            }
        )
    return result


JSON_TYPES = (bool, int, float, str, dict, list, NONE_TYPE)


def placeholder(key):
    """Value offered in the settings template: library default, null if required."""
    if key["required"]:
        return None
    default = key["default"]
    if isinstance(default, JSON_TYPES):
        return dict(default) if isinstance(default, dict) else default
    try:
        return dict(default)
    except (TypeError, ValueError):
        return None


def _coerce(key, value):
    target = key["type"]
    if value is None or target is None or isinstance(value, target):
        return value
    if target is bool and isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "sim")
    if target is bytes and isinstance(value, str):
        return value.encode()
    try:
        return target(value)
    except (TypeError, ValueError) as error:
        raise ConfigError(
            f"invalid value type for key {key['name']!r}", unknown=(key["name"],)
        ) from error


def build(config_cls, generic, public, secret, callbacks=None):
    """Instantiate `config_cls` from the provider values."""
    callbacks = callbacks or {}
    keys = {key["name"]: key for key in describe(config_cls)}
    unknown = sorted((set(public) | set(secret)) - set(keys))
    misplaced = sorted(name for name in public if keys.get(name, {}).get("secret"))
    if unknown or misplaced:
        raise ConfigError(
            "unknown or misplaced configuration keys",
            unknown=unknown,
            misplaced=misplaced,
        )
    values = {}
    for name, key in keys.items():
        if key["callable"]:
            if callbacks.get(name) is not None:
                values[name] = callbacks[name]
            continue
        if name in secret:
            value = secret[name]
        elif name in public:
            value = public[name]
        elif generic.get(name) not in (None, "", False, b""):
            value = generic[name]
        else:
            continue
        if value in (None, "") and not key["required"]:
            continue
        values[name] = _coerce(key, value)
    missing = sorted(
        name
        for name, key in keys.items()
        if key["required"] and values.get(name) in (None, "")
    )
    if missing:
        raise ConfigError("missing configuration keys", missing=missing)
    return config_cls(**values)
