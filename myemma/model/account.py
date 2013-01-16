from myemma.adapter.requests_adapter import RequestsAdapter
from . import Collection, MemberDeleteError, MemberChangeStatusError
from emma_import import EmmaImport
from member import Member
from field import Field
from status import Active


class Account(object):
    """
    Aggregate root for the API context

    :param account_id: Your account identifier
    :type account_id: :class:`int` or :class:`str`
    :param public_key: Your public key
    :type public_key: :class:`str`
    :param private_key: Your private key
    :type private_key: :class:`str`

    Usage::

        >>> acct = Account(1234, "08192a3b4c5d6e7f", "f7e6d5c4b3a29180")
        >>> acct.fields
        <FieldCollection>
        >>> acct.imports
        <ImportCollection>
        >>> acct.members
        <MemberCollection>
    """
    default_adapter = RequestsAdapter

    def __init__(self, account_id, public_key, private_key):
        self.adapter = self.__class__.default_adapter({
            "account_id": "%s" % account_id,
            "public_key": public_key,
            "private_key": private_key
        })
        self.fields = FieldCollection(self)
        self.imports = ImportCollection(self)
        self.members = MemberCollection(self)


class FieldCollection(Collection):
    """
    Encapsulates operations for the set of :class:`Field` objects of an
    :class:`account`
    """
    def fetch_all(self):
        """
        Lazy-loads the full set of :class:`Field` objects

        :rtype: :class:`dict` of :class:`Field` objects

        Usage::

            >>> acct = Account(1234, "08192a3b4c5d6e7f", "f7e6d5c4b3a29180")
            >>> acct.fields.fetch_all()
            {123: <Field>, 321: <Field>, ...}
        """
        path = '/fields'
        if not self._dict:
            self._dict = dict(map(
                lambda x: (x[u"field_id"], Field(self.account, x)),
                self.account.adapter.get(path)
            ))
        return self._dict

    def export_shortcuts(self):
        """
        Get a :class:`list` of shortcut names for this account

        :rtype: :class:`list` of :class:`str`

        Usage::

            >>> acct = Account(1234, "08192a3b4c5d6e7f", "f7e6d5c4b3a29180")
            >>> acct.fields.export_shortcuts()
            ["first_name", "last_name", ...]
        """
        return map(
            lambda x: x[u"shortcut_name"],
            self.fetch_all().values()
        )


