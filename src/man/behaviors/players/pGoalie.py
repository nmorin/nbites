from . import SoccerFSA
from . import FallControllerStates
from . import RoleSwitchingStates
from . import CommMonitorStates
from . import GameControllerStates
from . import GoalieStates
from . import VisualGoalieStates
from . import GoalieTransitions
from . import PenaltyStates
from ..util import Transition

import noggin_constants as NogginConstants
from GoalieConstants import RIGHT, LEFT, CENTER_POSITION

from objects import Location, RelRobotLocation

class SoccerPlayer(SoccerFSA.SoccerFSA):
    def __init__(self, brain):
        ### ADD STATES AND NAME FSA ###
        SoccerFSA.SoccerFSA.__init__(self,brain)
        self.addStates(FallControllerStates)
        self.addStates(RoleSwitchingStates)
        self.addStates(CommMonitorStates)
        self.addStates(GameControllerStates)
        self.addStates(GoalieStates)
        self.addStates(VisualGoalieStates)
        self.addStates(PenaltyStates)
        self.setName('pGoalie')
        self.currentState = 'fallController' # initial state

        ### THE STATE OF THE PLAYER ###
        self.role = 1
        self.squatTime = 0
        self.frameCounter = 0
        self.penaltyKicking = False
        self.aggressive = False
        self.returningFromPenalty = False
        self.side = RIGHT
        self.homeDirections = []
        self.brain.fallController.enabled = True
        self.roleSwitching = False
        self.penalized = False
        self.commMode = -1
        self.justKicked = False

        self.inPosition = CENTER_POSITION
        self.inGoalbox = True

        ### ALL TRANSITIONS ARE DEFINED HERE ############
        ### Their conditions are in GoalieTransitions ###
        VisualGoalieStates.walkToGoal.transitions = {

            Transition.CountTransition(GoalieTransitions.reachedMyDestination,
                                       Transition.ALL_OF_THE_TIME,
                                       Transition.INSTANT)
            : GoalieStates.watchWithLineChecks

            }

        VisualGoalieStates.waitToFaceField.transitions = {
            Transition.CountTransition(GoalieTransitions.notTurnedAround,
                                       Transition.MOST_OF_THE_TIME,
                                       Transition.HIGH_PRECISION)
            : PenaltyStates.afterPenalty
            }

        GoalieStates.watch.transitions = {
            Transition.CountTransition(GoalieTransitions.getLines,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.watchWithLineChecks,

            Transition.CountTransition(GoalieTransitions.shouldSquat,
                                       Transition.OCCASIONALLY,
                                       Transition.LOW_PRECISION)
            : GoalieStates.saveCenter,

            # No dives -- TESTING DIVES
            Transition.CountTransition(GoalieTransitions.shouldDiveLeft,
                                       Transition.OCCASIONALLY,
                                       Transition.LOW_PRECISION)
            : GoalieStates.saveLeft,

            Transition.CountTransition(GoalieTransitions.shouldDiveRight,
                                       Transition.OCCASIONALLY,
                                       Transition.LOW_PRECISION)
            : GoalieStates.saveRight,

            Transition.CountTransition(GoalieTransitions.shouldClearBall,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.OK_PRECISION + 5)
            : VisualGoalieStates.clearBall,


            # Transition.CountTransition(GoalieTransitions.noTopLine,
            #                            Transition.MOST_OF_THE_TIME,
            #                            40)
            # : GoalieStates.moveBackwards,

            # Transition.CountTransition(GoalieTransitions.shouldPositionLeft,
            #                            Transition.SOME_OF_THE_TIME,
            #                            Transition.OK_PRECISION + 5)
            # : GoalieStates.lineCheckReposition,

            # Transition.CountTransition(GoalieTransitions.shouldPositionRight,
            #                            Transition.SOME_OF_THE_TIME,
            #                            Transition.OK_PRECISION + 5)
            # : GoalieStates.lineCheckReposition,

            # Transition.CountTransition(GoalieTransitions.shouldClearDangerousBall,
            #                            Transition.SOME_OF_THE_TIME,
            #                            Transition.OK_PRECISION)
            # : VisualGoalieStates.backUpForDangerousBall
            }

        GoalieStates.moveBackwards.transitions = {
            Transition.CountTransition(GoalieTransitions.shouldStopGoingBack,
                                       Transition.OCCASIONALLY,
                                       Transition.LOW_PRECISION)
            : GoalieStates.watchWithLineChecks,

            Transition.CountTransition(GoalieTransitions.doneWalking,
                                       Transition.ALL_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.watchWithLineChecks

            # Transition.CountTransition(GoalieTransitions.shouldClearBall,
            #                            Transition.SOME_OF_THE_TIME,
            #                            Transition.OK_PRECISION + 5)
            # : VisualGoalieStates.spinToFaceBall,

            # Transition.CountTransition(GoalieTransitions.shouldClearDangerousBall,
            #                            Transition.SOME_OF_THE_TIME,
            #                            Transition.OK_PRECISION)
            # : VisualGoalieStates.backUpForDangerousBall
            }

        VisualGoalieStates.spinToFaceBall.transitions = {
            Transition.CountTransition(GoalieTransitions.facingBall,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : VisualGoalieStates.clearIt
            }

        VisualGoalieStates.clearBall.transitions = {
            Transition.CountTransition(GoalieTransitions.ballLostStopChasing,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.returnUsingLoc,

            Transition.CountTransition(GoalieTransitions.ballMovedStopChasing,
                                       Transition.MOST_OF_THE_TIME,
                                       Transition.OK_PRECISION)
            : GoalieStates.returnUsingLoc,

            Transition.CountTransition(GoalieTransitions.walkedTooFar,
                                       Transition.MOST_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.returnUsingLoc
            }

        VisualGoalieStates.positionForGoalieKick.transitions = {
            Transition.CountTransition(GoalieTransitions.ballReadyToKick,
                                       Transition.OCCASIONALLY,
                                       Transition.LOW_PRECISION)
            : GoalieStates.kickBall,

            Transition.CountTransition(GoalieTransitions.ballLostStopChasing,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.returnUsingLoc,

            Transition.CountTransition(GoalieTransitions.ballMovedStopChasing,
                                       Transition.MOST_OF_THE_TIME,
                                       Transition.OK_PRECISION)
            : GoalieStates.returnUsingLoc,

            Transition.CountTransition(GoalieTransitions.walkedTooFar,
                                       Transition.MOST_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.returnUsingLoc
            }

        VisualGoalieStates.backUpForDangerousBall.transitions = {
            Transition.CountTransition(GoalieTransitions.ballSafe,
                                       Transition.OCCASIONALLY,
                                       Transition.LOW_PRECISION)
            : VisualGoalieStates.spinToFaceBall,

            # Transition.CountTransition(GoalieTransitions.ballLostStopChasing,
            #                            Transition.ALL_OF_THE_TIME,
            #                            90)
            # : GoalieStates.watchWithCornerChecks,

            # Transition.CountTransition(GoalieTransitions.ballMovedStopChasing,
            #                            Transition.MOST_OF_THE_TIME,
            #                            Transition.OK_PRECISION)
            # : GoalieStates.watchWithCornerChecks
            }

        VisualGoalieStates.clearIt.transitions = {
            Transition.CountTransition(GoalieTransitions.shouldSquat,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.saveCenter,

            Transition.CountTransition(GoalieTransitions.reachedMyDestination,
                                       Transition.ALL_OF_THE_TIME,
                                       Transition.INSTANT)
            : GoalieStates.kickBall,

            Transition.CountTransition(GoalieTransitions.ballLostStopChasing,
                                       Transition.MOST_OF_THE_TIME,
                                       Transition.OK_PRECISION)
            : GoalieStates.returnUsingLoc,

            Transition.CountTransition(GoalieTransitions.ballMovedStopChasing,
                                       Transition.MOST_OF_THE_TIME,
                                       Transition.OK_PRECISION)
            : GoalieStates.returnUsingLoc,

            Transition.CountTransition(GoalieTransitions.walkedTooFar,
                                       Transition.MOST_OF_THE_TIME,
                                       Transition.OK_PRECISION)
            : GoalieStates.returnUsingLoc
            }

        VisualGoalieStates.repositionAfterWhiff.transitions = {
            Transition.CountTransition(GoalieTransitions.reachedMyDestination,
                                       Transition.ALL_OF_THE_TIME,
                                       Transition.INSTANT)
            : GoalieStates.kickBall
            }

            #VISION CHANGE
        VisualGoalieStates.returnToGoal.transitions = {
            Transition.CountTransition(GoalieTransitions.doneWalking,
                                       Transition.ALL_OF_THE_TIME,
                                       Transition.OK_PRECISION)
            : GoalieStates.watchWithLineChecks

            # Transition.CountTransition(GoalieTransitions.shouldStopGoingBack,
            #                            Transition.SOME_OF_THE_TIME,
            #                            Transition.OK_PRECISION)
            # : GoalieStates.watchWithLineChecks
            }

        VisualGoalieStates.didIKickIt.transitions = {
            Transition.CountTransition(GoalieTransitions.whiffed,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.OK_PRECISION)
            : VisualGoalieStates.repositionAfterWhiff,

            Transition.CountTransition(GoalieTransitions.successfulKick,
                                       Transition.ALL_OF_THE_TIME,
                                       Transition.INSTANT)
            : GoalieStates.returnUsingLoc,

            # Transition.CountTransition(GoalieTransitions.successfulKickAndTurn,
            #                            Transition.MOST_OF_THE_TIME,
            #                            Transition.LOW_PRECISION)
            # : GoalieStates.spinBack#lineCheckReposition
            }

        GoalieStates.watchWithLineChecks.transitions = {
            Transition.CountTransition(GoalieTransitions.getLines,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.watch,

            Transition.CountTransition(GoalieTransitions.shouldSquat,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.saveCenter,

            # No dives -- TESTING DIVES
            Transition.CountTransition(GoalieTransitions.shouldDiveLeft,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.saveLeft,

            Transition.CountTransition(GoalieTransitions.shouldDiveRight,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.saveRight,

            Transition.CountTransition(GoalieTransitions.shouldClearBall,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.OK_PRECISION + 5)
            : VisualGoalieStates.spinToFaceBall,

            # Transition.CountTransition(GoalieTransitions.shouldPositionLeft,
            #                            Transition.SOME_OF_THE_TIME,
            #                            Transition.OK_PRECISION + 5)
            # : GoalieStates.lineCheckReposition,

            # Transition.CountTransition(GoalieTransitions.shouldPositionRight,
            #                            Transition.SOME_OF_THE_TIME,
            #                            Transition.OK_PRECISION + 5)
            # : GoalieStates.lineCheckReposition,

            Transition.CountTransition(GoalieTransitions.shouldGoForward,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.lineCheckReposition,

            Transition.CountTransition(GoalieTransitions.shouldBackUp,
                                       Transition.ALL_OF_THE_TIME,
                                       45)
            : GoalieStates.moveBackwards,

            # Transition.CountTransition(GoalieTransitions.facingSideways,
            #                            Transition.SOME_OF_THE_TIME,
            #                            Transition.LOW_PRECISION)
            # : GoalieStates.lineCheckReposition,

            Transition.CountTransition(GoalieTransitions.frontLineCheckShouldReposition,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.lineCheckReposition,

            Transition.CountTransition(GoalieTransitions.facingBackward,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.OK_PRECISION)
            : GoalieStates.lineCheckReposition,

            Transition.CountTransition(GoalieTransitions.sideLineCheckShouldReposition,
                                       Transition.OCCASIONALLY,
                                       Transition.LOW_PRECISION)
            : GoalieStates.lineCheckReposition,

            Transition.CountTransition(GoalieTransitions.shouldTurn,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.OK_PRECISION)
            : GoalieStates.lineCheckReposition,

            Transition.CountTransition(GoalieTransitions.facingASideline,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.lineCheckReposition,

            Transition.CountTransition(GoalieTransitions.seeGoalbox,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.lineCheckReposition,

            # Transition.CountTransition(GoalieTransitions.noTopLine,
            #                            Transition.SOME_OF_THE_TIME,
            #                            Transition.OK_PRECISION)
            # : GoalieStates.moveBackwards,

            # Transition.CountTransition(GoalieTransitions.shouldClearDangerousBall,
            #                            Transition.SOME_OF_THE_TIME,
            #                            Transition.OK_PRECISION)
            # : VisualGoalieStates.backUpForDangerousBall,


        }

        GoalieStates.lineCheckReposition.transitions = {
            Transition.CountTransition(GoalieTransitions.doneWalking,
                                       Transition.ALL_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.watchWithLineChecks,

            Transition.CountTransition(GoalieTransitions.reachedMyDestination,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.watchWithLineChecks,

            Transition.CountTransition(GoalieTransitions.shouldSquat,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.saveCenter,

            # No dives -- TESTING DIVES
            Transition.CountTransition(GoalieTransitions.shouldDiveLeft,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.saveLeft,

            Transition.CountTransition(GoalieTransitions.shouldDiveRight,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.saveRight,

            Transition.CountTransition(GoalieTransitions.shouldClearBall,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.OK_PRECISION + 5)
            : VisualGoalieStates.spinToFaceBall
            }

        VisualGoalieStates.findMyWayBackPtI.transitions = {
            Transition.CountTransition(GoalieTransitions.shouldStopTurning,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : VisualGoalieStates.findMyWayBackPtII,

            Transition.CountTransition(GoalieTransitions.seeGoalbox,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.lineCheckReposition
            }

        VisualGoalieStates.findMyWayBackPtII.transitions = {
            Transition.CountTransition(GoalieTransitions.doneWalking,
                                       Transition.ALL_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.lineCheckReposition
            }

        GoalieStates.waitForPenaltySave.transitions = {
            Transition.CountTransition(GoalieTransitions.saveNow,
                                       Transition.MOST_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.doDive,
            }

        GoalieStates.spinToHorizon.transitions = {
            Transition.CountTransition(GoalieTransitions.facingFront,
                                       Transition.OCCASIONALLY,
                                       Transition.LOW_PRECISION)
            : GoalieStates.moveBackwards
            }

        GoalieStates.spinBack.transitions = {
            Transition.CountTransition(GoalieTransitions.doneWalking,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.moveBackwards #returnToGoal
            }

        GoalieStates.recoverMyself.transitions = {
            Transition.CountTransition(GoalieTransitions.shouldTurn,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.lineCheckReposition,

            Transition.CountTransition(GoalieTransitions.shouldBackUp,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.moveBackwards,

            Transition.CountTransition(GoalieTransitions.facingASideline,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.moveBackwards,

            }

        GoalieStates.returnUsingLoc.transitions = {
            Transition.CountTransition(GoalieTransitions.doneWalking,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.watchWithLineChecks,

            Transition.CountTransition(GoalieTransitions.reachedMyDestination,
                                       Transition.SOME_OF_THE_TIME,
                                       Transition.LOW_PRECISION)
            : GoalieStates.watchWithLineChecks
            # Transition.CountTransition(GoalieTransitions.shouldTurn,
            #                            Transition.SOME_OF_THE_TIME,
            #                            Transition.LOW_PRECISION)
            # : GoalieStates.lineCheckReposition,

            # Transition.CountTransition(GoalieTransitions.shouldBackUp,
            #                            Transition.SOME_OF_THE_TIME,
            #                            Transition.LOW_PRECISION)
            # : GoalieStates.moveBackwards,

            # Transition.CountTransition(GoalieTransitions.facingASideline,
            #                            Transition.SOME_OF_THE_TIME,
            #                            Transition.LOW_PRECISION)
            # : GoalieStates.moveBackwards,

            }