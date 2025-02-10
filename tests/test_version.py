from __future__ import annotations

import adminactions


def test_version() -> None:
    assert adminactions.__version__ is not None
