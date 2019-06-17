#!/usr/bin/env python


from transitions import Machine, MachineError

import flowtester.logging.logger as logger

class ServerState(Machine):

    DNE = 'DNE'
    ACTIVE = 'active'
    DELETING = 'deleting'
    DONE = 'finished'
    BUILDING = 'building'
    ERROR = 'error'
    REBUILD = 'rebuild'
    REBOOTING = 'rebooting'
    PAUSED = 'paused'
    LOCKED = 'locked'

    CREATE = 'create'
    DELETE = 'delete'
    FAIL = 'fail'
    SUCCESS = 'success'
    PAUSE = 'pause'
    UNPAUSE = 'unpause'

    STATES = [DNE, BUILDING, ACTIVE, DELETING, ERROR, PAUSED]
    TRIGGERS = [CREATE, FAIL, SUCCESS, DELETE]

    DEFAULT_STATE = DNE

    BORDER_LEN = 40

    def __init__(self, name):
        self.name = name
        Machine.__init__(self, states=ServerState.STATES, initial=self.DEFAULT_STATE)
        self.define_state_paths()
        self.path = [self.DNE]

    def define_state_paths(self):
        self.add_transition(trigger=self.CREATE, source=self.DNE, dest=self.BUILDING,
                            before='entry_into_state', after='exit_state')

        self.add_transition(trigger=self.FAIL, source=self.BUILDING, dest=self.ERROR,
                            before='entry_into_state', after='exit_state')

        self.add_transition(trigger=self.SUCCESS, source=self.BUILDING, dest=self.ACTIVE,
                            before='entry_into_state', after='exit_state')

        self.add_transition(trigger=self.DELETE, source=self.ACTIVE, dest=self.DELETING,
                            before='entry_into_state', after='exit_state')

        self.add_transition(trigger=self.PAUSE, source=self.ACTIVE, dest=self.PAUSED,
                            before='entry_into_state', after='exit_state')

        self.add_transition(trigger=self.UNPAUSE, source=self.PAUSED, dest=self.ACTIVE,
                            before='entry_into_state', after='exit_state')

        self.add_transition(trigger=self.SUCCESS, source=self.DELETING, dest=self.DNE,
                            before='entry_into_state', after='exit_state')

        self.add_transition(trigger=self.FAIL, source=self.DELETING, dest=self.ERROR,
                            before='entry_into_state', after='exit_state')

    def entry_into_state(self):
        logging.info(f"{'-' * self.BORDER_LEN}\nCurrent State: {self.state.upper()}")

    def exit_state(self):
        logging.info(f"New State: {self.state.upper()}\n{'*' * self.BORDER_LEN}")
        self.path.append(self.state.upper())


if __name__ == '__main__':
    machine = ServerState(name='VM')
    project = logger.Logger.determine_project()
    logging = logger.Logger(project=project, default_level=logger.Logger.STR_TO_VAL['info'])
    logging.info(f"INITIAL STATE: {machine.state}")
    machine_transitions = [machine.CREATE, machine.SUCCESS, machine.PAUSE, machine.DELETE, machine.UNPAUSE,
                           machine.DELETE, machine.SUCCESS]

    for trans in machine_transitions:
        try:
            logging.info(f"Requested Transition: {trans.upper()}")
            getattr(machine, trans)()

        except MachineError as exc:
            logging.error(f"\nERROR: {exc}")
            logging.error(f"\tRemaining in '{machine.state.upper()}' state.\n")
            machine.path.append(f"ERR: {machine.state.upper()}")

        except AttributeError as exc:
            raise exc

    logging.info(f"\nFINAL STATE: {machine.state}")
    traversed = [f"{state} --({trans})--> " for state, trans in zip(machine.path, machine_transitions)]
    logging.info(f"\nPATH:  {''.join(traversed)}\n")
