import time
from objects import RelRobotLocation, RobotLocation
from ..navigator import Navigator as nav
from ..util import *
import VisualGoalieStates as VisualStates
from .. import SweetMoves
from ..headTracker import HeadMoves
import GoalieConstants as constants
import math
import noggin_constants as nogginConstants

SAVING = False
DIVING = False

@superState('gameControllerResponder')
def gameInitial(player):
    if player.firstFrame():
        player.inKickingState = False
        player.returningFromPenalty = False
        player.brain.fallController.enabled = False
        player.stand()
        player.zeroHeads()
        player.isSaving = False
        player.lastStiffStatus = True
        player.justKicked = False

    # If stiffnesses were JUST turned on, then stand up.
    if player.lastStiffStatus == False and player.brain.interface.stiffStatus.on:
        player.stand()
    # Remember last stiffness.
    player.lastStiffStatus = player.brain.interface.stiffStatus.on

    return player.stay()

@superState('gameControllerResponder')
def gameReady(player):
    if player.firstFrame():
        player.inKickingState = False
        player.brain.fallController.enabled = True
        player.penaltyKicking = False
        player.stand()
        player.brain.tracker.lookToAngle(0)

    # Wait until the sensors are calibrated before moving.
    if(not player.brain.motion.calibrated):
        return player.stay()

    return player.stay()

@superState('gameControllerResponder')
def gameSet(player):
    if player.firstFrame():
        player.inKickingState = False
        player.brain.fallController.enabled = False
        player.returningFromPenalty = False
        player.penaltyKicking = False
        player.stand()
        player.brain.interface.motionRequest.reset_odometry = True
        player.brain.interface.motionRequest.timestamp = int(player.brain.time * 1000)
        player.inPosition = constants.CENTER_POSITION

        watchWithLineChecks.correctFacing = False
        watchWithLineChecks.numFixes = 0
        watchWithLineChecks.numTurns = 0
        watchWithLineChecks.looking = False

        # The ball will be right in front of us, for sure
        player.brain.tracker.lookToAngle(0)

    # Wait until the sensors are calibrated before moving.
    if (not player.brain.motion.calibrated):
        return player.stay()

    player.brain.resetGoalieLocalization()

    return player.stay()

@superState('gameControllerResponder')
def gamePlaying(player):
    if player.firstFrame():
        player.inKickingState = False
        player.brain.fallController.enabled = True
        player.penaltyKicking = False
        player.brain.nav.stand()

    # Wait until the sensors are calibrated before moving.
    if (not player.brain.motion.calibrated):
        return player.stay()

    # TODO penalty handling
    if player.penalized:
        player.penalized = False
        return player.goLater('afterPenalty')

    if player.lastDiffState == 'afterPenalty':
        return player.goLater('walkToGoal')

    if player.lastDiffState == 'fallen':
        # return player.goLater('watch')
        # #TODO fix this
        # player.justKicked = False
        if fallen.lastState == 'clearIt' and player.brain.ball.vis.on\
        and math.fabs(player.brain.ball.bearing_deg) < 25.0 and player.brain.ball.distance < 90:
            print "I was already going to clear it!"
            return player.goLater('clearIt')
        elif fallen.lastState == 'spinBack' or fallen.lastState == 'didIKickIt'\
        or fallen.lastState == 'kickBall' or fallen.lastState == 'repositionAfterWhiff':
            print("I was just in either spinback or didIKickIt, meaning I'm away frm the goalbox likely")
            return player.goLater('returnUsingLoc')
        elif fallen.lastState == 'returnUsingLoc':
            return player.goLater('returnUsingLoc')
        else:
            return player.goLater('watchWithLineChecks')

    #TODO before game/scrimmage change this to watch;
    # this is better for testing purposes!
    return player.goLater('watch')

@superState('gameControllerResponder')
def gamePenalized(player):
    if player.firstFrame():
        player.inKickingState = False
        player.brain.fallController.enabled = False
        player.stopWalking()
        player.penalizeHeads()
        player.penalized = True

    # TODO is this actually possible?
    if player.lastDiffState == '':
        # Just started up! Need to calibrate sensors
        player.brain.nav.stand()

    # Wait until the sensors are calibrated before moving.
    if (not player.brain.motion.calibrated):
        return player.stay()

    return player.stay()

@superState('gameControllerResponder')
def gameFinished(player):
    if player.firstFrame():
        player.inKickingState = False
        player.brain.fallController.enabled = False
        player.stopWalking()
        player.zeroHeads()
        if nogginConstants.V5_ROBOT:
            player.executeMove(SweetMoves.SIT_POS_V5)
        else:
            player.executeMove(SweetMoves.SIT_POS)
        return player.stay()

    if player.brain.nav.isStopped():
        player.gainsOff()

    return player.stay()

