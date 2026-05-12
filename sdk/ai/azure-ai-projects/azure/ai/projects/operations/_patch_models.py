# pylint: disable=line-too-long,useless-suppression
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
"""Customize generated code here.

Follow our quickstart for examples: https://aka.ms/azsdk/python/dpcodegen/python/customize
"""

import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Optional, Union

from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.core.tracing.decorator import distributed_trace

from ._operations import BetaModelsOperations as BetaModelsOperationsGenerated
from ..models._models import (
    ModelVersion,
    PendingUploadRequest,
    PendingUploadResult,
    PendingUploadType,
)

logger = logging.getLogger(__name__)


class BetaModelsOperations(BetaModelsOperationsGenerated):
    """
    .. warning::
        **DO NOT** instantiate this class directly.

        Instead, you should access the following operations through
        :class:`~azure.ai.projects.AIProjectClient`'s
        :attr:`beta.models <azure.ai.projects.operations.BetaOperations.models>` attribute.
    """

    @staticmethod
    def _extract_pending_upload_targets(
        response: Union[PendingUploadResult, dict],
    ) -> "tuple[str, str, Optional[str]]":
        """Return ``(sas_uri, container_blob_uri, pending_upload_id)`` from a pending-upload response.

        The service currently returns the raw datastore-style payload
        (``blobReferenceForConsumption`` / ``temporaryDataReferenceId``) for some
        Foundry deployments rather than the SDK-modeled ``PendingUploadResult``
        shape (``blobReference`` / ``pendingUploadId``). Tolerate both wire
        shapes so callers don't have to.
        """
        payload = response.as_dict() if hasattr(response, "as_dict") else dict(response)

        blob_ref = payload.get("blobReferenceForConsumption") or payload.get("blobReference") or {}
        sas_uri = (blob_ref.get("credential") or {}).get("sasUri")
        container_blob_uri = blob_ref.get("blobUri")
        pending_upload_id = payload.get("temporaryDataReferenceId") or payload.get("pendingUploadId")

        if not sas_uri or not container_blob_uri:
            raise ValueError("Could not locate SAS URI / blob URI in pending_upload response: " f"{payload!r}")
        return sas_uri, container_blob_uri, pending_upload_id

    @staticmethod
    def _run_azcopy(source: Path, sas_uri: str, *, azcopy_path: Optional[str] = None) -> None:
        """Shell out to ``azcopy copy`` to upload ``source`` to the SAS container."""
        azcopy = azcopy_path or shutil.which("azcopy")
        if not azcopy:
            raise RuntimeError(
                "`azcopy` was not found on PATH. Install AzCopy "
                "(https://aka.ms/downloadazcopy) and ensure it is on PATH, or "
                "pass `azcopy_path=` explicitly."
            )

        if source.is_dir():
            src_arg = str(source / "*")
        elif source.is_file():
            src_arg = str(source)
        else:
            raise ValueError(f"Upload source does not exist: {source}")

        cmd = [
            azcopy,
            "copy",
            src_arg,
            sas_uri,
            "--from-to",
            "LocalBlob",
            "--recursive",
        ]

        # Don't log the SAS query string — it's a credential.
        redacted = cmd.copy()
        redacted[3] = sas_uri.split("?", 1)[0] + "?<sas-redacted>"
        logger.info("[register_model] running: %s", " ".join(redacted))

        completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if completed.stdout:
            logger.debug("[register_model] azcopy stdout:\n%s", completed.stdout)
        if completed.stderr:
            logger.debug("[register_model] azcopy stderr:\n%s", completed.stderr)
        if completed.returncode != 0:
            raise RuntimeError(
                f"azcopy exited with code {completed.returncode}.\n"
                f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
            )

    @distributed_trace
    def register_model(
        self,
        *,
        name: str,
        version: str,
        source: Union[str, "os.PathLike[str]"],
        weight_type: Optional[str] = None,
        base_model: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional["dict[str, str]"] = None,
        azcopy_path: Optional[str] = None,
        wait_for_commit: bool = True,
        polling_timeout: float = 300.0,
        polling_interval: float = 2.0,
        **kwargs: Any,
    ) -> Optional[ModelVersion]:
        """Register a local model by running the full upload-first sequence.

        This wraps the three mandatory steps of the model-registration spec
        into a single call:

        1. :meth:`pending_upload` — provision a project-managed blob container
           and obtain a SAS URI.
        2. ``azcopy copy`` — upload the local weight files directly to the
           SAS container.
        3. :meth:`create_async` — finalize registration with the
           ``ModelVersion`` body (``blob_uri``, ``weight_type``, ``base_model``,
           ``description``, ``tags``).

        :keyword name: Name of the model to register. Required.
        :paramtype name: str
        :keyword version: Version identifier for the model. Required.
        :paramtype version: str
        :keyword source: Local file or directory containing the model weights.
            If a directory, its contents are uploaded recursively to the SAS
            container root. Required.
        :paramtype source: str or os.PathLike[str]
        :keyword weight_type: Optional weight type (e.g. ``"FullWeight"``,
            ``"LoRA"``, ``"DraftModel"``).
        :paramtype weight_type: str
        :keyword base_model: Optional base model asset ID.
        :paramtype base_model: str
        :keyword description: Optional asset description.
        :paramtype description: str
        :keyword tags: Optional asset tags.
        :paramtype tags: dict[str, str]
        :keyword azcopy_path: Optional explicit path to the azcopy executable.
            Defaults to ``shutil.which("azcopy")``.
        :paramtype azcopy_path: str
        :keyword wait_for_commit: When True (default) poll :meth:`get` until
            the committed ``ModelVersion`` is observable, and return it.
            When False, return ``None`` after the async commit is accepted.
        :paramtype wait_for_commit: bool
        :keyword polling_timeout: Total seconds to poll for commit completion.
        :paramtype polling_timeout: float
        :keyword polling_interval: Seconds between poll attempts.
        :paramtype polling_interval: float
        :return: The committed :class:`~azure.ai.projects.models.ModelVersion`
            when ``wait_for_commit`` is True, otherwise ``None``.
        :rtype: ~azure.ai.projects.models.ModelVersion or None
        :raises ValueError: If ``source`` does not exist or the pending-upload
            response is missing the SAS / blob URI.
        :raises RuntimeError: If ``azcopy`` is not on PATH or exits with a
            non-zero status, or the registration does not commit before
            ``polling_timeout`` elapses.
        """
        source_path = Path(os.fspath(source))
        if not source_path.exists():
            raise ValueError(f"Upload source does not exist: {source_path}")

        # --- Step 1: StartPendingUpload --------------------------------------
        logger.info(
            "[register_model] step 1/3 pending_upload(name=%r, version=%r)",
            name,
            version,
        )
        pending = self.pending_upload(
            name=name,
            version=version,
            body=PendingUploadRequest(
                pending_upload_type=PendingUploadType.TEMPORARY_BLOB_REFERENCE,
            ),
            **kwargs,
        )
        sas_uri, container_blob_uri, pending_upload_id = self._extract_pending_upload_targets(pending)
        logger.info(
            "[register_model] pending_upload_id=%s blob_uri=%s",
            pending_upload_id,
            container_blob_uri,
        )

        # --- Step 2: Upload via azcopy ---------------------------------------
        logger.info("[register_model] step 2/3 azcopy upload from %s", source_path)
        self._run_azcopy(source_path, sas_uri, azcopy_path=azcopy_path)

        # --- Step 3: Commit registration -------------------------------------
        body = ModelVersion(
            blob_uri=container_blob_uri,
            weight_type=weight_type,
            base_model=base_model,
            description=description,
            tags=tags or {},
        )
        logger.info(
            "[register_model] step 3/3 create_async(name=%r, version=%r)",
            name,
            version,
        )
        self.create_async(name=name, version=version, body=body, **kwargs)

        if not wait_for_commit:
            return None

        # The async op returns 202; the service materializes the ModelVersion
        # asynchronously. Poll get() until it appears or we time out.
        deadline = time.monotonic() + polling_timeout
        last_exc: Optional[BaseException] = None
        while True:
            try:
                return self.get(name=name, version=version, **kwargs)
            except ResourceNotFoundError as ex:
                last_exc = ex
                if time.monotonic() >= deadline:
                    raise RuntimeError(
                        f"Model {name!r}@{version!r} did not appear within " f"{polling_timeout}s after create_async."
                    ) from last_exc
                time.sleep(polling_interval)


__all__ = ["BetaModelsOperations"]
