===============
Overview
===============

The flowtester tool takes a different approach to testing. Rather than focus on a product's individual features or bug fixes, the approach focuses on determining the flow of data and user operations through the system using a tool called a finite state machine (FSM). State machines are modeling technique that identifies each "state" product can be in and listing the paths or transitions from the given state to a different state.

Small discussion on state machines: https://www.smashingmagazine.com/2018/01/rise-state-machines/

The flow testing tool uses three different input models to determine how to test:

state_machine_definition: This defines the state machine and the transitions between states.
object_model: This is an automated representation of the product under test and contains the routines used to interaction with the actual product under test. This model is used as a source of truth to compare to the system under test.
path_definition: This provides the data and path to traverse through the state machine. It is comprised of an ordered list of triggers (or transitions), data required to pass to the routine to cause a state transition on the system under test, and the expected results for the validations run after each state change.



