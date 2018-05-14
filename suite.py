import logging
import os
import sys

import yaml
from lintipy import DownloadCodeMixin, GitHubEvent, QUEUED

logger = logging.getLogger('suite')

root_logger = logging.getLogger('')
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(logging.StreamHandler(sys.stdout))


class CheckSuite(DownloadCodeMixin, GitHubEvent):
    """AWS lambda handler for GitHub ``check_suite`` events."""

    COMPLETED = 'completed'
    REQUESTED = 'requested'
    REREQUESTED = 'rerequested'

    config_file_pattern = '.check_suite.yml'

    def __call__(self, event, context):
        super().__call__(event, context)
        if self.hook['action'] not in [self.REQUESTED, self.REREQUESTED]:
            logger.info('no action required')
            return
        path = self.download_code()
        config = set(self.load_config(path) or [])

        with open('check_runs.yml') as fs:
            supported_check_runs = set(yaml.safe_load(fs))

        logger.debug(config)
        logger.debug(supported_check_runs)

        for name in supported_check_runs & config:
            self.create_check_run(name)

    @property
    def head_branch(self):
        return self.hook['check_suite']['head_branch']

    @property
    def sha(self):
        return self.hook['check_suite']['head_sha']

    @property
    def archive_url(self):
        return self.hook['repository']['archive_url'].format(**{
            'archive_format': 'tarball',
            '/ref': '/%s' % self.sha,
        })

    @property
    def check_runs_url(self):
        return "https://api.github.com/repos/{full_name}/check-runs".format(
            full_name=self.hook['repository']['full_name']
        )

    def load_config(self, path):
        """Return config dictionary or ``None`` if no config was found."""
        config_path = os.path.join(path, self.config_file_pattern)
        logger.info("Reading config: %s", config_path)
        try:
            with open(config_path) as fs:
                return yaml.safe_load(fs)
        except FileNotFoundError:
            logger.error("file not found")
            return None

    def create_check_run(self, name):
        logger.info("createing check run: %s", name)
        data = {
            'name': name,
            'head_branch': self.head_branch,
            'head_sha': self.sha,
            'status': QUEUED,
        }
        response = self.session.post(self.check_runs_url, json=data)
        logger.debug(response.content.decode())
        response.raise_for_status()


def handler(event, context):
    CheckSuite()(event, context)
