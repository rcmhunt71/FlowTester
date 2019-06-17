import random
import string
import time
import uuid

import prettytable

from flowtester.logging import logger
from vm_data_model.data_model.vm_data_class import VMData, VMStates

logging = logger.Logger(project='FlowTester')


class VmModel:
    ACTION_DURATION = 0  # in seconds
    PASSWORD_LENGTH = 18  # characters

    def __init__(self) -> None:
        self.data = VMData()

    def __str__(self) -> str:
        cols = ["Attribute", "Value"]
        table = prettytable.PrettyTable()
        table.field_names = cols
        table.align[cols[0]] = 'l'
        for data in self.data.get_data():
            table.add_row(data)
        return table.get_string()

    def log_state(self) -> None:
        logging.info(f"\n{self}")

    # ===========================================
    #        TRANSITION/ACTION METHODS
    # ===========================================
    def create_server(
            self, result: bool = True, state: str = VMStates.BUILDING) -> bool:
        self.data.name = f"Server{random.randint(0, 1000):04}"
        self.data.flavor = 3
        self.data.image = 'Linux'
        self.data.state = state
        logging.info(f"Creating Server: '{self.data.name}' using flavor '{self.data.flavor}', "
                     f"using a '{self.data.image}' image.")
        self.log_state()
        return result

    def building_server(
            self, result: bool = True, state: str = VMStates.ACTIVE) -> bool:
        self.data.uuid = str(uuid.uuid4())

        if self.data.root_password is None:
            self.data.root_password = ''.join(random.choices(
                string.ascii_uppercase + string.digits + string.ascii_lowercase,
                k=self.PASSWORD_LENGTH))

        if self.data.volume is None:
            self.data.volume = str(uuid.uuid4())

        self.data.state = state
        self.data.ip_addr = '192.168.1.1'

        logging.info(f"Building Server: '{self.data.name}'")
        logging.info(f"Root Password: '{self.data.root_password}'")
        logging.info(f"Mounting a volume '{self.data.volume}' to "
                     f"server '{self.data.name}' ({self.data.uuid})")
        logging.info(f"IPv4 Address: {self.data.ip_addr}")

        self.log_state()
        return result

    def building_server_fail(
            self, result: bool = True, state: str = VMStates.ERROR) -> bool:
        self.building_server(result=result)
        logging.info(f"Failing the build for '{self.data.uuid}'")
        self.data.state = state
        self.log_state()
        return result

    def add_metadata(
            self, key: str = 'test', value: str = 'value',
            state: str = VMStates.ACTIVE, result: bool = True) -> bool:
        logging.info(f"Adding metadata: key: {key}  value:{value}")

        self.data.metadata[key] = value
        self.data.state = state
        self.log_state()
        return result

    def go_into_error(
            self, state: str = VMStates.ERROR, result: bool = True) -> bool:
        logging.info(f"Gone into ERROR state.")
        self.data.state = state
        self.log_state()
        return result

    def reboot_server(
            self, state: str = VMStates.ACTIVE, result: bool = True) -> bool:
        logging.info(f"Rebooting server: '{self.data.uuid}'")

        time.sleep(self.ACTION_DURATION)

        self.data.state = state
        logging.info(f"Rebooted server: {self.data.uuid}")
        self.log_state()
        return result

    def resize_server(
            self, state: str = VMStates.ACTIVE, result: bool = True) -> bool:
        logging.info(f"Resizing server: '{self.data.uuid}'")

        time.sleep(self.ACTION_DURATION)

        self.data.state = state
        logging.info(f"Resized server: {self.data.uuid}")
        self.log_state()
        return result

    def pause_server(
            self, state: str = VMStates.PAUSED, result: bool = True) -> bool:
        logging.info(f"Pausing server: {self.data.uuid}")
        self.data.state = state
        self.log_state()
        return result

    def unpause_server(
            self, state: str = VMStates.ACTIVE, result: bool = True) -> bool:
        logging.info(f"Unpausing server: {self.data.uuid}")
        self.data.state = state
        self.log_state()
        return result

    def lock_server(
            self, state: str = VMStates.LOCKED, result: bool = True) -> bool:
        logging.info(f"Locking server: {self.data.uuid}")
        self.data.state = state
        self.log_state()
        return result

    def unlock_server(
            self, state: str = VMStates.ACTIVE, result: bool = True) -> bool:
        logging.info(f"Unlocking server: {self.data.uuid}")
        self.data.state = state
        self.log_state()
        return result

    def delete_server(
            self, state: str = VMStates.DELETING, result: bool = True) -> bool:
        logging.info(f"Deleting server: {self.data.uuid}")
        logging.info(f"Unmounting volume: {self.data.volume}")
        self.data.volume = None
        self.data.state = state
        self.log_state()
        return result

    def deleting_server(
            self, state: str = VMStates.DELETED, result: bool = True) -> bool:
        logging.info(f"Deleted server: {self.data.uuid}")
        self.data.state = state
        if self.data.state == VMStates.DELETED:
            self.data.ip_addr = '0.0.0.0'
            self.data.root_password = None
            self.data.metadata = {}
            self.data.image = None
            self.data.flavor = -1
        else:
            logging.error(f"Unable to delete server: {self.data.uuid}")

        self.log_state()
        return result

    # ===========================================
    #             VALIDATION METHODS
    # ===========================================
    def _validate_state(self, expected_states: list, **kwargs: dict) -> bool:

        result = self.data.state in expected_states

        # Overwrite data if specified
        if 'result' in kwargs:
            result = kwargs['result']

        logging.info(f"Checking if server '{self.data.uuid}' state is: {expected_states}: {result}")
        if not result:
            logging.error(f"Expected state: {expected_states}  Actual State: {self.data.state}")
        return result

    def does_server_exist(self, **kwargs: dict) -> bool:
        expected_states = [VMStates.DNE, VMStates.DELETED]
        return self._validate_state(expected_states, **kwargs)

    def is_server_active(self, **kwargs: dict) -> bool:
        expected_states = [VMStates.ACTIVE]
        return self._validate_state(expected_states, **kwargs)

    def is_server_in_error(self, **kwargs: dict) -> bool:
        expected_states = [VMStates.ERROR]
        return self._validate_state(expected_states, **kwargs)

    def is_server_paused(self, **kwargs: dict) -> bool:
        expected_states = [VMStates.PAUSED]
        return self._validate_state(expected_states, **kwargs)

    def is_server_locked(self, **kwargs: dict) -> bool:
        expected_states = [VMStates.LOCKED]
        return self._validate_state(expected_states, **kwargs)

    def is_server_deleting(self, **kwargs: dict) -> bool:
        expected_states = [VMStates.DELETING]
        return self._validate_state(expected_states, **kwargs)
