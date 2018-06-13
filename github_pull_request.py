#!/usr/bin/env python

import os
import sys
import json
try:
    from urllib.request import Request, urlopen  # Python 3
except:
    from urllib2 import Request, urlopen  # Python 2

'''
This script queries Github for source and target branches of a pull request
and updates environment variables at TeamCity CI to make these variable
available in the builds.
Usage: python teamcity_github_pr_branch.py <pull_request_id>
Before using the script from your TeamCity installation, do the following.
1. Update the constants defined below.
2. Export environment variable TEAMCITY_GITHUB_ACCESS_TOKEN containing your personal access token to Github.
3. In TeamCity project configuration, add the following empty parameters:
    env.GITHUB_PULL_REQUEST_BASE_REF
    env.GITHUB_PULL_REQUEST_HEAD_REF
After you run the script from one of your build steps, these variables will be
resolved and you'll be able to use them as environment variables in next build steps.
'''


def create_request():
    GITHUB_API_URL = 'https://api.github.com/repos/%(owner)s/%(repo)s/pulls/%(number)s'
    github_repo_owner = os.environ.get('GITHUB_REPO_OWNER')
    if github_repo_owner is None:
        raise Exception('Repository owner is empty, ensure that GITHUB_REPO_OWNER env var is set')
    github_repo_name = os.environ.get('GITHUB_REPO_NAME')
    if github_repo_name is None:
        raise Exception('Repository owner is empty, ensure that GITHUB_REPO_NAME env var is set')

    if len(sys.argv) == 1:
        raise Exception('Pull request id is not set, you should submit it as the first command-line argument')
    pr_id = sys.argv[1]
    access_token = os.environ.get('TEAMCITY_GITHUB_ACCESS_TOKEN', '-1')
    if access_token == '-1':
        raise Exception('Access token is empty, ensure that TEAMCITY_GITHUB_ACCESS_TOKEN env var is set')
    # Extract the id from "<id>/merge" format
    pr_id = pr_id.split('/',2)[0]
    url = GITHUB_API_URL % {'owner': github_repo_owner, 'repo': github_repo_name, 'number': pr_id}

    request = Request(url)
    request.add_header('Accept', 'application/vnd.github.v3+json')
    request.add_header('Authorization', 'token %s' % access_token)
    return request


def export_refs(json_data):
    base_ref = json_data['base']['ref']
    head_ref = json_data['head']['ref']
    print('##teamcity[setParameter name=\'env.GITHUB_PULL_REQUEST_BASE_REF\' value=\'%s\']' % base_ref)
    print('##teamcity[setParameter name=\'env.GITHUB_PULL_REQUEST_HEAD_REF\' value=\'%s\']' % head_ref)


def main():
    try:
        request = create_request()
        response = urlopen(request)
        status = response.getcode()

        if status == 200:
            response_content = response.read()
            if not isinstance(response_content, str):
                response_content = response_content.decode()
            data = json.loads(response_content)
            export_refs(data)
        else:
            raise Exception('Unexpected error code %d when fetching pull request details' % status)
    except Exception as e:
        print('exception:', e)
        exit(1)


if __name__ == "__main__":
        main()
