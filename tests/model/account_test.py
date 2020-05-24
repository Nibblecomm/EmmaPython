import unittest
from emma.adapter.requests_adapter import RequestsAdapter
from emma import exceptions as ex
from emma.enumerations import GroupType, MemberStatus, MailingStatus, MailingType
from emma.model.account import (Account, AccountFieldCollection,
                                  AccountImportCollection,
                                  AccountGroupCollection,
                                  AccountMemberCollection,
                                  AccountMailingCollection,
                                  AccountSearchCollection,
                                  AccountTriggerCollection,
                                  AccountWebHookCollection)
from emma.model.field import Field
from emma.model.group import Group
from emma.model.mailing import Mailing
from emma.model.member_import import MemberImport
from emma.model.member import Member
from emma.model.search import Search
from emma.model.trigger import Trigger
from emma.model.webhook import WebHook
from emma.model.automation import Workflow
from tests.model import MockAdapter


class AccountDefaultAdapterTest(unittest.TestCase):
    def test_default_adapter_is_api_v1_adapter(self):
        self.assertIs(Account.default_adapter, RequestsAdapter)


class AccountTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.account = Account(
            account_id="100",
            public_key="xxx",
            private_key="yyy")

    def test_field_collection_can_be_accessed(self):
        self.assertIsInstance(self.account.fields, AccountFieldCollection)

    def test_import_collection_can_be_accessed(self):
        self.assertIsInstance(self.account.imports, AccountImportCollection)

    def test_member_collection_can_be_accessed(self):
        self.assertIsInstance(self.account.members, AccountMemberCollection)


class AccountFieldCollectionTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.fields = Account(
            account_id="100",
            public_key="xxx",
            private_key="yyy").fields

    def test_factory_produces_a_new_field(self):
        self.assertIsInstance(self.fields.factory(), Field)
        self.assertEqual(self.fields.account.adapter.called, 0)

    def test_fetch_all_returns_a_dictionary(self):
        MockAdapter.expected = [{'field_id': 201}]
        self.assertIsInstance(self.fields.fetch_all(), dict)
        self.assertEqual(self.fields.account.adapter.called, 1)
        self.assertEqual(
            self.fields.account.adapter.call,
            ('GET', '/fields', {}))

    def test_fetch_all_returns_a_dictionary2(self):
        # Setup
        MockAdapter.expected = [{'field_id': 201},{'field_id': 204}]

        self.assertIsInstance(self.fields.fetch_all(deleted=True), dict)
        self.assertEqual(self.fields.account.adapter.called, 1)
        self.assertEqual(
            self.fields.account.adapter.call,
            ('GET', '/fields', {"deleted":True}))

    def test_fetch_all_populates_collection(self):
        MockAdapter.expected = [{'field_id': 201}]
        self.assertEqual(0, len(self.fields))
        self.fields.fetch_all()
        self.assertEqual(1, len(self.fields))

    def test_fetch_all_caches_results(self):
        MockAdapter.expected = [{'field_id': 201}]
        self.fields.fetch_all()
        self.fields.fetch_all()
        self.assertEqual(self.fields.account.adapter.called, 1)

    def test_field_collection_object_can_be_accessed_like_a_dictionary(self):
        MockAdapter.expected = [{'field_id': 201}]
        self.fields.fetch_all()
        self.assertIsInstance(self.fields, AccountFieldCollection)
        self.assertEqual(1, len(self.fields))
        self.assertIsInstance(self.fields[201], Field)

    def test_fetch_one_by_field_id_returns_a_field_object(self):
        # Setup
        MockAdapter.expected = {'field_id': 201}

        member = self.fields.find_one_by_field_id(201)

        self.assertIsInstance(member, Field)
        self.assertEqual(member['field_id'], 201)
        self.assertEqual(self.fields.account.adapter.called, 1)
        self.assertEqual(
            self.fields.account.adapter.call,
            ('GET', '/fields/201', {}))

    def test_fetch_one_by_field_id_returns_a_field_object2(self):
        # Setup
        MockAdapter.expected = {'field_id': 204}

        member = self.fields.find_one_by_field_id(204, deleted=True)

        self.assertIsInstance(member, Field)
        self.assertEqual(member['field_id'], 204)
        self.assertEqual(self.fields.account.adapter.called, 1)
        self.assertEqual(
            self.fields.account.adapter.call,
            ('GET', '/fields/204', {"deleted":True}))

    def test_fetch_one_by_field_id_populates_collection(self):
        # Setup
        MockAdapter.expected = {'field_id': 201}

        self.fields.find_one_by_field_id(201)

        self.assertIn(201, self.fields)
        self.assertIsInstance(self.fields[201], Field)
        self.assertEqual(self.fields[201]['field_id'], 201)

    def test_fetch_one_by_field_id_caches_result(self):
        # Setup
        MockAdapter.expected = {'field_id': 201}

        self.fields.find_one_by_field_id(201)
        self.fields.find_one_by_field_id(201)

        self.assertEqual(self.fields.account.adapter.called, 1)

    def test_dictionary_access_lazy_loads_by_field_id(self):
        # Setup
        MockAdapter.expected = {'field_id': 201}

        member = self.fields[201]

        self.assertIn(201, self.fields)
        self.assertIsInstance(member, Field)
        self.assertEqual(self.fields[201]['field_id'], 201)
        self.assertEqual(self.fields.account.adapter.called, 1)
        self.assertEqual(
            self.fields.account.adapter.call,
            ('GET', '/fields/201', {'deleted': True}))

    def test_dictionary_access_lazy_loads_by_field_id2(self):
        # Setup
        MockAdapter.expected = None

        field = self.fields.get(204)

        self.assertEqual(0, len(self.fields))
        self.assertIsNone(field)
        self.assertEqual(self.fields.account.adapter.called, 1)
        self.assertEqual(
            self.fields.account.adapter.call,
            ('GET', '/fields/204', {'deleted': True}))

    def test_field_collection_can_export_list_of_valid_shortcut_names(self):
        MockAdapter.expected = [
            {'field_id': 200, 'shortcut_name': "first_name"},
            {'field_id': 201, 'shortcut_name': "last_name"},
            {'field_id': 202, 'shortcut_name': "work_phone"}]
        shortcuts = self.fields.export_shortcuts()
        self.assertIsInstance(shortcuts, list)
        self.assertEqual(3, len(shortcuts))
        self.assertListEqual(
            shortcuts,
            ["first_name", "last_name", "work_phone"]
        )

    def test_can_delete_a_single_group_with_del(self):
        # Setup
        MockAdapter.expected = True
        self.fields._dict = {
            203: Field(self.fields.account, {'field_id':203}),
            204: Field(self.fields.account, {'field_id':204})
        }

        del(self.fields[203])

        self.assertEqual(self.fields.account.adapter.called, 1)
        self.assertEqual(
            self.fields.account.adapter.call,
            ('DELETE', '/fields/203', {}))
        self.assertEqual(1, len(self.fields))
        self.assertIn(204, self.fields)


class AccountGroupCollectionTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.groups = Account(
            account_id="100",
            public_key="xxx",
            private_key="yyy").groups

    def test_fetch_all_returns_a_dictionary(self):
        MockAdapter.expected = [{'member_group_id': 201}]
        self.assertIsInstance(self.groups.fetch_all(), dict)
        self.assertEqual(self.groups.account.adapter.called, 1)
        self.assertEqual(
            self.groups.account.adapter.call,
            ('GET', '/groups', {}))

    def test_fetch_all_returns_a_dictionary2(self):
        MockAdapter.expected = [{'member_group_id': 201}]
        self.assertIsInstance(
            self.groups.fetch_all([
                GroupType.RegularGroup,
                GroupType.HiddenGroup]),
            dict)
        self.assertEqual(self.groups.account.adapter.called, 1)
        self.assertEqual(
            self.groups.account.adapter.call,
            ('GET', '/groups', {'group_types': ["g", "h"]}))

    def test_fetch_all_populates_collection(self):
        MockAdapter.expected = [{'member_group_id': 201}]
        self.assertEqual(0, len(self.groups))
        self.groups.fetch_all()
        self.assertEqual(1, len(self.groups))

    def test_fetch_all_caches_results(self):
        MockAdapter.expected = [{'member_group_id': 201}]
        self.groups.fetch_all()
        self.groups.fetch_all()
        self.assertEqual(self.groups.account.adapter.called, 1)

    def test_group_collection_object_can_be_accessed_like_a_dictionary(self):
        MockAdapter.expected = [{'member_group_id': 201}]
        self.groups.fetch_all()
        self.assertIsInstance(self.groups, AccountGroupCollection)
        self.assertEqual(1, len(self.groups))
        self.assertIsInstance(self.groups[201], Group)

    def test_fetch_one_by_group_id_populates_collection(self):
        MockAdapter.expected = {'member_group_id': 201}
        self.groups.find_one_by_group_id(201)
        self.assertIn(201, self.groups)
        self.assertIsInstance(self.groups[201], Group)
        self.assertEqual(self.groups[201]['member_group_id'], 201)

    def test_fetch_one_by_import_id_caches_result(self):
        MockAdapter.expected = {'member_group_id': 201}
        self.groups.find_one_by_group_id(201)
        self.groups.find_one_by_group_id(201)
        self.assertEqual(self.groups.account.adapter.called, 1)

    def test_dictionary_access_lazy_loads_by_import_id(self):
        MockAdapter.expected = {'member_group_id': 201}
        group = self.groups[201]
        self.assertIn(201, self.groups)
        self.assertIsInstance(group, Group)
        self.assertEqual(self.groups[201]['member_group_id'], 201)
        self.assertEqual(self.groups.account.adapter.called, 1)
        self.assertEqual(
            self.groups.account.adapter.call,
            ('GET', '/groups/201', {}))

    def test_dictionary_access_lazy_loads_by_import_id2(self):
        MockAdapter.expected = None
        group = self.groups.get(204)
        self.assertEqual(0, len(self.groups))
        self.assertIsNone(group)
        self.assertEqual(self.groups.account.adapter.called, 1)
        self.assertEqual(
            self.groups.account.adapter.call,
            ('GET', '/groups/204', {}))

    def test_can_delete_a_single_group_with_del(self):
        # Setup
        MockAdapter.expected = True
        self.groups._dict = {
            203: Group(self.groups.account, {'member_group_id':203}),
            204: Group(self.groups.account, {'member_group_id':204})
        }

        del(self.groups[203])

        self.assertEqual(self.groups.account.adapter.called, 1)
        self.assertEqual(
            self.groups.account.adapter.call,
            ('DELETE', '/groups/203', {}))
        self.assertEqual(1, len(self.groups))
        self.assertIn(204, self.groups)

    def test_can_add_groups_in_bulk(self):
        result = self.groups.save()
        self.assertIsNone(result)
        self.assertEqual(self.groups.account.adapter.called, 0)

    def test_can_add_groups_in_bulk2(self):
        with self.assertRaises(ex.NoGroupNameError):
            self.groups.save([
                self.groups.factory(),
                self.groups.factory()
            ])

        self.assertEqual(self.groups.account.adapter.called, 0)

    def test_can_add_groups_in_bulk3(self):
        # Setup
        MockAdapter.expected = [
            {'member_group_id': 2010, 'group_name': "Test Group 0"},
            {'member_group_id': 2011, 'group_name': "Test Group 1"}]

        # Perform add
        result = self.groups.save([
            self.groups.factory({'group_name': "Test Group 0"}),
            self.groups.factory({'group_name': "Test Group 1"})
        ])

        self.assertIsNone(result)
        self.assertEqual(self.groups.account.adapter.called, 1)
        self.assertEqual(self.groups.account.adapter.call, (
            'POST',
            '/groups',
            {'groups': [
                {'group_name': "Test Group 0"},
                {'group_name': "Test Group 1"}
            ]}
        ))


class AccountImportCollectionTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.imports = Account(
            account_id="100",
            public_key="xxx",
            private_key="yyy").imports

    def test_fetch_all_returns_a_dictionary(self):
        MockAdapter.expected = [{'import_id': 201}]
        self.assertIsInstance(self.imports.fetch_all(), dict)
        self.assertEqual(self.imports.account.adapter.called, 1)
        self.assertEqual(
            self.imports.account.adapter.call,
            ('GET', '/members/imports', {}))

    def test_fetch_all_populates_collection(self):
        MockAdapter.expected = [{'import_id': 201}]
        self.assertEqual(0, len(self.imports))
        self.imports.fetch_all()
        self.assertEqual(1, len(self.imports))

    def test_fetch_all_caches_results(self):
        MockAdapter.expected = [{'import_id': 201}]
        self.imports.fetch_all()
        self.imports.fetch_all()
        self.assertEqual(self.imports.account.adapter.called, 1)

    def test_imports_collection_object_can_be_accessed_like_a_dictionary(self):
        MockAdapter.expected = [{'import_id': 201}]
        self.imports.fetch_all()
        self.assertIsInstance(self.imports, AccountImportCollection)
        self.assertEqual(1, len(self.imports))
        self.assertIsInstance(self.imports[201], MemberImport)

    def test_fetch_one_by_import_id_returns_an_import_object(self):
        MockAdapter.expected = {'import_id': 201}
        emma_import = self.imports.find_one_by_import_id(201)
        self.assertIsInstance(emma_import, MemberImport)
        self.assertEqual(emma_import['import_id'], 201)
        self.assertEqual(self.imports.account.adapter.called, 1)
        self.assertEqual(
            self.imports.account.adapter.call,
            ('GET', '/members/imports/201', {}))

    def test_fetch_one_by_import_id_populates_collection(self):
        MockAdapter.expected = {'import_id': 201}
        self.imports.find_one_by_import_id(201)
        self.assertIn(201, self.imports)
        self.assertIsInstance(self.imports[201], MemberImport)
        self.assertEqual(self.imports[201]['import_id'], 201)

    def test_fetch_one_by_import_id_caches_result(self):
        MockAdapter.expected = {'import_id': 201}
        self.imports.find_one_by_import_id(201)
        self.imports.find_one_by_import_id(201)
        self.assertEqual(self.imports.account.adapter.called, 1)

    def test_dictionary_access_lazy_loads_by_import_id(self):
        MockAdapter.expected = {'import_id': 201}
        emma_import = self.imports[201]
        self.assertIn(201, self.imports)
        self.assertIsInstance(emma_import, MemberImport)
        self.assertEqual(self.imports[201]['import_id'], 201)
        self.assertEqual(self.imports.account.adapter.called, 1)
        self.assertEqual(
            self.imports.account.adapter.call,
            ('GET', '/members/imports/201', {}))

    def test_dictionary_access_lazy_loads_by_import_id2(self):
        MockAdapter.expected = None
        emma_import = self.imports.get(204)
        self.assertEqual(0, len(self.imports))
        self.assertIsNone(emma_import)
        self.assertEqual(self.imports.account.adapter.called, 1)
        self.assertEqual(
            self.imports.account.adapter.call,
            ('GET', '/members/imports/204', {}))

    def test_can_delete_a_single_import_with_del(self):
        # Setup
        MockAdapter.expected = True
        self.imports._dict = {
            203: MemberImport(self.imports.account),
            204: MemberImport(self.imports.account)
        }

        del(self.imports[203])

        self.assertEqual(self.imports.account.adapter.called, 1)
        self.assertEqual(
            self.imports.account.adapter.call,
            ('DELETE', '/members/imports/delete', {'import_ids': [203]}))
        self.assertEqual(1, len(self.imports))
        self.assertIn(204, self.imports)

    def test_can_mark_imports_as_deleted(self):
        # Setup
        MockAdapter.expected = True
        self.imports._dict = {
            203: MemberImport(self.imports.account),
            204: MemberImport(self.imports.account),
            205: MemberImport(self.imports.account)
        }

        result = self.imports.delete([204, 205])
        self.assertIsNone(result)
        self.assertEqual(self.imports.account.adapter.called, 1)
        self.assertEqual(
            self.imports.account.adapter.call,
            ('DELETE', '/members/imports/delete', {'import_ids': [204, 205]}))
        self.assertEqual(1, len(self.imports))
        self.assertIn(203, self.imports)

    def test_can_mark_imports_as_deleted(self):
        result = self.imports.delete()
        self.assertIsNone(result)
        self.assertEqual(self.imports.account.adapter.called, 0)

    def test_can_mark_imports_as_deleted2(self):
        # Setup
        MockAdapter.expected = False
        self.imports._dict = {
            203: MemberImport(self.imports.account),
            204: MemberImport(self.imports.account),
            205: MemberImport(self.imports.account)
        }

        with self.assertRaises(ex.ImportDeleteError):
            self.imports.delete([204, 205])

        self.assertEqual(self.imports.account.adapter.called, 1)
        self.assertEqual(
            self.imports.account.adapter.call,
            ('DELETE', '/members/imports/delete', {'import_ids': [204, 205]}))
        self.assertEqual(3, len(self.imports))

    def test_can_mark_imports_as_deleted3(self):
        # Setup
        MockAdapter.expected = True
        self.imports._dict = {
            203: MemberImport(self.imports.account),
            204: MemberImport(self.imports.account),
            205: MemberImport(self.imports.account)
        }

        result = self.imports.delete([204, 205])
        self.assertIsNone(result)
        self.assertEqual(self.imports.account.adapter.called, 1)
        self.assertEqual(
            self.imports.account.adapter.call,
            ('DELETE', '/members/imports/delete', {'import_ids': [204, 205]}))
        self.assertEqual(1, len(self.imports))
        self.assertIn(203, self.imports)


class AccountMemberCollectionTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.members = Account(
            account_id="100",
            public_key="xxx",
            private_key="yyy").members

    def test_fetch_all_returns_a_dictionary(self):
        # Setup
        MockAdapter.expected = [{'member_id': 201}]

        self.assertIsInstance(self.members.fetch_all(), dict)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(
            self.members.account.adapter.call,
            ('GET', '/members', {}))

    def test_fetch_all_returns_a_dictionary2(self):
        # Setup
        MockAdapter.expected = [{'member_id': 201},{'member_id': 204}]

        self.assertIsInstance(self.members.fetch_all(deleted=True), dict)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(
            self.members.account.adapter.call,
            ('GET', '/members', {"deleted":True}))

    def test_fetch_all_populates_collection(self):
        # Setup
        MockAdapter.expected = [{'member_id': 201}]
        self.assertEqual(0, len(self.members))

        self.members.fetch_all()

        self.assertEqual(1, len(self.members))

    def test_fetch_all_caches_results(self):
        # Setup
        MockAdapter.expected = [{'member_id': 201}]

        self.members.fetch_all()
        self.members.fetch_all()

        self.assertEqual(self.members.account.adapter.called, 1)

    def test_members_collection_object_can_be_accessed_like_a_dictionary(self):
        # Setup
        MockAdapter.expected = [{'member_id': 201}]

        self.members.fetch_all()

        self.assertIsInstance(self.members, AccountMemberCollection)
        self.assertEqual(1, len(self.members))
        self.assertIsInstance(self.members[201], Member)

    def test_fetch_all_by_import_id_returns_a_dictionary(self):
        # Setup
        MockAdapter.expected = [{'member_id': 201}]

        self.assertIsInstance(self.members.fetch_all_by_import_id(100), dict)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(
            self.members.account.adapter.call,
            ('GET', '/members/imports/100/members', {}))

    def test_fetch_all_by_import_id_updates_collection(self):
        # Setup
        MockAdapter.expected = [{'member_id': 201}]
        self.assertEqual(0, len(self.members))

        self.members.fetch_all_by_import_id(100)

        self.assertEqual(1, len(self.members))

    def test_fetch_all_by_import_id_updates_collection2(self):
        # Setup
        self.members._dict = {
            200: {'member_id': 200, 'email': "test1@example.com"},
            201: {'member_id': 201, 'email': "test2@example.com"}
        }
        MockAdapter.expected = [
            {'member_id': 201, 'email': "test3@example.com"}
        ]
        self.assertEqual(2, len(self.members))

        self.members.fetch_all_by_import_id(100)

        self.assertEqual(2, len(self.members))
        self.assertDictEqual(
            self.members._dict,
            {
                200: {'member_id': 200, 'email': "test1@example.com"},
                201: {'member_id': 201, 'email': "test3@example.com"}
            }
        )

    def test_fetch_all_by_import_id_updates_collection3(self):
        # Setup
        self.members._dict = {
            200: {'member_id': 200, 'email': "test1@example.com"},
            201: {'member_id': 201, 'email': "test2@example.com"}
        }
        MockAdapter.expected = [
            {'member_id': 201, 'email': "test3@example.com"},
            {'member_id': 202, 'email': "test4@example.com"}
        ]
        self.assertEqual(2, len(self.members))

        self.members.fetch_all_by_import_id(100)

        self.assertEqual(3, len(self.members))
        self.assertDictEqual(
            self.members._dict,
            {
                200: {'member_id': 200, 'email': "test1@example.com"},
                201: {'member_id': 201, 'email': "test3@example.com"},
                202: {'member_id': 202, 'email': "test4@example.com"}
            }
        )

    def test_fetch_all_by_import_id_updates_collection4(self):
        # Setup
        self.members._dict = {
            201: {'member_id': 201, 'email': "test2@example.com"}
        }
        MockAdapter.expected = [
            {'member_id': 201, 'email': "test3@example.com"}
        ]
        self.assertEqual(1, len(self.members))

        self.members.fetch_all_by_import_id(100)

        self.assertEqual(1, len(self.members))
        self.assertDictEqual(
            self.members._dict,
            {
                201: {'member_id': 201, 'email': "test3@example.com"}
            }
        )

    def test_fetch_all_by_import_id_does_not_cache_results(self):
        # Setup
        MockAdapter.expected = [{'member_id': 201}]

        self.members.fetch_all_by_import_id(100)
        self.members.fetch_all_by_import_id(100)

        self.assertEqual(self.members.account.adapter.called, 2)

    def test_fetch_one_by_member_id_returns_a_member_object(self):
        # Setup
        MockAdapter.expected = {'member_id': 201}

        member = self.members.find_one_by_member_id(201)

        self.assertIsInstance(member, Member)
        self.assertEqual(member['member_id'], 201)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(
            self.members.account.adapter.call,
            ('GET', '/members/201', {}))

    def test_fetch_one_by_member_id_returns_a_member_object2(self):
        # Setup
        MockAdapter.expected = {'member_id': 204}

        member = self.members.find_one_by_member_id(204, deleted=True)

        self.assertIsInstance(member, Member)
        self.assertEqual(member['member_id'], 204)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(
            self.members.account.adapter.call,
            ('GET', '/members/204', {"deleted":True}))

    def test_fetch_one_by_member_id_populates_collection(self):
        # Setup
        MockAdapter.expected = {'member_id': 201}

        self.members.find_one_by_member_id(201)

        self.assertIn(201, self.members)
        self.assertIsInstance(self.members[201], Member)
        self.assertEqual(self.members[201]['member_id'], 201)

    def test_fetch_one_by_member_id_caches_result(self):
        # Setup
        MockAdapter.expected = {'member_id': 201}

        self.members.find_one_by_member_id(201)
        self.members.find_one_by_member_id(201)

        self.assertEqual(self.members.account.adapter.called, 1)

    def test_dictionary_access_lazy_loads_by_member_id(self):
        # Setup
        MockAdapter.expected = {'member_id': 201}

        member = self.members[201]

        self.assertIn(201, self.members)
        self.assertIsInstance(member, Member)
        self.assertEqual(self.members[201]['member_id'], 201)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(
            self.members.account.adapter.call,
            ('GET', '/members/201', {}))

    def test_dictionary_access_lazy_loads_by_member_id2(self):
        # Setup
        MockAdapter.expected = None

        member = self.members.get(204)

        self.assertEqual(0, len(self.members))
        self.assertIsNone(member)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(
            self.members.account.adapter.call,
            ('GET', '/members/204', {}))

    def test_fetch_one_by_email_returns_a_member_object(self):
        # Setup
        MockAdapter.expected = {'member_id': 201, 'email': "test@example.com"}

        member = self.members.find_one_by_email("test@example.com")

        self.assertIsInstance(member, Member)
        self.assertEqual(member['member_id'], 201)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(
            self.members.account.adapter.call,
            ('GET', '/members/email/test@example.com', {}))

    def test_fetch_one_by_email_returns_a_member_object2(self):
        # Setup
        MockAdapter.expected = {'member_id': 204, 'email': "test@example.com"}

        member = self.members.find_one_by_email("test@example.com", deleted=True)

        self.assertIsInstance(member, Member)
        self.assertEqual(member['member_id'], 204)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(
            self.members.account.adapter.call,
            ('GET', '/members/email/test@example.com', {"deleted":True}))

    def test_fetch_one_by_email_populates_collection(self):
        # Setup
        MockAdapter.expected = {'member_id': 201, 'email': "test@example.com"}

        self.members.find_one_by_email("test@example.com")

        self.assertIn(201, self.members)
        self.assertIsInstance(self.members[201], Member)
        self.assertEqual(self.members[201]['member_id'], 201)

    def test_fetch_one_by_email_caches_result(self):
        # Setup
        MockAdapter.expected = {'member_id': 201, 'email': "test@example.com"}

        self.members.find_one_by_email("test@example.com")
        self.members.find_one_by_email("test@example.com")

        self.assertEqual(self.members.account.adapter.called, 1)

    def test_dictionary_access_lazy_loads_by_email(self):
        # Setup
        MockAdapter.expected = {'member_id': 201, 'email': "test@example.com"}

        member = self.members["test@example.com"]

        self.assertIn(201, self.members)
        self.assertIsInstance(member, Member)
        self.assertEqual(self.members[201]['member_id'], 201)
        self.assertEqual(self.members[201]['email'], "test@example.com")
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(
            self.members.account.adapter.call,
            ('GET', '/members/email/test@example.com', {}))

    def test_dictionary_access_lazy_loads_by_email2(self):
        # Setup
        MockAdapter.expected = {'member_id': 201, 'email': "test@example.com"}

        member = self.members["test@example.com"]

        self.assertIn(201, self.members)
        self.assertIsInstance(member, Member)
        self.assertEqual(self.members[201]['member_id'], 201)
        self.assertEqual(self.members[201]['email'], "test@example.com")
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(
            self.members.account.adapter.call,
            ('GET', '/members/email/test@example.com', {}))

    def test_dictionary_access_lazy_loads_by_email3(self):
        # Setup
        MockAdapter.expected = None

        member = self.members.get("test@example.com")

        self.assertEqual(0, len(self.members))
        self.assertIsNone(member)
        self.assertEqual(1, self.members.account.adapter.called)
        self.assertEqual(
            self.members.account.adapter.call,
            ('GET', '/members/email/test@example.com', {}))

    def test_dictionary_access_lazy_loads_by_email4(self):
        # Setup
        MockAdapter.expected = None

        member = self.members.get("test@example.com")

        self.assertEqual(0, len(self.members))
        self.assertIsNone(member)
        self.assertEqual(1, self.members.account.adapter.called)
        self.assertEqual(
            self.members.account.adapter.call,
            ('GET', '/members/email/test@example.com', {}))

    def test_can_add_members_in_bulk(self):
        MockAdapter.expected = {'import_id': 1024}
        import_id = self.members.save()
        self.assertIsNone(import_id)
        self.assertEqual(self.members.account.adapter.called, 0)

    def test_can_add_members_in_bulk2(self):
        # Setup
        MockAdapter.expected = {'import_id': 1024}
        self.members.account.fields._dict = {
            2000: {'shortcut_name': "first_name"},
            2001: {'shortcut_name': "last_name"}
        }

        # Attempt save
        with self.assertRaises(ex.NoMemberEmailError):
            self.members.save([
                Member(self.members.account),
                Member(self.members.account)
            ])

        self.assertEqual(self.members.account.adapter.called, 0)

    def test_can_add_members_in_bulk3(self):
        # Setup
        MockAdapter.expected = {'import_id': 1024}
        self.members.account.fields._dict = {
            2000: {'shortcut_name': "first_name"},
            2001: {'shortcut_name': "last_name"}
        }

        # Perform add
        import_id = self.members.save([
            self.members.factory({
                'email': "test1@example.com",
                'does_not_exist': "A member field which does not exist"
            }),
            self.members.factory({
                'email': "test2@example.com",
                'first_name': "Emma"
            })
        ])

        self.assertIsInstance(import_id, dict)
        self.assertTrue('import_id' in import_id)
        self.assertEqual(import_id['import_id'], 1024)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(self.members.account.adapter.call, (
            'POST',
            '/members',
            {
                'members': [
                    {'email': "test1@example.com"},
                    {
                        'email': "test2@example.com",
                        'fields': {'first_name': "Emma"}
                    }
                ]
            }
        ))

    def test_can_add_members_in_bulk4(self):
        # Setup
        MockAdapter.expected = {'import_id': 1024}
        self.members.account.fields._dict = {
            2000: {'shortcut_name': "first_name"},
            2001: {'shortcut_name': "last_name"}
        }
        self.members._dict = {
            200: Member(self.members.account, {
                'member_id': 200,
                'email': "test1@example.com",
                'does_not_exist': "A member field which does not exist"
            }),
            201: Member(self.members.account, {
                'member_id': 201,
                'email': "test2@example.com",
                'first_name': "Emma"
            })
        }

        # Perform update
        import_id = self.members.save()

        self.assertIsInstance(import_id, dict)
        self.assertTrue('import_id' in import_id)
        self.assertEqual(import_id['import_id'], 1024)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(self.members.account.adapter.call, (
            'POST',
            '/members',
            {
                'members': [
                    {
                        'member_id': 200,
                        'email': "test1@example.com"},
                    {
                        'member_id': 201,
                        'email': "test2@example.com",
                        'fields': {'first_name': "Emma"}}
                ]
            }
        ))

    def test_can_add_members_in_bulk5(self):
        # Setup
        MockAdapter.expected = {'import_id': 1024}
        self.members.account.fields._dict = {
            2000: {'shortcut_name': "first_name"},
            2001: {'shortcut_name': "last_name"}
        }
        self.members._dict = {
            200: Member(self.members.account, {
                'member_id': 200,
                'email': "test1@example.com",
                'does_not_exist': "A member field which does not exist"
            })
        }

        # Perform add & update
        import_id = self.members.save([
            self.members.factory({
                'email': "test2@example.com",
                'first_name': "Emma"
            })
        ])

        self.assertIsInstance(import_id, dict)
        self.assertTrue('import_id' in import_id)
        self.assertEqual(import_id['import_id'], 1024)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(self.members.account.adapter.call, (
            'POST',
            '/members',
            {
                'members': [
                    {
                        'email': "test2@example.com",
                        'fields': {'first_name': "Emma"}},
                    {
                        'member_id': 200,
                        'email': "test1@example.com"}

                ]
            }
        ))

    def test_can_add_members_in_bulk6(self):
        # Setup
        MockAdapter.expected = {'import_id': 1024}
        self.members.account.fields._dict = {
            2000: {'shortcut_name': "first_name"},
            2001: {'shortcut_name': "last_name"}
        }

        # Perform save with "add-only"
        import_id = self.members.save([
            self.members.factory({
                'email': "test1@example.com",
                'does_not_exist': "A member field which does not exist"
            }),
            self.members.factory({
                'email': "test2@example.com",
                'first_name': "Emma"
            })
        ], add_only=True)

        self.assertIsInstance(import_id, dict)
        self.assertTrue('import_id' in import_id)
        self.assertEqual(import_id['import_id'], 1024)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(self.members.account.adapter.call, (
            'POST',
            '/members',
            {
                'members': [
                    {'email': "test1@example.com"},
                    {'email': "test2@example.com",
                     'fields': {'first_name': "Emma"}}
                ],
                'add_only': True
            }
        ))

    def test_can_add_members_in_bulk7(self):
        # Setup
        MockAdapter.expected = {'import_id': 1024}
        self.members.account.fields._dict = {
            2000: {'shortcut_name': "first_name"},
            2001: {'shortcut_name': "last_name"}
        }
        self.members._dict = {
            200: Member(self.members.account, {
                'member_id': 200,
                'email': "test1@example.com",
                'does_not_exist': "A member field which does not exist"
            }),
            201: Member(self.members.account, {
                'member_id': 201,
                'email': "test2@example.com",
                'first_name': "Emma"
            })
        }

        # Perform save with "add-only"
        import_id = self.members.save(add_only=True)

        self.assertIsNone(import_id, None)
        self.assertEqual(self.members.account.adapter.called, 0)

    def test_can_add_members_in_bulk8(self):
        # Setup
        MockAdapter.expected = {'import_id': 1024}
        self.members.account.fields._dict = {
            2000: {'shortcut_name': "first_name"},
            2001: {'shortcut_name': "last_name"}
        }
        self.members._dict = {
            200: Member(self.members.account, {
                'member_id': 200,
                'email': "test1@example.com",
                'does_not_exist': "A member field which does not exist"
            })
        }

        # Perform save with "add-only"
        import_id = self.members.save([
            self.members.factory({
                'email': "test2@example.com",
                'first_name': "Emma"
            })
        ], add_only=True)

        self.assertIsInstance(import_id, dict)
        self.assertTrue('import_id' in import_id)
        self.assertEqual(import_id['import_id'], 1024)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(self.members.account.adapter.call, (
            'POST',
            '/members',
            {
                'members': [
                    {
                        'email': "test2@example.com",
                        'fields': {'first_name': "Emma"}}

                ],
                'add_only': True
            }
        ))

    def test_can_add_members_in_bulk9(self):
        # Setup
        MockAdapter.expected = {'import_id': 1024}
        self.members.account.fields._dict = {
            2000: {'shortcut_name': "first_name"},
            2001: {'shortcut_name': "last_name"}
        }

        # Perform add
        import_id = self.members.save([
            self.members.factory({
                'email': "test1@example.com"
            })
        ], filename="test.csv", group_ids=[300, 301, 302])

        self.assertIsInstance(import_id, dict)
        self.assertTrue('import_id' in import_id)
        self.assertEqual(import_id['import_id'], 1024)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(self.members.account.adapter.call, (
            'POST',
            '/members',
            {
                'members': [{'email': "test1@example.com"}],
                'filename': "test.csv",
                'group_ids': [300, 301, 302]
            }
        ))

    def test_can_delete_a_single_member_with_del(self):
        # Setup
        MockAdapter.expected = True
        self.members._dict = {
            200: Member(self.members.account, {
                'member_id': 200,
                'email': "test1@example.com",
                'does_not_exist': "A member field which does not exist"
            }),
            201: Member(self.members.account, {
                'member_id': 201,
                'email': "test2@example.com",
                'first_name': "Emma"
            })
        }

        del(self.members[200])

        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(
            self.members.account.adapter.call,
            ('DELETE', '/members/200', {}))
        self.assertEqual(1, len(self.members))
        self.assertIn(201, self.members)

    def test_can_delete_members_in_bulk(self):
        # Setup
        MockAdapter.expected = False
        self.members._dict = {
            200: Member(self.members.account, {
                'member_id': 200,
                'email': "test1@example.com",
                'does_not_exist': "A member field which does not exist"
            }),
            201: Member(self.members.account, {
                'member_id': 201,
                'email': "test2@example.com",
                'first_name': "Emma"
            })
        }

        with self.assertRaises(ex.MemberDeleteError):
            self.members.delete([200, 201])

        self.assertEqual(2, len(self.members))
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(self.members.account.adapter.call, (
            'PUT',
            '/members/delete',
            {'member_ids': [200, 201]}
        ))

    def test_can_delete_members_in_bulk2(self):
        # Setup
        MockAdapter.expected = True
        self.members._dict = {
            200: Member(self.members.account, {
                'member_id': 200,
                'email': "test1@example.com",
                'does_not_exist': "A member field which does not exist"
            }),
            201: Member(self.members.account, {
                'member_id': 201,
                'email': "test2@example.com",
                'first_name': "Emma"
            })
        }

        self.members.delete([200])

        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(self.members.account.adapter.call, (
            'PUT',
            '/members/delete',
            {'member_ids': [200]}
        ))
        self.assertEqual(1, len(self.members))
        self.assertNotIn(200, self.members)
        self.assertIsInstance(self.members[201], Member)

    def test_can_delete_members_in_bulk3(self):
        # Setup
        MockAdapter.expected = True
        self.members._dict = {
            200: Member(self.members.account, {
                'member_id': 200,
                'email': "test1@example.com",
                'does_not_exist': "A member field which does not exist"
            }),
            201: Member(self.members.account, {
                'member_id': 201,
                'email': "test2@example.com",
                'first_name': "Emma"
            })
        }

        self.members.delete([200, 201])

        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(self.members.account.adapter.call, (
            'PUT',
            '/members/delete',
            {'member_ids': [200, 201]}
            ))
        self.assertEqual(0, len(self.members))

    def test_can_delete_members_in_bulk4(self):
        self.members._dict = {
            200: Member(self.members.account, {
                'member_id': 200,
                'email': "test1@example.com",
                'does_not_exist': "A member field which does not exist"
            }),
            201: Member(self.members.account, {
                'member_id': 201,
                'email': "test2@example.com",
                'first_name': "Emma"
            })
        }

        self.members.delete()

        self.assertEqual(self.members.account.adapter.called, 0)
        self.assertEqual(2, len(self.members))

    def test_can_delete_members_by_status(self):
        # Setup
        MockAdapter.expected = False
        self.members._dict = {
            200: Member(self.members.account, {
                'member_id': 200,
                'email': "test1@example.com",
                'member_status_id': MemberStatus.Active
            }),
            201: Member(self.members.account, {
                'member_id': 201,
                'email': "test2@example.com",
                'member_status_id': MemberStatus.OptOut
            })
        }

        with self.assertRaises(ex.MemberDeleteError):
            self.members.delete_by_status(MemberStatus.OptOut)

        self.assertEqual(2, len(self.members))
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(
            self.members.account.adapter.call,
            ('DELETE', '/members', {'member_status_id': "o"})
        )

    def test_can_delete_members_by_status2(self):
        # Setup
        MockAdapter.expected = True
        self.members._dict = {
            200: Member(self.members.account, {
                'member_id': 200,
                'email': "test1@example.com",
                'member_status_id': MemberStatus.Active
            }),
            201: Member(self.members.account, {
                'member_id': 201,
                'email': "test2@example.com",
                'member_status_id': MemberStatus.OptOut
            })
        }

        result = self.members.delete_by_status(MemberStatus.OptOut)

        self.assertIsNone(result)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(
            self.members.account.adapter.call,
            ('DELETE', '/members', {'member_status_id': "o"})
        )
        self.assertEqual(1, len(self.members))
        self.assertIsInstance(self.members[200], Member)

    def test_can_change_status_of_members_in_bulk(self):
        self.members.change_status_by_member_id()
        self.assertEqual(self.members.account.adapter.called, 0)

    def test_can_change_status_of_members_in_bulk2(self):
        # Setup
        MockAdapter.expected = False
        self.members._dict = {
            200: Member(self.members.account, {
                'member_id': 200,
                'email': "test1@example.com",
                'status': MemberStatus.Active
            }),
            201: Member(self.members.account, {
                'member_id': 201,
                'email': "test2@example.com",
                'status': MemberStatus.Active
            })
        }

        with self.assertRaises(ex.MemberChangeStatusError):
            self.members.change_status_by_member_id([200, 201], MemberStatus.OptOut)

        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(self.members.account.adapter.call, (
            'PUT',
            '/members/status',
            {'member_ids': [200, 201], 'status_to': "o"}
        ))

    def test_can_change_status_of_members_in_bulk3(self):
        # Setup
        MockAdapter.expected = True
        self.members._dict = {
            200: Member(self.members.account, {
                'member_id': 200,
                'email': "test1@example.com",
                'status': MemberStatus.Active
            }),
            201: Member(self.members.account, {
                'member_id': 201,
                'email': "test2@example.com",
                'status': MemberStatus.Active
            })
        }

        self.members.change_status_by_member_id([200], MemberStatus.OptOut)

        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(self.members.account.adapter.call, (
            'PUT',
            '/members/status',
            {'member_ids': [200], 'status_to': "o"}
        ))
        self.assertEqual(2, len(self.members))
        self.assertEqual(MemberStatus.OptOut, self.members[200]['status'])
        self.assertEqual(MemberStatus.Active, self.members[201]['status'])

    def test_can_change_status_of_members_in_bulk4(self):
        # Setup
        MockAdapter.expected = True
        self.members._dict = {
            200: Member(self.members.account, {
                'member_id': 200,
                'email': "test1@example.com",
                'status': MemberStatus.Active
            }),
            201: Member(self.members.account, {
                'member_id': 201,
                'email': "test2@example.com",
                'status': MemberStatus.Active
            })
        }

        self.members.change_status_by_member_id([200, 201], MemberStatus.OptOut)

        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(self.members.account.adapter.call, (
            'PUT',
            '/members/status',
            {'member_ids': [200, 201], 'status_to': "o"}
            ))
        self.assertEqual(2, len(self.members))
        self.assertEqual(MemberStatus.OptOut, self.members[200]['status'])
        self.assertEqual(MemberStatus.OptOut, self.members[201]['status'])

    def test_can_change_status_of_members_in_bulk5(self):
        # Setup
        MockAdapter.expected = True
        self.members._dict = {
            200: Member(self.members.account, {
                'member_id': 200,
                'email': "test1@example.com",
                'status': MemberStatus.Error
            }),
            201: Member(self.members.account, {
                'member_id': 201,
                'email': "test2@example.com",
                'status': MemberStatus.Error
            })
        }

        self.members.change_status_by_member_id([200, 201])

        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(self.members.account.adapter.call, (
            'PUT',
            '/members/status',
            {'member_ids': [200, 201], 'status_to': "a"}
            ))
        self.assertEqual(2, len(self.members))
        self.assertEqual(MemberStatus.Active, self.members[200]['status'])
        self.assertEqual(MemberStatus.Active, self.members[201]['status'])

    def test_can_change_status_of_members_in_bulk6(self):
        MockAdapter.expected = False

        with self.assertRaises(ex.MemberChangeStatusError):
            self.members.change_status_by_status(
                MemberStatus.Error,
                MemberStatus.Active)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(self.members.account.adapter.call,
            ('PUT', '/members/status/e/to/a', {}))

    def test_can_change_status_of_members_in_bulk7(self):
        MockAdapter.expected = True
        result = self.members.change_status_by_status(
            MemberStatus.Error,
            MemberStatus.Active)
        self.assertIsNone(result)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(self.members.account.adapter.call,
            ('PUT', '/members/status/e/to/a', {}))

    def test_can_change_status_of_members_in_bulk8(self):
        MockAdapter.expected = True

        result = self.members.change_status_by_status(
            MemberStatus.Error,
            MemberStatus.Active,
            200)
        self.assertIsNone(result)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(self.members.account.adapter.call,
            ('PUT', '/members/status/e/to/a', {'group_id': 200}))

    def test_can_drop_groups_of_members_in_bulk(self):
        self.members.drop_groups()
        self.assertEqual(self.members.account.adapter.called, 0)

    def test_can_drop_groups_of_members_in_bulk2(self):
        self.members.drop_groups([123, 321])
        self.assertEqual(self.members.account.adapter.called, 0)

    def test_can_drop_groups_of_members_in_bulk3(self):
        self.members.drop_groups([], [1024, 1025])
        self.assertEqual(self.members.account.adapter.called, 0)

    def test_can_drop_groups_of_members_in_bulk4(self):
        MockAdapter.expected = False

        with self.assertRaises(ex.MemberDropGroupError):
            self.members.drop_groups([123, 321], [1024, 1025])

        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(self.members.account.adapter.call, (
            'PUT',
            '/members/groups/remove',
            {'member_ids': [123, 321], 'group_ids': [1024, 1025]}
        ))

    def test_can_drop_groups_of_members_in_bulk5(self):
        MockAdapter.expected = True

        result = self.members.drop_groups([123, 321], [1024, 1025])

        self.assertIsNone(result)
        self.assertEqual(self.members.account.adapter.called, 1)
        self.assertEqual(self.members.account.adapter.call, (
            'PUT',
            '/members/groups/remove',
            {'member_ids': [123, 321], 'group_ids': [1024, 1025]}
        ))


class AccountMailingCollectionTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.mailings = Account(
            account_id="100",
            public_key="xxx",
            private_key="yyy").mailings

    def tearDown(self):
        Account.default_adapter.raised = None

    def test_fetch_all_returns_a_dictionary(self):
        MockAdapter.expected = [{'mailing_id': 201}]
        self.assertIsInstance(self.mailings.fetch_all(), dict)
        self.assertEqual(self.mailings.account.adapter.called, 1)
        self.assertEqual(
            self.mailings.account.adapter.call,
            ('GET', '/mailings', {}))

    def test_fetch_all_returns_a_dictionary2(self):
        # Setup
        MockAdapter.expected = [{'mailing_id': 201},{'mailing_id': 204}]

        self.assertIsInstance(self.mailings.fetch_all(include_archived=True), dict)
        self.assertEqual(self.mailings.account.adapter.called, 1)
        self.assertEqual(
            self.mailings.account.adapter.call,
            ('GET', '/mailings', {"include_archived":True}))

    def test_fetch_all_returns_a_dictionary3(self):
        # Setup
        MockAdapter.expected = [{'mailing_id': 201},{'mailing_id': 204}]

        self.assertIsInstance(
            self.mailings.fetch_all(mailing_types=[MailingType.Standard]), dict)
        self.assertEqual(self.mailings.account.adapter.called, 1)
        self.assertEqual(
            self.mailings.account.adapter.call,
            ('GET', '/mailings', {"mailing_types":["m"]}))

    def test_fetch_all_returns_a_dictionary4(self):
        # Setup
        MockAdapter.expected = [{'mailing_id': 201},{'mailing_id': 204}]

        self.assertIsInstance(
            self.mailings.fetch_all(mailing_statuses=[MailingStatus.Complete]),
            dict)
        self.assertEqual(self.mailings.account.adapter.called, 1)
        self.assertEqual(
            self.mailings.account.adapter.call,
            ('GET', '/mailings', {"mailing_statuses":["c"]}))

    def test_fetch_all_returns_a_dictionary5(self):
        # Setup
        MockAdapter.expected = [{'mailing_id': 201},{'mailing_id': 204}]

        self.assertIsInstance(self.mailings.fetch_all(is_scheduled=True), dict)
        self.assertEqual(self.mailings.account.adapter.called, 1)
        self.assertEqual(
            self.mailings.account.adapter.call,
            ('GET', '/mailings', {"is_scheduled":True}))

    def test_fetch_all_returns_a_dictionary6(self):
        # Setup
        MockAdapter.expected = [{'mailing_id': 201},{'mailing_id': 204}]

        self.assertIsInstance(self.mailings.fetch_all(with_html_body=True), dict)
        self.assertEqual(self.mailings.account.adapter.called, 1)
        self.assertEqual(
            self.mailings.account.adapter.call,
            ('GET', '/mailings', {"with_html_body":True}))

    def test_fetch_all_returns_a_dictionary7(self):
        # Setup
        MockAdapter.expected = [{'mailing_id': 201},{'mailing_id': 204}]

        self.assertIsInstance(self.mailings.fetch_all(with_plaintext=True), dict)
        self.assertEqual(self.mailings.account.adapter.called, 1)
        self.assertEqual(
            self.mailings.account.adapter.call,
            ('GET', '/mailings', {"with_plaintext":True}))

    def test_fetch_all_populates_collection(self):
        MockAdapter.expected = [{'mailing_id': 201}]
        self.assertEqual(0, len(self.mailings))
        self.mailings.fetch_all()
        self.assertEqual(1, len(self.mailings))

    def test_fetch_all_caches_results(self):
        MockAdapter.expected = [{'mailing_id': 201}]
        self.mailings.fetch_all()
        self.mailings.fetch_all()
        self.assertEqual(self.mailings.account.adapter.called, 1)

    def test_mailing_collection_object_can_be_accessed_like_a_dictionary(self):
        MockAdapter.expected = [{'mailing_id': 201}]
        self.mailings.fetch_all()
        self.assertIsInstance(self.mailings, AccountMailingCollection)
        self.assertEqual(1, len(self.mailings))
        self.assertIsInstance(self.mailings[201], Mailing)

    def test_fetch_one_by_mailing_id_returns_a_mailing_object(self):
        # Setup
        MockAdapter.expected = {'mailing_id': 201}

        mailing = self.mailings.find_one_by_mailing_id(201)

        self.assertIsInstance(mailing, Mailing)
        self.assertEqual(mailing['mailing_id'], 201)
        self.assertEqual(self.mailings.account.adapter.called, 1)
        self.assertEqual(
            self.mailings.account.adapter.call,
            ('GET', '/mailings/201', {}))

    def test_fetch_one_by_mailing_id_populates_collection(self):
        # Setup
        MockAdapter.expected = {'mailing_id': 201}

        self.mailings.find_one_by_mailing_id(201)

        self.assertIn(201, self.mailings)
        self.assertIsInstance(self.mailings[201], Mailing)
        self.assertEqual(self.mailings[201]['mailing_id'], 201)

    def test_fetch_one_by_mailing_id_caches_result(self):
        # Setup
        MockAdapter.expected = {'mailing_id': 201}

        self.mailings.find_one_by_mailing_id(201)
        self.mailings.find_one_by_mailing_id(201)

        self.assertEqual(self.mailings.account.adapter.called, 1)

    def test_dictionary_access_lazy_loads_by_mailing_id(self):
        # Setup
        MockAdapter.expected = {'mailing_id': 201}

        mailing = self.mailings[201]

        self.assertIn(201, self.mailings)
        self.assertIsInstance(mailing, Mailing)
        self.assertEqual(self.mailings[201]['mailing_id'], 201)
        self.assertEqual(self.mailings.account.adapter.called, 1)
        self.assertEqual(
            self.mailings.account.adapter.call,
            ('GET', '/mailings/201', {}))

    def test_dictionary_access_lazy_loads_by_mailing_id2(self):
        # Setup
        MockAdapter.expected = None

        mailing = self.mailings.get(204)

        self.assertEqual(0, len(self.mailings))
        self.assertIsNone(mailing)
        self.assertEqual(self.mailings.account.adapter.called, 1)
        self.assertEqual(
            self.mailings.account.adapter.call,
            ('GET', '/mailings/204', {}))

    def test_can_validate_tag_syntax(self):
        MockAdapter.expected = True

        valid = self.mailings.validate(subject="Test Subject")

        self.assertEqual(self.mailings.account.adapter.called, 1)
        self.assertEqual(
            self.mailings.account.adapter.call,
            ('POST', '/mailings/validate', {'subject':"Test Subject"}))
        self.assertTrue(valid)

    def test_can_validate_tag_syntax2(self):
        class MockResponse:
            pass
        MockAdapter.raised = ex.ApiRequest400(MockResponse())

        with self.assertRaises(ex.SyntaxValidationError) as e:
            self.mailings.validate(subject="Test Subject")

        self.assertEqual(self.mailings.account.adapter.called, 1)
        self.assertEqual(
            self.mailings.account.adapter.call,
            ('POST', '/mailings/validate', {'subject':"Test Subject"}))
        self.assertIsInstance(e.exception.message, MockResponse)

    def test_can_validate_tag_syntax3(self):
        MockAdapter.expected = True

        valid = self.mailings.validate(
            html_body="<p>Test Body</p>",
            plaintext="Test Body",
            subject="Test Subject"
        )

        self.assertEqual(self.mailings.account.adapter.called, 1)
        self.assertEqual(
            self.mailings.account.adapter.call,
            (
                'POST',
                '/mailings/validate',
                {
                    'html_body':"<p>Test Body</p>",
                    'plaintext':"Test Body",
                    'subject':"Test Subject"
                }))
        self.assertTrue(valid)

    def test_can_validate_tag_syntax4(self):
        valid = self.mailings.validate()

        self.assertEqual(self.mailings.account.adapter.called, 0)
        self.assertFalse(valid)


class AccountSearchCollectionTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.searches = Account(
            account_id="100",
            public_key="xxx",
            private_key="yyy").searches

    def test_fetch_all_returns_a_dictionary(self):
        MockAdapter.expected = [{'search_id': 201}]
        self.assertIsInstance(self.searches.fetch_all(), dict)
        self.assertEqual(self.searches.account.adapter.called, 1)
        self.assertEqual(
            self.searches.account.adapter.call,
            ('GET', '/searches', {}))

    def test_fetch_all_returns_a_dictionary2(self):
        # Setup
        MockAdapter.expected = [{'search_id': 201},{'search_id': 204}]

        self.assertIsInstance(self.searches.fetch_all(deleted=True), dict)
        self.assertEqual(self.searches.account.adapter.called, 1)
        self.assertEqual(
            self.searches.account.adapter.call,
            ('GET', '/searches', {"deleted":True}))

    def test_fetch_all_populates_collection(self):
        MockAdapter.expected = [{'search_id': 201}]
        self.assertEqual(0, len(self.searches))
        self.searches.fetch_all()
        self.assertEqual(1, len(self.searches))

    def test_fetch_all_caches_results(self):
        MockAdapter.expected = [{'search_id': 201}]
        self.searches.fetch_all()
        self.searches.fetch_all()
        self.assertEqual(self.searches.account.adapter.called, 1)

    def test_search_collection_object_can_be_accessed_like_a_dictionary(self):
        MockAdapter.expected = [{'search_id': 201}]
        self.searches.fetch_all()
        self.assertIsInstance(self.searches, AccountSearchCollection)
        self.assertEqual(1, len(self.searches))
        self.assertIsInstance(self.searches[201], Search)

    def test_find_one_by_search_id_returns_an_import_object(self):
        MockAdapter.expected = {'search_id': 201}
        search = self.searches.find_one_by_search_id(201)
        self.assertIsInstance(search, Search)
        self.assertEqual(search['search_id'], 201)
        self.assertEqual(self.searches.account.adapter.called, 1)
        self.assertEqual(
            self.searches.account.adapter.call,
            ('GET', '/searches/201', {}))

    def test_find_one_by_search_id_populates_collection(self):
        MockAdapter.expected = {'search_id': 201}
        self.searches.find_one_by_search_id(201)
        self.assertIn(201, self.searches)
        self.assertIsInstance(self.searches[201], Search)
        self.assertEqual(self.searches[201]['search_id'], 201)

    def test_find_one_by_search_id_caches_result(self):
        MockAdapter.expected = {'search_id': 201}
        self.searches.find_one_by_search_id(201)
        self.searches.find_one_by_search_id(201)
        self.assertEqual(self.searches.account.adapter.called, 1)

    def test_dictionary_access_lazy_loads_by_search_id(self):
        MockAdapter.expected = {'search_id': 201}
        search = self.searches[201]
        self.assertIn(201, self.searches)
        self.assertIsInstance(search, Search)
        self.assertEqual(self.searches[201]['search_id'], 201)
        self.assertEqual(self.searches.account.adapter.called, 1)
        self.assertEqual(
            self.searches.account.adapter.call,
            ('GET', '/searches/201', {}))

    def test_dictionary_access_lazy_loads_by_search_id2(self):
        MockAdapter.expected = None
        search = self.searches.get(204)
        self.assertEqual(0, len(self.searches))
        self.assertIsNone(search)
        self.assertEqual(self.searches.account.adapter.called, 1)
        self.assertEqual(
            self.searches.account.adapter.call,
            ('GET', '/searches/204', {}))

    def test_can_delete_a_single_search_with_del(self):
        # Setup
        MockAdapter.expected = True
        self.searches._dict = {
            200: Search(self.searches.account, {'search_id': 200}),
            201: Search(self.searches.account, {'search_id': 201})
        }

        del(self.searches[200])

        self.assertEqual(self.searches.account.adapter.called, 1)
        self.assertEqual(
            self.searches.account.adapter.call,
            ('DELETE', '/searches/200', {}))
        self.assertEqual(1, len(self.searches))
        self.assertIn(201, self.searches)


class AccountTriggerCollectionTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.triggers = Account(
            account_id="100",
            public_key="xxx",
            private_key="yyy").triggers

    def test_fetch_all_returns_a_dictionary(self):
        MockAdapter.expected = [{'trigger_id': 201}]
        self.assertIsInstance(self.triggers.fetch_all(), dict)
        self.assertEqual(self.triggers.account.adapter.called, 1)
        self.assertEqual(
            self.triggers.account.adapter.call,
            ('GET', '/triggers', {}))

    def test_fetch_all_populates_collection(self):
        MockAdapter.expected = [{'trigger_id': 201}]
        self.assertEqual(0, len(self.triggers))
        self.triggers.fetch_all()
        self.assertEqual(1, len(self.triggers))

    def test_fetch_all_caches_results(self):
        MockAdapter.expected = [{'trigger_id': 201}]
        self.triggers.fetch_all()
        self.triggers.fetch_all()
        self.assertEqual(self.triggers.account.adapter.called, 1)

    def test_trigger_collection_object_can_be_accessed_like_a_dictionary(self):
        MockAdapter.expected = [{'trigger_id': 201}]
        self.triggers.fetch_all()
        self.assertIsInstance(self.triggers, AccountTriggerCollection)
        self.assertEqual(1, len(self.triggers))
        self.assertIsInstance(self.triggers[201], Trigger)

    def test_find_one_by_trigger_id_returns_an_import_object(self):
        MockAdapter.expected = {'trigger_id': 201}
        search = self.triggers.find_one_by_trigger_id(201)
        self.assertIsInstance(search, Trigger)
        self.assertEqual(search['trigger_id'], 201)
        self.assertEqual(self.triggers.account.adapter.called, 1)
        self.assertEqual(
            self.triggers.account.adapter.call,
            ('GET', '/triggers/201', {}))

    def test_find_one_by_trigger_id_populates_collection(self):
        MockAdapter.expected = {'trigger_id': 201}
        self.triggers.find_one_by_trigger_id(201)
        self.assertIn(201, self.triggers)
        self.assertIsInstance(self.triggers[201], Trigger)
        self.assertEqual(self.triggers[201]['trigger_id'], 201)

    def test_find_one_by_trigger_id_caches_result(self):
        MockAdapter.expected = {'trigger_id': 201}
        self.triggers.find_one_by_trigger_id(201)
        self.triggers.find_one_by_trigger_id(201)
        self.assertEqual(self.triggers.account.adapter.called, 1)

    def test_dictionary_access_lazy_loads_by_trigger_id(self):
        MockAdapter.expected = {'trigger_id': 201}
        trigger = self.triggers[201]
        self.assertIn(201, self.triggers)
        self.assertIsInstance(trigger, Trigger)
        self.assertEqual(self.triggers[201]['trigger_id'], 201)
        self.assertEqual(self.triggers.account.adapter.called, 1)
        self.assertEqual(
            self.triggers.account.adapter.call,
            ('GET', '/triggers/201', {}))

    def test_dictionary_access_lazy_loads_by_trigger_id2(self):
        MockAdapter.expected = None
        search = self.triggers.get(204)
        self.assertEqual(0, len(self.triggers))
        self.assertIsNone(search)
        self.assertEqual(self.triggers.account.adapter.called, 1)
        self.assertEqual(
            self.triggers.account.adapter.call,
            ('GET', '/triggers/204', {}))

    def test_can_delete_a_single_trigger_with_del(self):
        # Setup
        MockAdapter.expected = True
        self.triggers._dict = {
            200: self.triggers.factory({'trigger_id': 200}),
            201: self.triggers.factory({'trigger_id': 201})
        }

        del(self.triggers[200])

        self.assertEqual(self.triggers.account.adapter.called, 1)
        self.assertEqual(
            self.triggers.account.adapter.call,
            ('DELETE', '/triggers/200', {}))
        self.assertEqual(1, len(self.triggers))
        self.assertIn(201, self.triggers)


class AccountWebHookCollectionTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.webhooks = Account(
            account_id="100",
            public_key="xxx",
            private_key="yyy").webhooks

    def test_fetch_all_returns_a_dictionary(self):
        MockAdapter.expected = [{'webhook_id': 201}]
        self.assertIsInstance(self.webhooks.fetch_all(), dict)
        self.assertEqual(self.webhooks.account.adapter.called, 1)
        self.assertEqual(
            self.webhooks.account.adapter.call,
            ('GET', '/webhooks', {}))

    def test_fetch_all_populates_collection(self):
        MockAdapter.expected = [{'webhook_id': 201}]
        self.assertEqual(0, len(self.webhooks))
        self.webhooks.fetch_all()
        self.assertEqual(1, len(self.webhooks))

    def test_fetch_all_caches_results(self):
        MockAdapter.expected = [{'webhook_id': 201}]
        self.webhooks.fetch_all()
        self.webhooks.fetch_all()
        self.assertEqual(self.webhooks.account.adapter.called, 1)

    def test_webhook_collection_object_can_be_accessed_like_a_dictionary(self):
        MockAdapter.expected = [{'webhook_id': 201}]
        self.webhooks.fetch_all()
        self.assertIsInstance(self.webhooks, AccountWebHookCollection)
        self.assertEqual(1, len(self.webhooks))
        self.assertIsInstance(self.webhooks[201], WebHook)

    def test_find_one_by_webhook_id_returns_an_import_object(self):
        MockAdapter.expected = {'webhook_id': 201}
        webhook = self.webhooks.find_one_by_webhook_id(201)
        self.assertIsInstance(webhook, WebHook)
        self.assertEqual(webhook['webhook_id'], 201)
        self.assertEqual(self.webhooks.account.adapter.called, 1)
        self.assertEqual(
            self.webhooks.account.adapter.call,
            ('GET', '/webhooks/201', {}))

    def test_find_one_by_webhook_id_populates_collection(self):
        MockAdapter.expected = {'webhook_id': 201}
        self.webhooks.find_one_by_webhook_id(201)
        self.assertIn(201, self.webhooks)
        self.assertIsInstance(self.webhooks[201], WebHook)
        self.assertEqual(self.webhooks[201]['webhook_id'], 201)

    def test_find_one_by_webhook_id_caches_result(self):
        MockAdapter.expected = {'webhook_id': 201}
        self.webhooks.find_one_by_webhook_id(201)
        self.webhooks.find_one_by_webhook_id(201)
        self.assertEqual(self.webhooks.account.adapter.called, 1)

    def test_dictionary_access_lazy_loads_by_webhook_id(self):
        MockAdapter.expected = {'webhook_id': 201}
        webhook = self.webhooks[201]
        self.assertIn(201, self.webhooks)
        self.assertIsInstance(webhook, WebHook)
        self.assertEqual(self.webhooks[201]['webhook_id'], 201)
        self.assertEqual(self.webhooks.account.adapter.called, 1)
        self.assertEqual(
            self.webhooks.account.adapter.call,
            ('GET', '/webhooks/201', {}))

    def test_dictionary_access_lazy_loads_by_webhook_id2(self):
        MockAdapter.expected = None
        webhook = self.webhooks.get(204)
        self.assertEqual(0, len(self.webhooks))
        self.assertIsNone(webhook)
        self.assertEqual(self.webhooks.account.adapter.called, 1)
        self.assertEqual(
            self.webhooks.account.adapter.call,
            ('GET', '/webhooks/204', {}))

    def test_can_delete_a_single_webhook_with_del(self):
        # Setup
        MockAdapter.expected = True
        self.webhooks._dict = {
            200: self.webhooks.factory({'webhook_id': 200}),
            201: self.webhooks.factory({'webhook_id': 201})
        }

        del(self.webhooks[200])

        self.assertEqual(self.webhooks.account.adapter.called, 1)
        self.assertEqual(
            self.webhooks.account.adapter.call,
            ('DELETE', '/webhooks/200', {}))
        self.assertEqual(1, len(self.webhooks))
        self.assertIn(201, self.webhooks)

    def test_can_delete_all_webhooks(self):
        # Setup
        MockAdapter.expected = True
        self.webhooks._dict = {
            200: WebHook(self.webhooks.account, {'webhook_id': 200}),
            201: WebHook(self.webhooks.account, {'webhook_id': 201})
        }

        result = self.webhooks.delete_all()

        self.assertIsNone(result)
        self.assertEqual(self.webhooks.account.adapter.called, 1)
        self.assertEqual(
            self.webhooks.account.adapter.call,
            ('DELETE', '/webhooks', {}))
        self.assertEqual(0, len(self.webhooks))

    def test_can_delete_all_webhooks2(self):
        # Setup
        MockAdapter.expected = False
        self.webhooks._dict = {
            200: WebHook(self.webhooks.account, {'webhook_id': 200}),
            201: WebHook(self.webhooks.account, {'webhook_id': 201})
        }

        with self.assertRaises(ex.WebHookDeleteError):
            self.webhooks.delete_all()

        self.assertEqual(self.webhooks.account.adapter.called, 1)
        self.assertEqual(
            self.webhooks.account.adapter.call,
            ('DELETE', '/webhooks', {}))
        self.assertEqual(2, len(self.webhooks))

    def test_can_list_events(self):
        # Setup
        MockAdapter.expected = [
            {
                "event_name": "mailing_finish",
                "webhook_event_id": 1,
                "description": "Fired when a mailing is finished."
            },
            {
                "event_name": "mailing_start",
                "webhook_event_id": 2,
                "description": "Fired when a mailing starts."
            }
        ]

        result = self.webhooks.list_events()

        self.assertIsInstance(result, list)
        self.assertEqual(2, len(result))
        self.assertEqual(self.webhooks.account.adapter.called, 1)
        self.assertEqual(
            self.webhooks.account.adapter.call,
            ('GET', '/webhooks/events', {}))
        self.assertEqual(0, len(self.webhooks))


class AccountWorkflowTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.workflows = Account(
            account_id="100",
            public_key="xxx",
            private_key="yyy").workflows

    def test_fetch_all_returns_a_dictionary(self):
        MockAdapter.expected = [{'workflow_id': 201}]
        self.assertIsInstance(self.workflows.fetch_all(), dict)
        self.assertEqual(self.workflows.account.adapter.called, 1)
        self.assertEqual(
            self.workflows.account.adapter.call,
            ('GET', '/automation/workflows', {}))

    def test_fetch_all_returns_a_dictionary(self):
        MockAdapter.expected = [{'workflow_id': 201}]
        self.assertIsInstance(self.workflows.fetch_all(), dict)
        self.assertEqual(self.workflows.account.adapter.called, 1)
        self.assertEqual(
            self.workflows.account.adapter.call,
            ('GET', '/automation/workflows', {}))

    def test_find_one_by_workflow_id_returns_an_import_object(self):
        MockAdapter.expected = {'workflow_id': 201}
        workflow = self.workflows.find_one_by_workflow_id(201)
        self.assertIsInstance(workflow, Workflow)
        self.assertEqual(workflow['workflow_id'], 201)
        self.assertEqual(self.workflows.account.adapter.called, 1)
        self.assertEqual(
            self.workflows.account.adapter.call,
            ('GET', '/automation/workflows/201', {}))

    def test_find_one_by_workflow_id_populates_collection(self):
        MockAdapter.expected = {'workflow_id': 201}
        self.workflows.find_one_by_workflow_id(201)
        self.assertIn(201, self.workflows)
        self.assertIsInstance(self.workflows[201], Workflow)
        self.assertEqual(self.workflows[201]['workflow_id'], 201)

    def test_find_one_by_workflow_id_caches_result(self):
        MockAdapter.expected = {'workflow_id': 201}
        self.workflows.find_one_by_workflow_id(201)
        self.workflows.find_one_by_workflow_id(201)
        self.assertEqual(self.workflows.account.adapter.called, 1)

