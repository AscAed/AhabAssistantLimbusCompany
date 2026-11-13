import hashlib
import shutil
from unittest.mock import patch

import pytest

from module.resource_sync.manifest import ResourceFileEntry, ResourceManifest, ResourcePackageEntry
from module.resource_sync.service import ResourceCheckResult, ResourceCheckStatus, ResourceSyncPlan, ResourceSyncService
from module.resource_sync.source import ResourceSource


@pytest.mark.parametrize("path", ["../outside.png", "nested/../../outside.png", r"..\outside.png"])
def test_resource_file_entry_rejects_parent_traversal_paths(path):
    with pytest.raises(ValueError):
        ResourceFileEntry.from_dict({"path": path, "sha256": "hash", "size": 1})
    with pytest.raises(ValueError):
        ResourceFileEntry(path=path, sha256="hash", size=1)


@pytest.mark.parametrize(
    "path",
    [
        "", ".", "/outside.png", r"\outside.png", "C:/outside.png", "C:outside.png",
        r"\\server\share\outside.png", "nested/image.png:stream", "nested/.. /outside.png",
    ],
)
def test_resource_file_entry_rejects_absolute_and_drive_paths(path):
    with pytest.raises(ValueError):
        ResourceFileEntry.from_dict({"path": path, "sha256": "hash", "size": 1})


@pytest.mark.parametrize("path", [None, 1, [], {}])
def test_resource_entries_reject_non_string_paths(path):
    with pytest.raises(ValueError):
        ResourceFileEntry.from_dict({"path": path, "sha256": "hash", "size": 1})
    with pytest.raises(ValueError):
        ResourcePackageEntry.from_dict(
            {"path": path, "sha256": "hash", "size": 1, "format": "7z"}
        )


@pytest.mark.parametrize("path", ["../package.7z", "/package.7z", "C:package.7z", r"\\server\share\package.7z", ""])
def test_resource_package_entry_rejects_unsafe_paths(path):
    with pytest.raises(ValueError):
        ResourcePackageEntry(path=path, sha256="hash", size=1, format="7z")


def test_resource_entries_normalize_valid_nested_paths():
    entry = ResourceFileEntry.from_dict({"path": r"nested\image.png", "sha256": "hash", "size": 1})
    package = ResourcePackageEntry(path="packages/./images.7z", sha256="hash", size=1, format="7z")

    assert entry.path == "nested/image.png"
    assert package.path == "packages/images.7z"


def _sync_fixture(tmp_path, monkeypatch, payload):
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    service = ResourceSyncService(
        assets_dir=assets_dir,
        state_path=tmp_path / "state.json",
        temp_dir=tmp_path / "temp",
    )
    package = ResourcePackageEntry(
        path="payload.7z",
        sha256=hashlib.sha256(payload).hexdigest(),
        size=len(payload),
        format="7z",
    )
    result = ResourceCheckResult(
        status=ResourceCheckStatus.UPDATE_AVAILABLE,
        source=ResourceSource("test", "https://example.invalid/manifest.json"),
        remote_manifest=ResourceManifest(manifest_id="test", package=package),
    )

    def download(_source, _package, target):
        target.write_bytes(payload)
        return target

    monkeypatch.setattr(service, "_download_resource_package", download)
    monkeypatch.setattr(service, "_refresh_runtime_image_cache", lambda: None)
    return service, result


@pytest.mark.parametrize("operation", ["copy", "delete"])
def test_resource_sync_never_copies_or_deletes_outside_assets_root(tmp_path, monkeypatch, operation):
    sentinel = tmp_path / "payload.7z"
    sentinel.write_bytes(b"keep outside assets")
    payload = b"untrusted package bytes"
    service, result = _sync_fixture(tmp_path, monkeypatch, payload)

    def extract(_package, target):
        target.mkdir()
        return target

    monkeypatch.setattr(service, "_extract_resource_package", extract)
    if operation == "copy":
        entry = ResourceFileEntry(path="valid.png", sha256=hashlib.sha256(payload).hexdigest(), size=len(payload))
        entry.path = "../payload.7z"
        plan = ResourceSyncPlan(files_to_add=[entry])
    else:
        plan = ResourceSyncPlan(files_to_delete=["../payload.7z"])

    with pytest.raises(ValueError):
        service.apply_sync_plan(check_result=result, sync_plan=plan)

    assert sentinel.read_bytes() == b"keep outside assets"


