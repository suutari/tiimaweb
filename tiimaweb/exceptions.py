class Error(Exception):
    pass


class LoginFailed(Error):
    pass


class ParseError(Error):
    pass


class UnexpectedResponse(Error):
    pass
