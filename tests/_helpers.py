# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This file contains the some helpers needed for the tests"""

from azure.cli.core import get_default_cli
from azure.cli.core._profile import Profile

def get_credentials():
    cli_ctx = get_default_cli()
    profile = Profile(cli_ctx=cli_ctx)
    creds, _, _ = profile.get_login_credentials(subscription_id=None)
    return creds
