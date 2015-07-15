from . import SoccerFSA
from . import FallControllerStates
from . import RoleSwitchingStates
from . import CommMonitorStates
from . import GameControllerStates
from . import CornerStates
from ..util import Transition

import noggin_constants as NogginConstants

class SoccerPlayer(SoccerFSA.SoccerFSA):
    def __init__(self, brain):
        ### ADD STATES AND NAME FSA ###
        SoccerFSA.SoccerFSA.__init__(self,brain)
        self.addStates(FallControllerStates)
        self.addStates(RoleSwitchingStates)
        self.addStates(CommMonitorStates)
        self.addStates(GameControllerStates)
        self.addStates(CornerStates)
        self.setName('pCorner')
        self.currentState = 'fallController' # initial state

        self.role = brain.playerNumber
        self.brain.fallController.enabled = True
        self.isCornerKicker = False
