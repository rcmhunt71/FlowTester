
class VMData:

    ATTRS = {'uuid': None,
             'volume': None,
             'flavor': -1,
             'image': None,
             'root_password': None,
             'ip_addr': '0.0.0.0'}

    def __init__(self):

        self.name = None
        self.state = None
        self.uuid = None
        self.metadata = {}
        for attr, value in self.ATTRS.items():
            setattr(self, attr, value)

    def get_data(self):
        data = [['name', f"{self.name}  ({str(self.state).upper()})"]]

        for attr in self.ATTRS.keys():
            data.append([attr, getattr(self, attr)])

        for key, value in self.metadata.items():
            data.append([f"Metadata:", f"{key}: {value}"])

        return data


class VMStates:
    ACTIVE = 'ACTIVE'
    BUILDING = 'BUILDING'
    DELETING = 'DELETING'
    DELETED = 'DELETED'
    DNE = 'DOES_NOT_EXIST'
    ERROR = 'ERROR'
    LOCKED = 'LOCKED'
    PAUSED = 'PAUSED'
    REBOOTING = 'REBOOTING'
    RESIZING = 'RESIZING'