##### EXTRA METHODS

@superState('gameControllerResponder')
def fallen(player):
    fallen.lastState = player.lastDiffState
    player.inKickingState = False
    return player.stay()

fallen.lastState = 'watch'

@superState('gameControllerResponder')
def standStill(player):
    if player.firstFrame():
        player.brain.nav.stop()

    return player.stay()

@superState('gameControllerResponder')
def watchWithLineChecks(player):
    if player.firstFrame():
        watchWithLineChecks.counter = 0
        print ("My num turns:", watchWithLineChecks.numTurns)
        print ("My num fix:", watchWithLineChecks.numFixes)
        watchWithLineChecks.lines[:] = []
        player.homeDirections = []

        if player.lastDiffState == 'returnUsingLoc':
            print("I'm resetting my loc, I think I'm back!")
            player.brain.resetGoalieLocalization()

        if player.lastDiffState is not 'lineCheckReposition' and\
        player.lastDiffState is not 'moveBackwards':
            print "My facing is not necessarily correct! I'm checking"
            watchWithLineChecks.correctFacing = False
            watchWithLineChecks.numFixes = 0
            watchWithLineChecks.numTurns = 0
            watchWithLineChecks.looking = False

        elif watchWithLineChecks.numTurns > 0:
            print "I think I have corrected my facing now..."
            watchWithLineChecks.correctFacing = True

        player.brain.tracker.trackBall()
        player.brain.nav.stand()
        player.returningFromPenalty = False

        if watchWithLineChecks.shiftedPosition:
            watchWithLineChecks.shiftedPosition = False
            print "I just shifted my position, I'm moving to watch"
            return player.goLater('watch')

    if player.counter % 90 == 0:
        print("Horizon dist == ", player.brain.vision.horizon_dist)

    if (player.brain.ball.vis.frames_on > constants.BALL_ON_SAFE_THRESH \
        and player.brain.ball.distance > constants.BALL_SAFE_DISTANCE_THRESH \
        and not watchWithLineChecks.looking):
        watchWithLineChecks.looking = True
        player.brain.tracker.performBasicPan()

    if player.brain.tracker.isStopped():
        watchWithLineChecks.looking = False
        player.brain.tracker.trackBall()

    if watchWithLineChecks.counter > 400 or watchWithLineChecks.numFixes > 6:
        print "Counter was over 300, going to watch!"
        return player.goLater('watch')

    # Bc we won't be looking at landmarks if ball is on
    if not player.brain.ball.vis.on:
        watchWithLineChecks.counter += 1
    return Transition.getNextState(player, watchWithLineChecks)

watchWithLineChecks.lines = []
watchWithLineChecks.shiftedPosition = False
watchWithLineChecks.wentToClearIt = False

@superState('gameControllerResponder')
def lineCheckReposition(player):
    if player.firstFrame():
        player.brain.tracker.repeatBasicPan()
        dest = average(player.homeDirections)
        print "My home directions: "
        print dest
        if dest.relX == 0.0 and dest.relY == 0.0:
            print "I think this was a turn, I'm increasing my num turns!"
            watchWithLineChecks.numTurns += 1
        elif dest.relX == 5.0 and dest.relY == -30:
            player.inPosition = constants.RIGHT_POSITION
        elif dest.relX == 5.0 and dest.relY == 30:
            player.inPosition = constants.LEFT_POSITION
        else:
            print "This was a reposition, I think"
            watchWithLineChecks.numFixes += 1
        player.brain.nav.walkTo(dest, speed = nav.QUICK_SPEED)
        # player.brain.nav.goTo(dest, precision = (20.0, 20.0, 20))

    if player.counter > 300:
        return player.goLater('watchWithLineChecks')

    return Transition.getNextState(player, lineCheckReposition)

@superState('gameControllerResponder')
def spinToHorizon(player):
    if player.firstFrame():
        player.brain.tracker.lookToAngle(0)
        if player.brain.nav.isStopped():
            player.setWalk(0, 0, 15.0)

    if player.counter % 30 == 0:
        print("Horizon dist == ", player.brain.vision.horizon_dist)

    return Transition.getNextState(player, spinToHorizon)

@superState('gameControllerResponder')
def returnUsingLoc(player):
    if player.firstFrame():
        dest = RobotLocation(nogginConstants.FIELD_WHITE_LEFT_SIDELINE_X,
                        nogginConstants.MIDFIELD_Y,
                        0.0)
        player.brain.nav.goTo(dest,
                            speed = nav.BRISK_SPEED)
        print("I'm trying to return using loc!")
        player.brain.tracker.trackBall()

    if player.counter > 300:
        print "This is taking a suspiciously long time"
        return player.goLater('watchWithLineChecks')

    return Transition.getNextState(player, returnUsingLoc)

