class ActionInterruptedError(Exception):
    """
    This exception can be raised by a :ref:`adminaction_requested` or :ref:`adminaction_start`
     to prevent action to be executed
    """


class FakeTransactionError(Exception):
    pass


class MassUpdateSkipRecordError(Exception):
    pass