class MemberCollection(Collection):
    """
    Encapsulates operations for the set of :class:`Member` objects of an
    :class:`account`
    """
    def __getitem__(self, key):
        """
        Overriding again to provide lazy-loading of a member by ID or email
        """
        if isinstance(key, int):
            return self.find_one_by_member_id(key)
        if isinstance(key, str) or isinstance(key, unicode):
            return self.find_one_by_email(key)

    def factory(self, raw={}):
        """
        New :class:`Member` factory

        :param raw: Raw data with which to populate class
        :type raw: :class:`dict`
        :rtype: :class:`Member`

        Usage::

            >>> acct = Account(1234, "08192a3b4c5d6e7f", "f7e6d5c4b3a29180")
            >>> acct.members.factory()
            <Member{}>
            >>> acct.members.factory({'email': u"test@example.com"})
            <Member{'email': u"test@example.com"}>
        """
        return Member(self.account, raw)

    def fetch_all(self, deleted=False):
        """
        Lazy-loads the full set of :class:`Member` objects

        :param deleted: Whether to include deleted members
        :type deleted: :class:`bool`
        :rtype: :class:`dict` of :class:`Member` objects

        Usage::

            >>> acct = Account(1234, "08192a3b4c5d6e7f", "f7e6d5c4b3a29180")
            >>> acct.members.fetch_all()
            {123: <Member>, 321: <Member>, ...}
        """
        path = '/members'
        params = {"deleted":True} if deleted else {}
        if not self._dict:
            self._dict = dict(map(
                lambda x: (x[u"member_id"], Member(self.account, x)),
                self.account.adapter.get(path, params)
            ))
        return self._dict

    def fetch_all_by_import_id(self, import_id):
        """
        Updates the collection with a dictionary of all members from a given
        import. *Does not lazy-load*

        :param import_id: The import identifier
        :type import_id: :class:`int` or :class:`str`
        :rtype: :class:`dict` of :class:`Member` objects

        Usage::

            >>> acct = Account(1234, "08192a3b4c5d6e7f", "f7e6d5c4b3a29180")
            >>> acct.members.fetch_all_by_import_id(123)
            {123: <Member>, 321: <Member>, ...}
        """
        path = '/members/imports/%s/members' % import_id
        members = dict(map(
            lambda x: (x[u"member_id"], Member(self.account, x)),
            self.account.adapter.get(path)
        ))
        self.replace_all(members)
        return members

    def find_one_by_member_id(self, member_id, deleted=False):
        """
        Lazy-loads a single :class:`Member` by ID

        :param member_id: The member identifier
        :type member_id: :class:`int`
        :param deleted: Whether to include deleted members
        :type deleted: :class:`bool`
        :rtype: :class:`Member` or :class:`None`

        Usage::

            >>> acct = Account(1234, "08192a3b4c5d6e7f", "f7e6d5c4b3a29180")
            >>> acct.members.find_one_by_member_id(0) # does not exist
            None
            >>> acct.members.find_one_by_member_id(123)
            <Member{'member_id': 123, 'email': u"test@example.com", ...}>
            >>> acct.members[123]
            <Member{'member_id': 123, 'email': u"test@example.com", ...}>
        """
        path = '/members/%s' % member_id
        params = {"deleted":True} if deleted else {}
        if member_id not in self._dict:
            member = self.account.adapter.get(path, params)
            if member is not None:
                self._dict[member[u"member_id"]] = Member(self.account, member)
                return self._dict[member[u"member_id"]]
        else:
            return self._dict[member_id]

    def find_one_by_email(self, email, deleted=False):
        """
        Lazy-loads a single :class:`Member` by email address

        :param email: The email address
        :type email: :class:`str`
        :param deleted: Whether to include deleted members
        :type deleted: :class:`bool`
        :rtype: :class:`Member` or :class:`None`

        Usage::

            >>> acct = Account(1234, "08192a3b4c5d6e7f", "f7e6d5c4b3a29180")
            >>> acct.members.find_one_by_email("null@example.com") # does not exist
            None
            >>> acct.members.find_one_by_email("test@example.com")
            <Member{'member_id': 123, 'email': u"test@example.com", ...}>
            >>> acct.members["test@example.com"]
            <Member{'member_id': 123, 'email': u"test@example.com", ...}>
        """
        path = '/members/email/%s' % email
        params = {"deleted":True} if deleted else {}
        members = filter(
            lambda x: x[u"email"] == email,
            self._dict.values())
        if not members:
            member = self.account.adapter.get(path, params)
            if member is not None:
                self._dict[member[u"member_id"]] = \
                    Member(self.account, member)
                return self._dict[member[u"member_id"]]
        else:
            member = members[0]
        return member

    def save(self, members=[], filename=None, add_only=False,
             group_ids=[]):
        """
        :param members: List of :class:`Member` objects to save
        :type members: :class:`list` of :class:`Member` objects
        :param filename: An arbitrary string to associate with this import
        :type filename: :class:`str`
        :param add_only: Only add new members, ignore existing members
        :type add_only: :class:`bool`
        :param group_ids: Add imported members to this list of groups
        :type group_ids: :class:`list`
        :rtype: :class:`int` representing an import identifier or :class:`None`

        Usage::

            >>> acct = Account(1234, "08192a3b4c5d6e7f", "f7e6d5c4b3a29180")
            >>> acct.members.save() # no changes
            None
            >>> acct.members[123]['first_name'] = u"Emma"
            >>> acct.members.save()
            2001
            >>> acct.members.save([
            ...     acct.members.factory({'email': u"new1@example.com"}),
            ...     acct.members.factory({'email': u"new2@example.com"}),
            ...     acct.members.factory({'email': u"new3@example.com"})
            ... ])
            2002
        """

        if not members and (not self._dict or add_only) :
            return None

        path = '/members'
        data = {
            'members': (
                map(lambda x: x.extract(), members)
                + ([]
                   if add_only
                   else map(lambda x: x.extract(), self._dict.values())))
        }
        if add_only:
            data['add_only'] = add_only
        if filename:
            data['filename'] = filename
        if group_ids:
            data['group_ids'] = group_ids
        return self.account.adapter.post(path, data)

    def _delete_all(self):
        # Update internal dictionary
        self._dict = {}

    def _delete_list(self, member_ids):
        path = '/members/delete'
        data = {'member_ids': member_ids}
        if not self.account.adapter.put(path, data):
            raise MemberDeleteError()

        # Update internal dictionary
        self._dict = dict(filter(
            lambda x: x[0] not in member_ids,
            self._dict.items()))

    def delete(self, member_ids=[]):
        """
        :param member_ids: Set of member identifiers to delete
        :type member_ids: :class:`list` of :class:`int`
        :rtype: :class:`None`

        Usage::

            >>> acct = Account(1234, "08192a3b4c5d6e7f", "f7e6d5c4b3a29180")
            >>> acct.members.delete([123, 321]) # Deletes members 123, and 321
            None
            >>> acct.members.delete() # Deletes all members on the account
            None
        """
        return self._delete_all() if not member_ids else self._delete_list(member_ids)

    def change_status(self, member_ids=[], status_to=Active):
        """
        :param member_ids: Set of member identifiers to change
        :type member_ids: :class:`list` of :class:`int`
        :param status_to: The new status
        :type status_to: :class:`Status`
        :rtype: :class:`None`

        Usage::

            >>> acct = Account(1234, "08192a3b4c5d6e7f", "f7e6d5c4b3a29180")
            >>> acct.members.change_status([123, 321], Active)
            None
        """
        if not member_ids:
            return None

        path = '/members/status'
        data = {'member_ids': member_ids, 'status_to': status_to.get_code()}
        if not self.account.adapter.put(path, data):
            raise MemberChangeStatusError()

        # Update internal dictionary
        for id in self._dict:
            if id in member_ids:
                self._dict[id]['status'] = status_to