@superState('gameControllerResponder')
def spinBack(player):
    if player.firstFrame():
        spinBack.counter = 0
        player.brain.tracker.lookToAngle(0)
        if (math.fabs(-spinBack.toAngle) < 10.0 and -spinBack.toAngle > 0):
            angle = 20.0
        elif(math.fabs(-spinBack.toAngle) < 10.0 and -spinBack.toAngle < 0):
            angle = -20.0
        else:
            angle = -spinBack.toAngle

        VisualStates.returnToGoal.kickPose.relX += \
            player.brain.interface.odometry.x
        VisualStates.returnToGoal.kickPose.relY += \
            player.brain.interface.odometry.y
        VisualStates.returnToGoal.kickPose.relH += \
            player.brain.interface.odometry.h
        player.brain.nav.walkTo(RelRobotLocation(0,0,angle))
        print("My toangle:", spinBack.toAngle, "My angle:", angle)

    if player.counter % 30 == 0:
        print("Horizon dist == ", player.brain.vision.horizon_dist)
    if spinBack.counter > 150:
        return player.goLater('returnToGoal')

    return Transition.getNextState(player, spinBack)

spinBack.toAngle = 0.0

@superState('gameControllerResponder')
def recoverMyself(player):
    if player.firstFrame():
        print("In recover myself")
        player.brain.tracker.lookToAngle(0)
        player.brain.nav.setWalk(0,0,20)

    return Transition.getNextState(player, recoverMyself)

@superState('gameControllerResponder')
def watch(player):
    if player.firstFrame():
        player.brain.tracker.trackBall()
        player.brain.nav.stand()
        player.returningFromPenalty = False
        print ("I'm moving to watch! I think I'm in the right position")

    return Transition.getNextState(player, watch)

def average(locations):
    x = 0.0
    y = 0.0
    h = 0.0

    for item in locations:
        x += item.relX
        y += item.relY
        h += item.relH

    if len(locations) == 0:
        return RelRobotLocation(0.0, 0.0, 0.0)

    return RelRobotLocation(x/len(locations),
                            y/len(locations),
                            h/len(locations))

def correct(destination):
    if math.fabs(destination.relX) < constants.STOP_NAV_THRESH:
        destination.relX = 0.0
    if math.fabs(destination.relY) < constants.STOP_NAV_THRESH:
        destination.relY = 0.0
    if math.fabs(destination.relH) < constants.STOP_NAV_THRESH:
        destination.relH = 0.0

    destination.relX = destination.relX / constants.OVERZEALOUS_ODO
    destination.relY = destination.relY / constants.OVERZEALOUS_ODO
    destination.relH = destination.relH / constants.OVERZEALOUS_ODO

    return destination

@superState('gameControllerResponder')
def moveBackwards(player):
    if player.firstFrame():
        watchWithLineChecks.numFixes += 1
        # player.brain.tracker.lookToAngle(0)
        player.brain.tracker.trackBall
        player.brain.nav.walkTo(RelRobotLocation(-100.0, 0, 0))

    if player.counter > 100:
        print("Walking backwards too long... switch to a different state!")
        return player.goLater('findMyWayBackPtI')

    return Transition.getNextState(player, moveBackwards)

@superState('gameControllerResponder')
def kickBall(player):
    """
    Kick the ball
    """
    if player.firstFrame():
        player.justKicked = True
        # save odometry if this was your first kick
        if player.lastDiffState == 'clearIt' or player.lastDiffState == 'positionForGoalieKick':
            print "Here after clearit"
            h = math.degrees(player.brain.interface.odometry.h)
            VisualStates.returnToGoal.kickPose = \
                RelRobotLocation(player.brain.interface.odometry.x,
                                 player.brain.interface.odometry.y,
                                 h)
            print "Im saving my odo!"
            print ("MY H: ", h)
            print ("setting kickpose: ", player.brain.interface.odometry.x, player.brain.interface.odometry.y, player.brain.interface.odometry.h)
        #otherwise add to previously saved odo
        else:
            VisualStates.returnToGoal.kickPose.relX += \
                player.brain.interface.odometry.x
            VisualStates.returnToGoal.kickPose.relY += \
                player.brain.interface.odometry.y
            VisualStates.returnToGoal.kickPose.relH += \
                player.brain.interface.odometry.h

        player.brain.tracker.trackBall()
        player.brain.nav.stop()

    if player.counter is 20:
        player.executeMove(player.kick.sweetMove)

    if player.brain.ball.vis.frames_off > 15.0:
        print("I lost the ball! I'm returning to goal")
        return player.goLater('returnUsingLoc')

    if player.counter > 30 and player.brain.nav.isStopped():
        return player.goLater('didIKickIt')

    return player.stay()