def test_resource_sync_applies_valid_nested_paths(tmp_path, monkeypatch):
    payload = b"new image bytes"
    service, result = _sync_fixture(tmp_path, monkeypatch, payload)
    old_file = service.assets_dir / "nested" / "old.png"
    old_file.parent.mkdir()
    old_file.write_bytes(b"old image")
    entry = ResourceFileEntry(
        path="nested/new.png",
        sha256=hashlib.sha256(payload).hexdigest(),
        size=len(payload),
    )

    def extract(_package, target):
        image = target / "nested" / "new.png"
        image.parent.mkdir(parents=True)
        image.write_bytes(payload)
        return target

    monkeypatch.setattr(service, "_extract_resource_package", extract)
    result.remote_manifest.files = [entry]
    applied = service.apply_sync_plan(
        check_result=result,
        sync_plan=ResourceSyncPlan(files_to_add=[entry], files_to_delete=["nested/old.png"]),
    )

    assert (service.assets_dir / "nested" / "new.png").read_bytes() == payload
    assert not old_file.exists()
    assert applied.downloaded_count == 1
    assert applied.deleted_count == 1


def test_resource_sync_retries_after_partial_copy_failure(tmp_path, monkeypatch):
    payload = b"new image bytes"
    service, result = _sync_fixture(tmp_path, monkeypatch, payload)
    entries = [
        ResourceFileEntry(
            path=f"nested/{name}.png",
            sha256=hashlib.sha256(payload).hexdigest(),
            size=len(payload),
        )
        for name in ("first", "second")
    ]
    result.remote_manifest.files = entries
    old_file = service.assets_dir / "nested" / "old.png"
    old_file.parent.mkdir(parents=True)
    old_file.write_bytes(b"old image")

    def extract(_package, target):
        target.mkdir()
        for entry in entries:
            image = target / entry.path
            image.parent.mkdir(parents=True, exist_ok=True)
            image.write_bytes(payload)
        return target

    monkeypatch.setattr(service, "_extract_resource_package", extract)
    original_copy2 = shutil.copy2
    copy_calls = 0

    def fail_second_copy(source, destination):
        nonlocal copy_calls
        copy_calls += 1
        if copy_calls == 2:
            raise OSError("disk full")
        return original_copy2(source, destination)

    plan = ResourceSyncPlan(
        files_to_add=entries,
        files_to_delete=["nested/old.png"],
    )
    with patch("module.resource_sync.service.shutil.copy2", side_effect=fail_second_copy):
        with pytest.raises(OSError, match="disk full"):
            service.apply_sync_plan(check_result=result, sync_plan=plan)

    assert (service.assets_dir / entries[0].path).read_bytes() == payload
    assert not (service.assets_dir / entries[1].path).exists()
    assert old_file.read_bytes() == b"old image"
    assert not service.state_path.exists()
    assert not service.temp_dir.exists()

    applied = service.apply_sync_plan(check_result=result, sync_plan=plan)

    assert all((service.assets_dir / entry.path).read_bytes() == payload for entry in entries)
    assert not old_file.exists()
    assert applied.downloaded_count == 2
    assert applied.deleted_count == 1
    assert service.load_state().last_applied_manifest_id == "test"


def test_resource_sync_retries_after_partial_delete_failure(tmp_path, monkeypatch):
    service, result = _sync_fixture(tmp_path, monkeypatch, b"package")
    first_file = service.assets_dir / "obsolete-first.png"
    second_file = service.assets_dir / "obsolete-second.png"
    first_file.write_bytes(b"first obsolete image")
    second_file.write_bytes(b"second obsolete image")
    plan = ResourceSyncPlan(files_to_delete=["obsolete-first.png", "obsolete-second.png"])
    original_unlink = first_file.unlink

    def fail_second_delete(path, *args, **kwargs):
        if path == second_file:
            raise PermissionError("file is in use")
        return original_unlink.__func__(path, *args, **kwargs)

    with patch("module.resource_sync.service.Path.unlink", new=fail_second_delete):
        with pytest.raises(PermissionError, match="file is in use"):
            service.apply_sync_plan(check_result=result, sync_plan=plan)

    assert not first_file.exists()
    assert second_file.read_bytes() == b"second obsolete image"
    assert not service.state_path.exists()

    applied = service.apply_sync_plan(check_result=result, sync_plan=plan)

    assert not first_file.exists()
    assert not second_file.exists()
    assert applied.deleted_count == 1
    assert service.load_state().last_applied_manifest_id == "test"


def test_resource_sync_rejects_asset_link_outside_root(tmp_path, monkeypatch):
    service, result = _sync_fixture(tmp_path, monkeypatch, b"package")
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel.png"
    sentinel.write_bytes(b"keep linked file")
    try:
        (service.assets_dir / "linked").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Creating symbolic links is unavailable")

    with pytest.raises(ValueError):
        service.apply_sync_plan(
            check_result=result,
            sync_plan=ResourceSyncPlan(files_to_delete=["linked/sentinel.png"]),
        )

    assert sentinel.read_bytes() == b"keep linked file"
