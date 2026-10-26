"""
Shared helpers for the TravelBuddy backend test suite.

pytest adds the ``tests`` directory to ``sys.path`` (the directory has no
``__init__.py``), so test modules can simply use ``from helpers import ...``.
"""


def field(value):
    """
    Wraps a value in the form-field structure sent by the TravelBuddy frontend.

    Every form value travels as ``{"value": ..., "errors": [...], "isValid": ...}``
    so that validation errors can be attached to individual fields.
    """
    return {"value": value, "errors": [], "isValid": True}


def raise_error(*args, **kwargs):
    """
    Drop-in replacement for any callable that should fail.

    Used with ``monkeypatch.setattr`` to force a route into its error-handling
    branch, e.g. by simulating a failing ``db.session.commit``.
    """
    raise RuntimeError("Simulated failure")


def stub_validation(is_valid):
    """
    Returns a replacement for a ``*Validation.validate_*`` method.

    The real validators return ``(form_values, is_valid)``. The stub echoes the
    submitted form values back unchanged and reports the given ``is_valid``
    result, which lets route tests focus on route behavior instead of
    validation rules. Both positional and keyword calls are supported, because
    some routes pass the form data as a keyword argument.
    """

    def _validate(*args, **kwargs):
        form_values = args[0] if args else next(iter(kwargs.values()))
        return form_values, is_valid

    return _validate
