class ImportCheck:

    DEFAULT_RESPONSE = True

    # For use with data/basic_state_machine.yaml

    def __init__(self):
        self.last_call = None
        self.data = None

    def test_routine(self, option=DEFAULT_RESPONSE):
        self.last_call = 'test_routine'
        self.data = option
        return option

    # TRANSITIONS/TRIGGERS
    # ---------------------
    def create(self, data=None):
        self.last_call = 'create'
        self.data = data
        return "create"

    def in_error(self, data):
        self.last_call = 'in_error'
        self.data = data
        return "in_error"

    def delete(self, data):
        self.last_call = 'delete'
        self.data = data
        return "delete"

    # VALIDATIONS
    # ---------------------
    def exists(self, result=True):
        self.last_call = 'exists'
        self.data = result
        return result

    def is_active(self, result=True):
        self.last_call = 'is_active'
        self.data = result
        return result
