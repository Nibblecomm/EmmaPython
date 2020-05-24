from datetime import datetime
import unittest
from emma import exceptions as ex
from emma.enumerations import FieldType, WidgetType
from emma.model.account import Account
from emma.model.field import Field
from emma.model import SERIALIZED_DATETIME_FORMAT
from tests.model import MockAdapter


class FieldTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.field = Field(
            Account(account_id="100", public_key="xxx", private_key="yyy"),
            {
                'field_id':200,
                'shortcut_name':"test_field",
                'display_name':"Test Field",
                'field_type':FieldType.TextArray,
                'widget_type':WidgetType.RadioButtonMenu,
                'column_order':3,
                'options':["A", "B", "C"],
                'deleted_at': None
            }
        )

    def test_can_parse_special_fields_correctly(self):
        self.assertIsNone(self.field.get('deleted_at'))

    def test_can_save_a_field(self):
        fld = Field(
            self.field.account,
            {'shortcut_name':"test_field"})
        MockAdapter.expected = 1024

        result = fld.save()

        self.assertIsNone(result)
        self.assertEqual(fld.account.adapter.called, 1)
        self.assertEqual(
            fld.account.adapter.call,
            ('POST', '/fields', {'shortcut_name':"test_field"}))
        self.assertEqual(1024, fld['field_id'])
        self.assertEqual("test_field", fld['shortcut_name'])

    def test_can_save_a_field2(self):
        fld = Field(
            self.field.account,
            {
                'shortcut_name':"test_field",
                'display_name':"Test Field",
                'field_type':FieldType.Text,
                'widget_type':WidgetType.ShortAnswer,
                'column_order':1
            })
        MockAdapter.expected = 1024

        result = fld.save()

        self.assertIsNone(result)
        self.assertEqual(fld.account.adapter.called, 1)
        self.assertEqual(
            fld.account.adapter.call,
            (
                'POST', '/fields',
                {
                    'shortcut_name':"test_field",
                    'display_name':"Test Field",
                    'field_type':"text",
                    'widget_type':"text",
                    'column_order':1
                }))
        self.assertEqual(1024, fld['field_id'])
        self.assertEqual("test_field", fld['shortcut_name'])
        self.assertEqual("Test Field", fld['display_name'])
        self.assertEqual(FieldType.Text, fld['field_type'])
        self.assertEqual(WidgetType.ShortAnswer, fld['widget_type'])
        self.assertEqual(1, fld['column_order'])

    def test_can_save_a_field3(self):
        MockAdapter.expected = 200

        result = self.field.save()

        self.assertIsNone(result)
        self.assertEqual(self.field.account.adapter.called, 1)
        self.assertEqual(self.field.account.adapter.call,
            (
                'PUT',
                '/fields/200',
                {
                    'shortcut_name':"test_field",
                    'display_name':"Test Field",
                    'field_type':"text[]",
                    'widget_type':"radio",
                    'column_order':3,
                    'options': ["A", "B", "C"]
                }
            ))

    def test_can_delete_a_field(self):
        fld = Field(self.field.account)

        with self.assertRaises(ex.NoFieldIdError):
            fld.delete()
        self.assertEqual(self.field.account.adapter.called, 0)
        self.assertFalse(self.field.is_deleted())

    def test_can_delete_a_field2(self):
        MockAdapter.expected = None
        fld = Field(
            self.field.account,
            {
                'field_id': 200,
                'deleted_at': datetime.now().strftime(SERIALIZED_DATETIME_FORMAT)
            })

        result = fld.delete()

        self.assertIsNone(result)
        self.assertEqual(fld.account.adapter.called, 0)
        self.assertTrue(fld.is_deleted())

    def test_can_delete_a_field3(self):
        MockAdapter.expected = True
        fld = Field(
            self.field.account,
            {
                'field_id': 200,
                'deleted_at': None
            })

        result = fld.delete()

        self.assertIsNone(result)
        self.assertEqual(fld.account.adapter.called, 1)
        self.assertEqual(
            fld.account.adapter.call,
            ('DELETE', '/fields/200', {}))
        self.assertTrue(fld.is_deleted())

    def test_can_clear_member_info(self):
        MockAdapter.expected = True

        result = self.field.clear_member_information()

        self.assertIsNone(result)
        self.assertEqual(self.field.account.adapter.called, 1)
        self.assertEqual(
            self.field.account.adapter.call,
            ('POST', '/fields/200/clear', {}))

    def test_can_clear_member_info2(self):
        del(self.field['field_id'])
        with self.assertRaises(ex.NoFieldIdError):
            self.field.clear_member_information()

        self.assertEqual(self.field.account.adapter.called, 0)

    def test_can_clear_member_info3(self):
        MockAdapter.expected = False

        with self.assertRaises(ex.ClearMemberFieldInformationError):
            self.field.clear_member_information()

        self.assertEqual(self.field.account.adapter.called, 1)
        self.assertEqual(
            self.field.account.adapter.call,
            ('POST', '/fields/200/clear', {}))
