"""M0 gate: the package imports and exposes the documented public surface."""

import nspk


def test_package_exposes_evaluate():
    assert hasattr(nspk, "evaluate")
    assert callable(nspk.evaluate)


def test_version_is_pep440_ish():
    assert isinstance(nspk.__version__, str)
    assert nspk.__version__.count(".") == 2
