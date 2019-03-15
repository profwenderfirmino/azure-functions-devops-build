# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import subprocess
import vsts.service_endpoint.v4_1.models as models
from vsts.exceptions import VstsClientRequestError
from ..base.base_manager import BaseManager
from ..constants import SERVICE_ENDPOINT_DOMAIN

class ServiceEndpointManager(BaseManager):
    """ Manage DevOps service endpoints within projects

    Attributes:
        See BaseManager
    """

    def __init__(self, organization_name="", project_name="", creds=None):
        """Inits ServiceEndpointManager as per BaseManager"""
        super(ServiceEndpointManager, self).__init__(creds, organization_name=organization_name,
                                                     project_name=project_name)

    # Get the details of a service endpoint
    # If endpoint does not exist, return None
    def get_service_endpoints(self, repository_name):
        service_endpoint_name = self._get_service_endpoint_name(repository_name, "pipeline")
        return self._service_endpoint_client.get_service_endpoints_by_names(self._project_name, [service_endpoint_name])


    def create_github_service_endpoint(self, githubname, access_token):
        """ Create a github access token connection """
        project = self._get_project_by_name(self._project_name)

        data = {}

        auth = models.endpoint_authorization.EndpointAuthorization(
            parameters={
                "accessToken": access_token
            },
            scheme="PersonalAccessToken"
        )

        service_endpoint = models.service_endpoint.ServiceEndpoint(
            administrators_group=None,
            authorization=auth,
            data=data,
            name=githubname,
            type="github",
            url="http://github.com"
        )

        return self._service_endpoint_client.create_service_endpoint(service_endpoint, project.id)

    # This function requires user permission of Microsoft.Authorization/roleAssignments/write
    # i.e. only the owner of the subscription can use this function
    def create_service_endpoint(self, repository_name):
        """Create a new service endpoint within a project with an associated service principal"""
        project = self._get_project_by_name(self._project_name)

        command = "az account show --o json"
        token_resp = subprocess.check_output(command, shell=True).decode()
        account = json.loads(token_resp)

        data = {}
        data["subscriptionId"] = account['id']
        data["subscriptionName"] = account['name']
        data["environment"] = "AzureCloud"
        data["scopeLevel"] = "Subscription"

        # The following command requires Microsoft.Authorization/roleAssignments/write permission
        service_principle_name = self._get_service_endpoint_name(repository_name, "pipeline")
        command = "az ad sp create-for-rbac --o json --name " + service_principle_name

        token_resp = subprocess.check_output(command, shell=True).decode()
        token_resp_dict = json.loads(token_resp)
        auth = models.endpoint_authorization.EndpointAuthorization(
            parameters={
                "tenantid": token_resp_dict['tenant'],
                "serviceprincipalid": token_resp_dict['appId'],
                "authenticationType": "spnKey",
                "serviceprincipalkey": token_resp_dict['password']
            },
            scheme="ServicePrincipal"
        )

        service_endpoint = models.service_endpoint.ServiceEndpoint(
            administrators_group=None,
            authorization=auth,
            data=data,
            name=token_resp_dict['displayName'],
            type="azurerm"
        )
        return self._service_endpoint_client.create_service_endpoint(service_endpoint, project.id)

    def list_service_endpoints(self):
        """List exisiting service endpoints within a project"""
        project = self._get_project_by_name(self._project_name)
        return self._service_endpoint_client.get_service_endpoints(project.id)

    def _get_service_endpoint_name(self, repository_name, service_name):
        # A service principal name has to include the http/https to be valid
        return "http://{domain}/{org}/{proj}/{repo}/{service}".format(
            domain=SERVICE_ENDPOINT_DOMAIN,
            org=self._organization_name,
            proj=self._project_name,
            repo=repository_name,
            service=service_name
        )