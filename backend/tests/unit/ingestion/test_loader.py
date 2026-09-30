from dataclasses import FrozenInstanceError
from hashlib import sha256
from pathlib import Path

import pytest
from app.services.ingestion.loader import (
    SourceLoadError,
    load_source,
)

FIXTURE_DIRECTORY = Path(__file__).resolve().parents[2] / "fixtures" / "ingestion"


def test_loader_captures_immutable_hashed_local_source_version():
    expected_content = (FIXTURE_DIRECTORY / "policy.html").read_bytes()

    loaded = load_source("policy.html", source_root=FIXTURE_DIRECTORY)

    assert loaded.content == expected_content
    assert loaded.content_hash == sha256(expected_content).hexdigest()
    assert loaded.byte_size == len(expected_content)
    with pytest.raises(FrozenInstanceError):
        loaded.content = b"modified"


def test_loader_rejects_paths_outside_source_root():
    with pytest.raises(SourceLoadError, match="outside source_root"):
        load_source("../outside.html", source_root=FIXTURE_DIRECTORY)
