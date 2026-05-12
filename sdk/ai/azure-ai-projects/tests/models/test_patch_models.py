# pylint: disable=line-too-long,useless-suppression
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
"""Offline unit tests for ``azure.ai.projects.operations._patch_models``.

These tests do not contact the Foundry service. They cover the patch helpers
``_extract_pending_upload_targets`` and ``_run_azcopy``, and the orchestration
performed by ``register_model`` (mocking ``pending_upload``, ``create_async``
and ``get`` on the base class).
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from azure.core.exceptions import ResourceNotFoundError

from azure.ai.projects.operations._patch_models import BetaModelsOperations


# ---------------------------------------------------------------------------
# _extract_pending_upload_targets
# ---------------------------------------------------------------------------


class TestExtractPendingUploadTargets:
    def test_datastore_wire_shape(self):
        """The service currently returns ``blobReferenceForConsumption``."""
        payload = {
            "blobReferenceForConsumption": {
                "blobUri": "https://acct.blob.core.windows.net/c/path",
                "credential": {"sasUri": "https://acct.blob.core.windows.net/c/path?sig=abc"},
            },
            "temporaryDataReferenceId": "abc-123",
        }
        sas, blob, pid = BetaModelsOperations._extract_pending_upload_targets(payload)
        assert sas == payload["blobReferenceForConsumption"]["credential"]["sasUri"]
        assert blob == payload["blobReferenceForConsumption"]["blobUri"]
        assert pid == "abc-123"

    def test_modeled_wire_shape(self):
        """The SDK-modeled shape uses ``blobReference`` / ``pendingUploadId``."""
        payload = {
            "blobReference": {
                "blobUri": "https://acct.blob.core.windows.net/c/path",
                "credential": {"sasUri": "https://acct.blob.core.windows.net/c/path?sig=xyz"},
            },
            "pendingUploadId": "modeled-id",
        }
        sas, blob, pid = BetaModelsOperations._extract_pending_upload_targets(payload)
        assert sas == payload["blobReference"]["credential"]["sasUri"]
        assert blob == payload["blobReference"]["blobUri"]
        assert pid == "modeled-id"

    def test_response_object_with_as_dict(self):
        """Accept anything exposing ``.as_dict()`` (the modeled response type)."""
        payload = {
            "blobReference": {
                "blobUri": "https://x/y",
                "credential": {"sasUri": "https://x/y?sas"},
            },
            "pendingUploadId": "id1",
        }
        response = SimpleNamespace(as_dict=lambda: payload)
        sas, blob, pid = BetaModelsOperations._extract_pending_upload_targets(response)
        assert (sas, blob, pid) == ("https://x/y?sas", "https://x/y", "id1")

    def test_missing_sas_uri_raises(self):
        payload = {
            "blobReferenceForConsumption": {"blobUri": "https://x/y", "credential": {}},
        }
        with pytest.raises(ValueError, match="SAS URI / blob URI"):
            BetaModelsOperations._extract_pending_upload_targets(payload)

    def test_missing_blob_uri_raises(self):
        payload = {
            "blobReferenceForConsumption": {"credential": {"sasUri": "https://x?sas"}},
        }
        with pytest.raises(ValueError, match="SAS URI / blob URI"):
            BetaModelsOperations._extract_pending_upload_targets(payload)

    def test_missing_pending_upload_id_is_none(self):
        payload = {
            "blobReferenceForConsumption": {
                "blobUri": "https://x/y",
                "credential": {"sasUri": "https://x/y?sas"},
            },
        }
        sas, blob, pid = BetaModelsOperations._extract_pending_upload_targets(payload)
        assert pid is None
        assert (sas, blob) == ("https://x/y?sas", "https://x/y")


# ---------------------------------------------------------------------------
# _run_azcopy
# ---------------------------------------------------------------------------


class TestRunAzcopy:
    def test_missing_azcopy_raises_runtime_error(self, tmp_path):
        src = tmp_path / "weights.bin"
        src.write_bytes(b"x")
        with mock.patch("azure.ai.projects.operations._patch_models.shutil.which", return_value=None):
            with pytest.raises(RuntimeError, match="azcopy"):
                BetaModelsOperations._run_azcopy(src, "https://x?sas")

    def test_explicit_path_overrides_shutil_which(self, tmp_path):
        src = tmp_path / "weights.bin"
        src.write_bytes(b"x")
        completed = SimpleNamespace(returncode=0, stdout="", stderr="")
        with mock.patch(
            "azure.ai.projects.operations._patch_models.subprocess.run",
            return_value=completed,
        ) as run, mock.patch("azure.ai.projects.operations._patch_models.shutil.which", return_value=None):
            BetaModelsOperations._run_azcopy(src, "https://x?sas", azcopy_path="/opt/azcopy")
        assert run.call_args.args[0][0] == "/opt/azcopy"

    def test_directory_source_uses_glob_arg(self, tmp_path):
        (tmp_path / "weights.bin").write_bytes(b"x")
        completed = SimpleNamespace(returncode=0, stdout="", stderr="")
        with mock.patch(
            "azure.ai.projects.operations._patch_models.subprocess.run",
            return_value=completed,
        ) as run, mock.patch("azure.ai.projects.operations._patch_models.shutil.which", return_value="/usr/bin/azcopy"):
            BetaModelsOperations._run_azcopy(tmp_path, "https://x?sas")
        cmd = run.call_args.args[0]
        assert cmd[0] == "/usr/bin/azcopy"
        assert cmd[1] == "copy"
        assert cmd[2] == str(tmp_path / "*")
        assert cmd[3] == "https://x?sas"
        assert "--from-to" in cmd
        assert cmd[cmd.index("--from-to") + 1] == "LocalBlob"
        assert "--recursive" in cmd

    def test_file_source_uses_file_arg(self, tmp_path):
        src = tmp_path / "weights.bin"
        src.write_bytes(b"x")
        completed = SimpleNamespace(returncode=0, stdout="", stderr="")
        with mock.patch(
            "azure.ai.projects.operations._patch_models.subprocess.run",
            return_value=completed,
        ) as run, mock.patch("azure.ai.projects.operations._patch_models.shutil.which", return_value="/usr/bin/azcopy"):
            BetaModelsOperations._run_azcopy(src, "https://x?sas")
        assert run.call_args.args[0][2] == str(src)

    def test_missing_source_raises_value_error(self, tmp_path):
        ghost = tmp_path / "does-not-exist"
        with mock.patch("azure.ai.projects.operations._patch_models.shutil.which", return_value="/usr/bin/azcopy"):
            with pytest.raises(ValueError, match="does not exist"):
                BetaModelsOperations._run_azcopy(ghost, "https://x?sas")

    def test_nonzero_exit_raises_runtime_error(self, tmp_path):
        src = tmp_path / "weights.bin"
        src.write_bytes(b"x")
        completed = SimpleNamespace(returncode=1, stdout="oops-stdout", stderr="oops-stderr")
        with mock.patch(
            "azure.ai.projects.operations._patch_models.subprocess.run",
            return_value=completed,
        ), mock.patch("azure.ai.projects.operations._patch_models.shutil.which", return_value="/usr/bin/azcopy"):
            with pytest.raises(RuntimeError, match="exited with code 1"):
                BetaModelsOperations._run_azcopy(src, "https://x?sas")


# ---------------------------------------------------------------------------
# register_model orchestration
# ---------------------------------------------------------------------------


def _make_ops() -> BetaModelsOperations:
    """Build a ``BetaModelsOperations`` without going through the client wiring."""
    return BetaModelsOperations.__new__(BetaModelsOperations)


def _pending_payload() -> dict:
    return {
        "blobReferenceForConsumption": {
            "blobUri": "https://acct.blob.core.windows.net/c/path",
            "credential": {"sasUri": "https://acct.blob.core.windows.net/c/path?sig=abc"},
        },
        "temporaryDataReferenceId": "pending-id-1",
    }


class TestRegisterModelOrchestration:
    def test_register_model_runs_three_steps_in_order_and_returns_get_result(self, tmp_path):
        (tmp_path / "weights.bin").write_bytes(b"x")
        ops = _make_ops()

        committed = SimpleNamespace(
            id="model/abc",
            name="my-model",
            version="1",
            blob_uri="https://acct.blob.core.windows.net/c/path",
        )
        calls: list[str] = []

        def fake_pending_upload(**kwargs):
            calls.append("pending_upload")
            assert kwargs["name"] == "my-model"
            assert kwargs["version"] == "1"
            return _pending_payload()

        def fake_run_azcopy(source, sas_uri, *, azcopy_path=None):  # noqa: ARG001
            calls.append("azcopy")
            assert Path(source) == tmp_path
            assert sas_uri.startswith("https://")
            assert azcopy_path == "/custom/azcopy"

        def fake_create_async(**kwargs):
            calls.append("create_async")
            assert kwargs["name"] == "my-model"
            assert kwargs["version"] == "1"
            body = kwargs["body"]
            # The blob_uri from the pending response is plumbed into the commit body.
            assert body.blob_uri == "https://acct.blob.core.windows.net/c/path"
            assert body.weight_type == "FullWeight"
            assert body.description == "desc"
            assert body.tags == {"k": "v"}

        def fake_get(**kwargs):
            calls.append("get")
            assert kwargs["name"] == "my-model"
            assert kwargs["version"] == "1"
            return committed

        with mock.patch.object(ops, "pending_upload", side_effect=fake_pending_upload), mock.patch.object(
            BetaModelsOperations, "_run_azcopy", staticmethod(fake_run_azcopy)
        ), mock.patch.object(ops, "create_async", side_effect=fake_create_async), mock.patch.object(
            ops, "get", side_effect=fake_get
        ):
            result = ops.register_model(
                name="my-model",
                version="1",
                source=tmp_path,
                weight_type="FullWeight",
                description="desc",
                tags={"k": "v"},
                azcopy_path="/custom/azcopy",
            )

        assert result is committed
        assert calls == ["pending_upload", "azcopy", "create_async", "get"]

    def test_register_model_wait_for_commit_false_returns_none_and_does_not_poll(self, tmp_path):
        (tmp_path / "weights.bin").write_bytes(b"x")
        ops = _make_ops()
        get_mock = mock.Mock()

        with mock.patch.object(ops, "pending_upload", return_value=_pending_payload()), mock.patch.object(
            BetaModelsOperations, "_run_azcopy", staticmethod(lambda *a, **kw: None)
        ), mock.patch.object(ops, "create_async", return_value=None), mock.patch.object(ops, "get", get_mock):
            result = ops.register_model(
                name="m",
                version="1",
                source=tmp_path,
                wait_for_commit=False,
            )

        assert result is None
        get_mock.assert_not_called()

    def test_register_model_polls_until_get_succeeds(self, tmp_path):
        (tmp_path / "weights.bin").write_bytes(b"x")
        ops = _make_ops()
        committed = SimpleNamespace(name="m", version="1")

        get_mock = mock.Mock(
            side_effect=[
                ResourceNotFoundError(message="not yet"),
                ResourceNotFoundError(message="still not yet"),
                committed,
            ]
        )

        with mock.patch.object(ops, "pending_upload", return_value=_pending_payload()), mock.patch.object(
            BetaModelsOperations, "_run_azcopy", staticmethod(lambda *a, **kw: None)
        ), mock.patch.object(ops, "create_async", return_value=None), mock.patch.object(
            ops, "get", get_mock
        ), mock.patch(
            "azure.ai.projects.operations._patch_models.time.sleep"
        ) as sleep:
            result = ops.register_model(
                name="m",
                version="1",
                source=tmp_path,
                polling_interval=0.01,
            )

        assert result is committed
        assert get_mock.call_count == 3
        assert sleep.call_count == 2

    def test_register_model_polling_timeout_raises_runtime_error(self, tmp_path):
        (tmp_path / "weights.bin").write_bytes(b"x")
        ops = _make_ops()

        # First a real time.monotonic call (start), then an over-the-deadline one.
        times = iter([1000.0, 1000.0, 9999.0])
        with mock.patch.object(ops, "pending_upload", return_value=_pending_payload()), mock.patch.object(
            BetaModelsOperations, "_run_azcopy", staticmethod(lambda *a, **kw: None)
        ), mock.patch.object(ops, "create_async", return_value=None), mock.patch.object(
            ops, "get", side_effect=ResourceNotFoundError(message="never")
        ), mock.patch(
            "azure.ai.projects.operations._patch_models.time.monotonic",
            side_effect=lambda: next(times),
        ), mock.patch(
            "azure.ai.projects.operations._patch_models.time.sleep"
        ):
            with pytest.raises(RuntimeError, match="did not appear within"):
                ops.register_model(
                    name="m",
                    version="1",
                    source=tmp_path,
                    polling_timeout=1.0,
                )

    def test_register_model_missing_source_raises_before_calling_service(self, tmp_path):
        ops = _make_ops()
        ghost = tmp_path / "does-not-exist"
        pending = mock.Mock()
        with mock.patch.object(ops, "pending_upload", pending):
            with pytest.raises(ValueError, match="does not exist"):
                ops.register_model(name="m", version="1", source=ghost)
        pending.assert_not_called()
