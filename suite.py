import logging
import os

import yaml
from lintipy import DownloadCodeMixin, GitHubEvent, QUEUED

logger = logging.getLogger('suite')


class CheckSuite(DownloadCodeMixin, GitHubEvent):
    """AWS lambda handler for GitHub ``check_suite`` events."""

    config_file_pattern = '.check_suite.yml'

    def __call__(self, event, context):
        super().__call__(event, context)
        path = self.download_code()
        config = set(self.load_config(path) or [])

        with open('check_runs.yml') as fs:
            supported_check_runs = set(yaml.safe_load(fs))

        map(self.create_check_run, supported_check_runs & config)

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
        try:
            with open(config_path) as fs:
                return yaml.safe_load(fs)
        except FileNotFoundError:
            return None

    def create_check_run(self, name):
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