@superState('gameControllerResponder')
def saveCenter(player):
    if player.firstFrame():
        player.brain.fallController.enabled = False
        player.brain.tracker.lookToAngle(0)
        if SAVING:
            player.executeMove(SweetMoves.GOALIE_SQUAT)
        # else:
        #     player.executeMove(SweetMoves.GOALIE_TEST_CENTER_SAVE)

    if player.counter > 80:
        if SAVING:
            player.executeMove(SweetMoves.GOALIE_SQUAT_STAND_UP)
            return player.goLater('upUpUP')
        else:
            return player.goLater('watch')

    return player.stay()

@superState('gameControllerResponder')
def upUpUP(player):
    if player.firstFrame():
        player.brain.fallController.enabled = True
        player.upDelay = 0

    if player.brain.nav.isStopped():
        #TODO testing change, put this back!!!
        return player.goLater('watch')
    return player.stay()

@superState('gameControllerResponder')
def saveRight(player):
    if player.firstFrame():
        player.brain.fallController.enabled = False
        player.brain.tracker.lookToAngle(0)
        if SAVING and DIVING:
            player.executeMove(SweetMoves.GOALIE_DIVE_RIGHT)
            player.brain.tracker.performHeadMove(HeadMoves.OFF_HEADS)
        # else:
        #     player.executeMove(SweetMoves.GOALIE_TEST_DIVE_RIGHT)

    if player.counter > 80:
        if SAVING and DIVING:
            player.executeMove(SweetMoves.GOALIE_ROLL_OUT_RIGHT)
            return player.goLater('rollOut')
        else:
            return player.goLater('watch')

    return player.stay()

@superState('gameControllerResponder')
def saveLeft(player):
    if player.firstFrame():
        player.brain.fallController.enabled = False
        player.brain.tracker.lookToAngle(0)
        if SAVING and DIVING:
            player.executeMove(SweetMoves.GOALIE_DIVE_LEFT)
            player.brain.tracker.performHeadMove(HeadMoves.OFF_HEADS)
        # else:
        #     player.executeMove(SweetMoves.GOALIE_TEST_DIVE_LEFT)

    if player.counter > 80:
        if SAVING and DIVING:
            player.executeMove(SweetMoves.GOALIE_ROLL_OUT_LEFT)
            return player.goLater('fallen')
        else:
            return player.goLater('watch')

    return player.stay()

@superState('gameControllerResponder')
def rollOut(player):
    if player.brain.nav.isStopped():
        player.brain.fallController.enabled = True
        return player.goLater('fallen')

    return player.stay()

# ############# PENALTY SHOOTOUT #############

@superState('gameControllerResponder')
def penaltyShotsGameSet(player):
    if player.firstFrame():
        player.inKickingState = False
        player.returningFromPenalty = False
        player.brain.fallController.enabled = False
        player.stand()
        player.brain.tracker.trackBall()
        player.side = constants.LEFT
        player.isSaving = False
        player.penaltyKicking = True

    return player.stay()

@superState('gameControllerResponder')
def penaltyShotsGamePlaying(player):
    if player.firstFrame():
        player.inKickingState = False
        player.returningFromPenalty = False
        player.brain.fallController.enabled = False
        player.stand()
        player.zeroHeads()
        player.isSaving = False
        player.lastStiffStatus = True

    return player.goLater('waitForPenaltySave')

@superState('gameControllerResponder')
def waitForPenaltySave(player):
    if player.firstFrame():
        player.brain.tracker.trackBall()
        player.brain.nav.stop()

    return Transition.getNextState(player, waitForPenaltySave)

@superState('gameControllerResponder')
def doDive(player):
    if player.firstFrame():
        player.brain.fallController.enabled = False
        player.brain.tracker.performHeadMove(HeadMoves.OFF_HEADS)
        if doDive.side == constants.RIGHT:
            player.executeMove(SweetMoves.GOALIE_DIVE_RIGHT)
        elif doDive.side == constants.LEFT:
            player.executeMove(SweetMoves.GOALIE_DIVE_LEFT)
        else:
            player.executeMove(SweetMoves.GOALIE_SQUAT)
    return player.stay()

@superState('gameControllerResponder')
def squat(player):
    if player.firstFrame():
        player.brain.fallController.enabled = False
        player.executeMove(SweetMoves.GOALIE_SQUAT)

    return player.stay()
