import json
import os
from lintipy import COMPLETED, NEUTRAL
from pathlib import Path

import httpretty
import pytest
from botocore.vendored import requests

from suite import CheckSuite

BASE_DIR = Path(os.path.dirname(__file__))


@pytest.fixture()
def sns():
    with open(BASE_DIR / 'fixtures' / 'sns.json') as f:
        return json.load(f)


def check_suite_event():
    with open(BASE_DIR / 'fixtures' / 'checkSuiteEvent.json') as f:
        return 'check_suite', f.read()


class TestSuite:

    @pytest.fixture()
    def handler(self):
        hnd = CheckSuite()
        subject, message = check_suite_event()
        notice = sns()
        notice['Records'][0]['Sns']['Subject'] = subject
        notice['Records'][0]['Sns']['Message'] = message
        hnd.event = notice
        hnd.hook = json.loads(message)
        hnd._session = requests.Session()
        return hnd

    def test_head_branch(self, handler):
        assert handler.head_branch == 'master'

    def test_sha(self, handler):
        assert handler.sha == '0d1a26e67d8f5eaf1f6ba5c57fc3c7d91ac0fd1c'

    def test_archive_url(self, handler):
        assert handler.archive_url == (
            'https://api.github.com/repos/baxterthehacker/public-repo/'
            'tarball/0d1a26e67d8f5eaf1f6ba5c57fc3c7d91ac0fd1c'
        )

    def test_check_runs_url(self, handler):
        assert handler.check_runs_url == (
            'https://api.github.com/repos/baxterthehacker/public-repo/check-runs'
        )

    def test_load_config(self, handler):
        assert handler.load_config('tests') == ['pycodestyle', 'pyflakes']
        assert handler.load_config('does_not_exist') is None

    @httpretty.activate
    def test_create_check_run(self, handler):
        httpretty.register_uri(
            httpretty.POST, handler.check_runs_url,
            body=json.dumps({'status': 'created'}),
            status=201,
            content_type='application/json',
        )

        handler.create_check_run('pycodestyle')
        handler.create_check_run(
            'pycodestyle',
            status=COMPLETED,
            body='hello world',
            conclusion=NEUTRAL
        )

    def test_create_getting_started_guide(self, handler):
        body = handler.create_getting_started_guide({
            'example': 'https://example.com/'
        })

        assert "[click here][template]" in body
        assert "*   [example](https://example.com/)" in body

    def test_call(self, handler):
        handler.create_check_run = lambda *args, **kwargs: None
        handler(handler.event, {})
