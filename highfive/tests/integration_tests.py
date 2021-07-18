from highfive import newpr, payload
from highfive.tests import base, fakes
from highfive.tests.test_newpr import HighfiveHandlerMock
import mock
from nose.plugins.attrib import attr

@attr(type='integration')
class TestIsNewContributor(base.BaseTest):
    def setUp(self):
        super(TestIsNewContributor, self).setUp()

        self.payload = payload.Payload({'repository': {'fork': False}})
        self.handler = HighfiveHandlerMock(
            self.payload, integration_token=''
        ).handler

    def test_real_contributor_true(self):
        self.assertFalse(
            self.handler.is_new_contributor('nrc', 'rust-lang', 'rust')
        )

    def test_real_contributor_false(self):
        self.assertTrue(
            self.handler.is_new_contributor('octocat', 'rust-lang', 'rust')
        )

    def test_fake_user(self):
        self.assertTrue(
            self.handler.is_new_contributor(
                'fjkesfgojsrgljsdgla', 'rust-lang', 'rust'
            )
        )

class ApiReqMocker(object):
    def __init__(self, calls_and_returns):
        self.calls = [(c[0],) for c in calls_and_returns]
        self.patcher = mock.patch('highfive.newpr.HighfiveHandler.api_req')
        self.mock = self.patcher.start()
        self.mock.side_effect = [c[1] for c in calls_and_returns]

    def verify_calls(self):
        self.patcher.stop()

        for (expected, actual) in zip(self.calls, self.mock.call_args_list):
            assert expected == actual, 'Expected call with args %s, got %s' % (
                str(expected), str(actual)
            )

        assert self.mock.call_count == len(self.calls)

@attr(type='integration')
@attr('hermetic')
class TestNewPr(base.BaseTest):
    def setUp(self):
        super(TestNewPr, self).setUp((
            ('get_irc_nick', 'highfive.newpr.HighfiveHandler.get_irc_nick'),
            ('ConfigParser', 'highfive.newpr.ConfigParser'),
            ('load_json_file', 'highfive.newpr.HighfiveHandler._load_json_file'),
        ))

        self.mocks['get_irc_nick'].return_value = None

        config_mock = mock.Mock()
        config_mock.get.side_effect = ('integration-user', 'integration-token')
        self.mocks['ConfigParser'].RawConfigParser.return_value = config_mock

        self.mocks['load_json_file'].side_effect = (
            fakes.get_repo_configs()['individuals_no_dirs'],
            fakes.get_global_configs()['base'],
        )

    def test_new_pr_non_contributor(self):
        payload = fakes.Payload.new_pr(
            repo_owner='rust-lang', repo_name='rust', pr_author='pnkfelix'
        )
        handler = newpr.HighfiveHandler(payload)

        api_req_mock = ApiReqMocker([
            (
                (
                    'GET', 'https://the.url/', None,
                    'application/vnd.github.v3.diff'
                ),
                {'body': self._load_fake('normal.diff')},
            ),
            (
                (
                    'PATCH', newpr.issue_url % ('rust-lang', 'rust', '7'),
                    {'assignee': 'nrc'}
                ),
                {'body': {}},
            ),
            (
                (
                    'GET', newpr.commit_search_url % ('rust-lang', 'rust', 'pnkfelix'),
                    None, 'application/vnd.github.cloak-preview'
                ),
                {'body': '{"total_count": 0}'},
            ),
            (
                (
                    'POST', newpr.post_comment_url % ('rust-lang', 'rust', '7'),
                    {'body': "Thanks for the pull request, and welcome! The Rust team is excited to review your changes, and you should hear from @nrc (or someone else) soon.\n\nIf any changes to this PR are deemed necessary, please add them as extra commits. This ensures that the reviewer can see what has changed since they last reviewed the code. Due to the way GitHub handles out-of-date commits, this should also make it reasonably obvious what issues have or haven't been addressed. Large or tricky changes may require several passes of review and changes.\n\nPlease see [the contribution instructions](https://github.com/rust-lang/rust/blob/master/CONTRIBUTING.md) for more information.\n"}
                ),
                {'body': {}},
            ),
        ])
        handler.new_pr()

        api_req_mock.verify_calls()

    def test_new_pr_contributor(self):
        payload = fakes.Payload.new_pr(
            repo_owner='rust-lang', repo_name='rust', pr_author='pnkfelix'
        )
        handler = newpr.HighfiveHandler(payload)

        api_req_mock = ApiReqMocker([
            (
                (
                    'GET', 'https://the.url/', None,
                    'application/vnd.github.v3.diff'
                ),
                {'body': self._load_fake('normal.diff')},
            ),
            (
                (
                    'PATCH', newpr.issue_url % ('rust-lang', 'rust', '7'),
                    {'assignee': 'nrc'}
                ),
                {'body': {}},
            ),
            (
                (
                    'GET', newpr.commit_search_url % ('rust-lang', 'rust', 'pnkfelix'),
                    None, 'application/vnd.github.cloak-preview'
                ),
                {'body': '{"total_count": 1}'},
            ),
            (
                (
                    'POST', newpr.post_comment_url % ('rust-lang', 'rust', '7'),
                    {'body': 'r? @nrc\n\n(rust_highfive has picked a reviewer for you, use r? to override)'}
                ),
                {'body': {}},
            ),
        ])
        handler.new_pr()

        api_req_mock.verify_calls()

    def test_new_pr_contributor_with_labels(self):
        self.mocks['load_json_file'].side_effect = (
            fakes.get_repo_configs()['individuals_no_dirs_labels'],
            fakes.get_global_configs()['base'],
        )
        payload = fakes.Payload.new_pr(
            repo_owner='rust-lang', repo_name='rust', pr_author='pnkfelix'
        )
        handler = newpr.HighfiveHandler(payload)

        api_req_mock = ApiReqMocker([
            (
                (
                    'GET', 'https://the.url/', None,
                    'application/vnd.github.v3.diff'
                ),
                {'body': self._load_fake('normal.diff')},
            ),
            (
                (
                    'PATCH', newpr.issue_url % ('rust-lang', 'rust', '7'),
                    {'assignee': 'nrc'}
                ),
                {'body': {}},
            ),
            (
                (
                    'GET', newpr.commit_search_url % ('rust-lang', 'rust', 'pnkfelix'),
                    None, 'application/vnd.github.cloak-preview'
                ),
                {'body': '{"total_count": 1}'},
            ),
            (
                (
                    'POST', newpr.post_comment_url % ('rust-lang', 'rust', '7'),
                    {'body': 'r? @nrc\n\n(rust_highfive has picked a reviewer for you, use r? to override)'}
                ),
                {'body': {}},
            ),
            (
                (
                    'POST', newpr.issue_labels_url % ('rust-lang', 'rust', '7'),
                    ['a', 'b']
                ),
                {'body': {}},
            ),
        ])
        handler.new_pr()

        api_req_mock.verify_calls()