class ImportCollection(Collection):
    """
    Encapsulates operations for the set of :class:`Import` objects of an
    :class:`account`
    """
    def __getitem__(self, key):
        """
        Overriding again to provide lazy-loading of an import by ID
        """
        return self.find_one_by_import_id(key)

    def fetch_all(self):
        """
        Lazy-loads the full set of :class:`Import` objects

        :rtype: :class:`dict` of :class:`Import` objects

        Usage::

            >>> acct = Account(1234, "08192a3b4c5d6e7f", "f7e6d5c4b3a29180")
            >>> acct.imports.fetch_all()
            {123: <Import>, 321: <Import>, ...}

        """
        path = '/members/imports'
        if not self._dict:
            self._dict = dict(map(
                lambda x: (x[u"import_id"], EmmaImport(self.account, x)),
                self.account.adapter.get(path, {})
            ))
        return self._dict

    def find_one_by_import_id(self, import_id):
        """
        Lazy-loads a single :class:`Import` by ID

        :param import_id: The import identifier
        :type import_id: :class:`int` or :class:`str`
        :rtype: :class:`Import` or :class:`None`

        Usage::

            >>> acct = Account(1234, "08192a3b4c5d6e7f", "f7e6d5c4b3a29180")
            >>> acct.imports.find_one_by_import_id(0) # does not exist
            None
            >>> acct.imports.find_one_by_import_id(123)
            <Import>
            >>> acct.imports[123]
            <Import>
        """
        import_id = int(import_id)
        path = '/members/imports/%s' % import_id
        if not self._dict.has_key(import_id):
            emma_import = self.account.adapter.get(path)
            if emma_import is not None:
                self._dict[emma_import[u"import_id"]] = \
                    EmmaImport(self.account, emma_import)
                return self._dict[emma_import[u"import_id"]]
        else:
            return self._dict[import_id]
