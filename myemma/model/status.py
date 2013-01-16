class Status(object):
    @classmethod
    def get_code(cls):
        return cls._code

    @classmethod
    def get_name(cls):
        return cls._name

    @staticmethod
    def factory(status_or_name_or_code):
        return {
            Active: Active,
            Active._code: Active,
            Active._name: Active,
            Error: Error,
            Error._code: Error,
            Error._name: Error,
            Forwarded: Forwarded,
            Forwarded._code: Forwarded,
            Forwarded._name: Forwarded,
            OptOut: OptOut,
            OptOut._code: OptOut,
            OptOut._name: OptOut
        }[status_or_name_or_code]

class Active(Status):
    _code = u"a"
    _name = u"active"

class Error(Status):
    _code = u"e"
    _name = u"error"

class Forwarded(Status):
    _code = u"f"
    _name = u"forwarded"

class OptOut(Status):
    _code = u"o"
    _name = u"opt-out"