@attr(type='integration')
@attr('hermetic')
class TestNewComment(base.BaseTest):
    def setUp(self):
        super(TestNewComment, self).setUp((
            ('get_irc_nick', 'highfive.newpr.HighfiveHandler.get_irc_nick'),
            ('ConfigParser', 'highfive.newpr.ConfigParser'),
        ))

        self.mocks['get_irc_nick'].return_value = None

        config_mock = mock.Mock()
        config_mock.get.side_effect = ('integration-user', 'integration-token')
        self.mocks['ConfigParser'].RawConfigParser.return_value = config_mock

    def test_author_is_commenter(self):
        payload = fakes.Payload.new_comment()
        handler = newpr.HighfiveHandler(payload)
        api_req_mock = ApiReqMocker([
            (
                (
                    'PATCH', newpr.issue_url % ('rust-lang', 'rust', '1'),
                    {'assignee': 'davidalber'}
                ),
                {'body': {}},
            ),
        ])
        handler.new_comment()
        api_req_mock.verify_calls()

    def test_author_not_commenter_is_collaborator(self):
        payload = fakes.Payload.new_comment()
        payload._payload['issue']['user']['login'] = 'foouser'

        handler = newpr.HighfiveHandler(payload)
        api_req_mock = ApiReqMocker([
            (
                (
                    "GET",
                    newpr.user_collabo_url % (
                        'rust-lang', 'rust', 'davidalber'
                    ),
                    None
                ),
                {'body': {}},
            ),
            (
                (
                    'PATCH', newpr.issue_url % ('rust-lang', 'rust', '1'),
                    {'assignee': 'davidalber'}
                ),
                {'body': {}},
            ),
        ])
        handler.new_comment()
        api_req_mock.verify_calls()