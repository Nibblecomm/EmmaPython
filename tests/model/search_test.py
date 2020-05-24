from datetime import datetime
import unittest
from emma import exceptions as ex
from emma.model.account import Account
from emma.model.search import Search
from emma.model import SERIALIZED_DATETIME_FORMAT
from emma.model.member import Member
from tests.model import MockAdapter


class SearchTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.search = Search(
            Account(account_id="100", public_key="xxx", private_key="yyy"),
            {
                'search_id':200,
                'deleted_at':None,
                'last_run_at':datetime.now().strftime(SERIALIZED_DATETIME_FORMAT)
            }
        )

    def test_can_parse_special_fields_correctly(self):
        self.assertIsInstance(self.search['last_run_at'], datetime)
        self.assertIsNone(self.search.get('deleted_at'))

    def test_can_delete_a_search(self):
        del(self.search['search_id'])

        with self.assertRaises(ex.NoSearchIdError):
            self.search.delete()
        self.assertEqual(self.search.account.adapter.called, 0)
        self.assertFalse(self.search.is_deleted())

    def test_can_delete_a_search2(self):
        self.search['deleted_at'] = datetime.now()

        result = self.search.delete()

        self.assertIsNone(result)
        self.assertEqual(self.search.account.adapter.called, 0)
        self.assertTrue(self.search.is_deleted())

    def test_can_delete_a_search3(self):
        MockAdapter.expected = True

        result = self.search.delete()

        self.assertIsNone(result)
        self.assertEqual(self.search.account.adapter.called, 1)
        self.assertEqual(
            self.search.account.adapter.call,
            ('DELETE', '/searches/200', {}))
        self.assertTrue(self.search.is_deleted())

    def test_can_save_a_search(self):
        srch = Search(
            self.search.account,
            {'name':"Test Search", 'criteria':["group", "eq", "Test Group"]}
        )
        MockAdapter.expected = 1024

        result = srch.save()

        self.assertIsNone(result)
        self.assertEqual(srch.account.adapter.called, 1)
        self.assertEqual(
            srch.account.adapter.call,
            (
                'POST',
                '/searches',
                {
                    'name': "Test Search",
                    'criteria':["group", "eq", "Test Group"]
                }))
        self.assertEqual(1024, srch['search_id'])

    def test_can_save_a_search2(self):
        MockAdapter.expected = True

        self.search['name'] = "Test Search"
        self.search['criteria'] = ["group", "eq", "Test Group"]
        result = self.search.save()

        self.assertIsNone(result)
        self.assertEqual(self.search.account.adapter.called, 1)
        self.assertEqual(self.search.account.adapter.call,
            (
                'PUT',
                '/searches/200',
                {
                    'name': "Test Search",
                    'criteria':["group", "eq", "Test Group"]
                }))


class SearchMemberCollectionTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.members = Search(
            Account(account_id="100", public_key="xxx", private_key="yyy"),
            {'search_id': 1024}
        ).members

    def test_can_fetch_all_members(self):
        del(self.members.search['search_id'])
        with self.assertRaises(ex.NoSearchIdError):
            self.members.fetch_all()
        self.assertEqual(self.members.search.account.adapter.called, 0)

    def test_can_fetch_all_members2(self):
        # Setup
        MockAdapter.expected = [
            {'member_id': 200, 'email': "test01@example.org"},
            {'member_id': 201, 'email': "test02@example.org"},
            {'member_id': 202, 'email': "test03@example.org"}
        ]

        members = self.members.fetch_all()

        self.assertEqual(self.members.search.account.adapter.called, 1)
        self.assertEqual(
            self.members.search.account.adapter.call,
            ('GET', '/searches/1024/members', {}))
        self.assertIsInstance(members, dict)
        self.assertEqual(3, len(members))
        self.assertEqual(3, len(self.members))
        self.assertIsInstance(self.members[200], Member)
        self.assertIsInstance(self.members[201], Member)
        self.assertIsInstance(self.members[202], Member)
        self.assertEqual(self.members[200]['email'], "test01@example.org")
        self.assertEqual(self.members[201]['email'], "test02@example.org")
        self.assertEqual(self.members[202]['email'], "test03@example.org")
