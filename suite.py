import datetime
import logging
import os
import sys
import urllib.parse

import yaml
from lintipy import DownloadCodeMixin, GitHubEvent, QUEUED, COMPLETED, NEUTRAL

logger = logging.getLogger('suite')

root_logger = logging.getLogger('')
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(logging.StreamHandler(sys.stdout))


class CheckSuite(DownloadCodeMixin, GitHubEvent):
    """AWS lambda handler for GitHub ``check_suite`` events."""

    COMPLETED = 'completed'
    REQUESTED = 'requested'
    REREQUESTED = 'rerequested'

    config_file_pattern = '.checks.yml'

    def __call__(self, event, context):
        super().__call__(event, context)
        if self.hook['action'] not in [self.REQUESTED, self.REREQUESTED]:
            logger.info('no action required')
            return
        path = self.download_code()
        config = set(self.load_config(path) or [])

        with open('check_runs.yml') as fs:
            services = yaml.safe_load(fs)
        supported_check_runs = set(services.keys())

        logger.debug(config)
        logger.debug(supported_check_runs)

        for name in supported_check_runs & config:
            self.create_check_run(name)
        else:
            body = self.create_getting_started_guide(services)
            self.create_check_run('Getting Started', status=COMPLETED, body=body, conclusion=NEUTRAL)

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

    def create_getting_started_guide(self, services):
        with open('getting_started.md') as fp:
            body = fp.read()
        hyperlink_pattern = "*   [{title}]({href})"
        service_links = (
            hyperlink_pattern.format(title=title, href=url)
            for title, url in services.items()
        )
        body += "\n".join(service_links)
        body += "\n\n[template]: %s\n" % self.get_new_config_link()
        return body

    def create_check_run(self, name, status=QUEUED, body=None, conclusion=None):
        logger.info("createing check run: %s", name)
        data = {
            'name': name,
            'head_branch': self.head_branch,
            'head_sha': self.sha,
            'status': status,
        }
        if body is not None:
            data['output'] = {
                'title': name,
                'summary': body,
            }
        if conclusion:
            data['conclusion'] = conclusion
        if status == COMPLETED:
            data['completed_at'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        response = self.session.post(self.check_runs_url, json=data)
        logger.debug(response.content.decode())
        response.raise_for_status()

    def get_new_config_link(self):
        url = "https://github.com/{full_name}/new/master?".format(
            full_name=self.hook['repository']['full_name']
        )
        with open('template.yml') as f:
            template = f.read()
        kwargs = {
            'filename': self.config_file_pattern,
            'value': template
        }
        return url + urllib.parse.urlencode(kwargs)


def handler(event, context):
    CheckSuite()(event, context)
