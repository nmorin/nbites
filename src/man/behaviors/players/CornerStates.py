"""
Game controller states for pCorner, player for corner kick technical challenge
"""

import noggin_constants as nogginConstants
import ChaseBallTransitions
import ChaseBallStates
from math import fabs
from ..util import *
from .. import SweetMoves
from objects import RobotLocation

# Corner constants
kickerStartPosition = RobotLocation(nogginConstants.OPP_GOALBOX_LEFT_X,
									nogginConstants.FIELD_WHITE_TOP_SIDELINE_Y,
									nogginConstants.OPP_GOAL_HEADING)

receiverStartPosition = RobotLocation(nogginConstants.LANDMARK_OPP_FIELD_CROSS[0] - 50.0,
									nogginConstants.LANDMARK_OPP_FIELD_CROSS[1],
									nogginConstants.OPP_GOAL_HEADING)

# Figure out which player you are and reset loc to that spot
# Player one: approach and kick the ball
# Player two: wait until ball moves, then try to score

@superState('gameControllerResponder')
def gameInitial(player):
    """
    Ensure we are sitting down and head is snapped forward.
    """
    if player.firstFrame():
        player.inKickingState = False
        player.brain.fallController.enabled = False
        player.gainsOn()
        player.stand()
        player.zeroHeads()
        player.brain.resetInitialLocalization()
        player.lastStiffStatus = True
        #Reset role to player number
        player.role = player.brain.playerNumber
        roleConstants.setRoleConstants(player, player.role)

    # If stiffnesses were JUST turned on, then stand up.
    if player.lastStiffStatus == False and player.brain.interface.stiffStatus.on:
        player.stand()
    # Remember last stiffness.
    player.lastStiffStatus = player.brain.interface.stiffStatus.on

    return player.stay()

@superState('gameControllerResponder')
def gameReady(player):
    """
    Do nothing here!
    """
    if player.firstFrame():
        player.inKickingState = False
        player.brain.fallController.enabled = True
        player.brain.nav.stand()
    return player.stay()

@superState('gameControllerResponder')
def gameSet(player):
    """
    Look for ball to determine role
    """
    if player.firstFrame():
        player.inKickingState = False
        player.brain.fallController.enabled = True
        player.gainsOn()
        player.stand()
        player.brain.nav.stand()
        player.brain.tracker.performWidePan()

    elif player.brain.tracker.isStopped():
        player.brain.tracker.trackBall()

    if player.brain.ball.vis.on:
    	determineIfKicking(player)

    # Wait until the sensors are calibrated before moving.
    if not player.brain.motion.calibrated:
        return player.stay()

    return player.stay()

@superState('gameControllerResponder')
def gamePlaying(player):
    if player.firstFrame():
    	if player.isCornerKicker:
    		player.brain.resetLocTo(kickerStartPosition.x,
    								kickerStartPosition.y,
    								kickerStartPosition.h)
            return player.goLater('positionForCornerKick')
    	else:
    		player.brain.resetLocTo(receiverStartPosition.x,
    								receiverStartPosition.y,
    								receiverStartPosition.h)
    		return player.goLater('waitForKick')

   	return player.stay()

@superState('gameControllerResponder')
def gameFinished(player):
    """
    Ensure we are sitting down and head is snapped forward.
    In the future, we may wish to make the head move a bit slower here
    """
    if player.firstFrame():
        player.inKickingState = False
        player.brain.fallController.enabled = False
        player.stopWalking()
        player.zeroHeads()
        if nogginConstants.V5_ROBOT:
            player.executeMove(SweetMoves.SIT_POS_V5)
        else:
            player.executeMove(SweetMoves.SIT_POS)

    if player.brain.nav.isStopped():
        player.gainsOff()

    return player.stay()

@superState('gameControllerResponder')
def gamePenalized(player):
    if player.firstFrame():
        player.inKickingState = False
        player.brain.fallController.enabled = False
        player.gainsOn()
        player.stand()
        player.penalizeHeads()

    return player.stay()

@superState('gameControllerResponder')
def waitForKick(player):
	if player.firstFrame():
        waitForKick.ballRelX = player.brain.ball.rel_x
        waitForKick.ballRelY = player.brain.ball.rel_y

    if (fabs(player.brain.ball.rel_x - waitForKick.ballRelX) > 15.0 or
        fabs(player.brain.ball.rel_y - waitForKick.ballRelY) > 15.0):
        return player.goNow('ChaseBallStates.approachBall')

    return player.stay()

@superState('gameControllerResponder')
def positionForCornerKick:
    if player.firstFrame():
        location = RelRobotLocation(ball.rel_x + 20, ball.rel_y + 20, 0)
        player.brain.nav.destinationWalkTo(location, Navigator.MEDIUM_SPEED)

        # Positions the robot for a corner kick to the goal cross
        player.brain.nav.chaseBall(Navigator.FAST_SPEED, fast = True)
        player.brain.tracker.repeatFastNarrowPan()
    else:
        location = RelRobotLocation(ball.rel_x + 20, ball.rel_y + 20, 0)
        player.brain.nav.updateDestinationWalkDest(location)


    if (location.relX**2 + location.relY**2)**.5 < 15:
        print "X: ", player.brain.ball.rel_x
        print "Y: ", player.brain.ball.rel_y
        player.brain.nav.stand()
        # prepareForPenaltyKick.chase = True
        return player.goNow('CornerKickSpin')

def determineIfKicking(player):
	bearing = player.brain.ball.bearing_deg
	distance = player.brain.ball.distance

	# If ball directly in front of us, we are probably supposed to do the corner kick!
	if fabs(bearing) < 15.0 and distance < 100.0:
		player.isCornerKicker = True
	else:
		player.isCornerKicker = False
