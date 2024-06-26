# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
import os
from typing import Any, Optional
from .client_assertion import ClientAssertionCredential
from ..._credentials.workload_identity import TokenFileMixin
from ..._constants import EnvironmentVariables


class WorkloadIdentityCredential(ClientAssertionCredential, TokenFileMixin):
    """Authenticates using Microsoft Entra Workload ID.

    Workload identity authentication is a feature in Azure that allows applications running on virtual machines (VMs)
    to access other Azure resources without the need for a service principal or managed identity. With workload
    identity authentication, applications authenticate themselves using their own identity, rather than using a shared
    service principal or managed identity. Under the hood, workload identity authentication uses the concept of Service
    Account Credentials (SACs), which are automatically created by Azure and stored securely in the VM. By using
    workload identity authentication, you can avoid the need to manage and rotate service principals or managed
    identities for each application on each VM. Additionally, because SACs are created automatically and managed by
    Azure, you don't need to worry about storing and securing sensitive credentials themselves.

    The WorkloadIdentityCredential supports Azure workload identity authentication on Azure Kubernetes and acquires
    a token using the service account credentials available in the Azure Kubernetes environment. Refer
    to `this workload identity overview <https://learn.microsoft.com/azure/aks/workload-identity-overview>`__
    for more information.

    :keyword str tenant_id: ID of the application's Microsoft Entra tenant. Also called its "directory" ID.
    :keyword str client_id: The client ID of a Microsoft Entra app registration.
    :keyword str token_file_path: The path to a file containing a Kubernetes service account token that authenticates
        the identity.

    .. admonition:: Example:

        .. literalinclude:: ../samples/credential_creation_code_snippets.py
            :start-after: [START workload_identity_credential_async]
            :end-before: [END workload_identity_credential_async]
            :language: python
            :dedent: 4
            :caption: Create a WorkloadIdentityCredential.
    """

    def __init__(
        self,
        *,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        token_file_path: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        tenant_id = tenant_id or os.environ.get(EnvironmentVariables.AZURE_TENANT_ID)
        client_id = client_id or os.environ.get(EnvironmentVariables.AZURE_CLIENT_ID)
        token_file_path = token_file_path or os.environ.get(EnvironmentVariables.AZURE_FEDERATED_TOKEN_FILE)
        if not tenant_id:
            raise ValueError(
                "'tenant_id' is required. Please pass it in or set the "
                f"{EnvironmentVariables.AZURE_TENANT_ID} environment variable"
            )
        if not client_id:
            raise ValueError(
                "'client_id' is required. Please pass it in or set the "
                f"{EnvironmentVariables.AZURE_CLIENT_ID} environment variable"
            )
        if not token_file_path:
            raise ValueError(
                "'token_file_path' is required. Please pass it in or set the "
                f"{EnvironmentVariables.AZURE_FEDERATED_TOKEN_FILE} environment variable"
            )
        self._token_file_path = token_file_path
        super().__init__(
            tenant_id=tenant_id,
            client_id=client_id,
            func=self._get_service_account_token,
            token_file_path=token_file_path,
            **kwargs,
        )
