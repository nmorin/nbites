from ..headTracker.HeadMoves import (FIXED_PITCH_LEFT_SIDE_PAN,
                                      FIXED_PITCH_RIGHT_SIDE_PAN,
                                      FIXED_PITCH_PAN,
                                      FIXED_PITCH_SLOW_GOALIE_PAN)
#from vision import certainty
from ..navigator import Navigator as nav
from ..util import *
#import goalie
from GoalieConstants import RIGHT, LEFT, UNKNOWN, CENTER_TO_POST
import GoalieTransitions
from objects import RelRobotLocation, RelLocation, Location, RobotLocation
from noggin_constants import (LINE_CROSS_OFFSET, GOALBOX_DEPTH, GOALBOX_WIDTH,
                              FIELD_WHITE_LEFT_SIDELINE_X, CENTER_FIELD_Y,
                              HEADING_LEFT)

#from vision import cornerID as IDs
from math import fabs, degrees, radians, sin, cos
from ..kickDecider import kicks
import noggin_constants as Constants

@superState('gameControllerResponder')
def walkToGoal(player):
    """
    Has the goalie walk in the general direction of the goal.
    """
    if player.firstFrame():
        player.brain.tracker.repeatBasicPan()
        player.returningFromPenalty = False
        player.brain.nav.goTo(Location(FIELD_WHITE_LEFT_SIDELINE_X,
                                       CENTER_FIELD_Y))

    return Transition.getNextState(player, walkToGoal)

@superState('gameControllerResponder')
def spinAtGoal(player):
    if player.firstFrame():
        player.brain.nav.stop()
        spinAtGoal.counter = 0
        player.brain.tracker.lookToAngle(0.0)
    spinAtGoal.counter += 1
    if spinAtGoal.counter > 200:
            return player.goLater('watchWithCornerChecks')
    if player.brain.nav.isStopped():
        player.setWalk(0, 0, 20.0)

    return Transition.getNextState(player, spinAtGoal)

@superState('gameControllerResponder')
def backUpForDangerousBall(player):
    if player.firstFrame():
        player.brain.tracker.trackBall()
        player.brain.nav.goTo(RelRobotLocation(-10, 0, 0))

    return Transition.getNextState(player, backUpForDangerousBall)

# clearIt->kickBall->didIKickIt->returnToGoal
@superState('gameControllerResponder')
def clearIt(player):
    if player.firstFrame():
        player.brain.tracker.trackBall()
        if clearIt.dangerousSide == -1:
            if player.brain.ball.rel_y < 0.0:
                player.side = RIGHT
                player.kick = kicks.RIGHT_SHORT_STRAIGHT_KICK
            else:
                player.side = LEFT
                player.kick = kicks.LEFT_SHORT_STRAIGHT_KICK
        elif clearIt.dangerousSide == RIGHT:
            player.side = RIGHT
            player.kick = kicks.RIGHT_SIDE_KICK
        else:
            player.side = LEFT
            player.kick = kicks.LEFT_SIDE_KICK

        kickPose = player.kick.getPosition()
        clearIt.ballDest = RelRobotLocation(player.brain.ball.rel_x - kickPose[0],
                                            player.brain.ball.rel_y -
                                            kickPose[1],
                                            0.0)

        return Transition.getNextState(player, clearIt)

    if clearIt.odoDelay:
        clearIt.odoDelay = False
        player.brain.nav.goTo(clearIt.ballDest,
                              nav.CLOSE_ENOUGH,
                              nav.MEDIUM_SPEED,
                              adaptive = False)

    kickPose = player.kick.getPosition()

    clearIt.ballDest.relX = player.brain.ball.rel_x - kickPose[0]
    clearIt.ballDest.relY = player.brain.ball.rel_y - kickPose[1]

    return Transition.getNextState(player, clearIt)
clearIt.near = False
clearIt.count = 0

@superState('gameControllerResponder')
def didIKickIt(player):
    if player.firstFrame():
        player.brain.nav.stop()
    return Transition.getNextState(player, didIKickIt)

@superState('gameControllerResponder')
def spinToFaceBall(player):
    facingDest = RelRobotLocation(0.0, 0.0, 0.0)
    player.ballAngle = player.brain.ball.bearing_deg
    if player.brain.ball.bearing_deg < 0.0:
        player.side = RIGHT
        #facingDest.relH = -90
        facingDest.relH = player.brain.ball.bearing_deg
    else:
        player.side = LEFT
        #facingDest.relH = 90
        facingDest.relH = player.brain.ball.bearing_deg
    player.brain.nav.goTo(facingDest,
                          nav.CLOSE_ENOUGH,
                          nav.CAREFUL_SPEED)
    spinToFaceBall.count += 1

    player.brain.interface.motionRequest.reset_odometry = True
    player.brain.interface.motionRequest.timestamp = int(player.brain.time * 1000)
    clearIt.odoDelay = True



    if player.counter > 180:
        return player.goLater('spinAtGoal')

    return Transition.getNextState(player, spinToFaceBall)
spinToFaceBall.count = 0

@superState('gameControllerResponder')
def waitToFaceField(player):
    if player.firstFrame():
        player.brain.tracker.lookToAngle(0)

    return Transition.getNextState(player, waitToFaceField)

@superState('gameControllerResponder')
def returnToGoal(player):
    if player.firstFrame():
        player.brain.tracker.trackBall()
        player.brain.nav.stand()
        player.returningFromPenalty = False
        returnToGoal.c = 0

        player.brain.interface.motionRequest.reset_odometry = True
        player.brain.interface.motionRequest.timestamp = int(player.brain.time * 1000)

        print "Odometry y = " + str(returnToGoal.kickPose.relY)
        print "Odometry x = " + str(returnToGoal.kickPose.relX)
        print "Odometry H = " + str(returnToGoal.kickPose.relH)

    returnToGoal.c += 1
    if returnToGoal.c < 10:
        returnToGoal.dest = RelRobotLocation(-returnToGoal.kickPose.relX,
                                            -returnToGoal.kickPose.relY,
                                            -returnToGoal.kickPose.relH)
        player.brain.nav.destinationWalkTo(returnToGoal.dest)

    if player.brain.interface.odometry.x + fabs(returnToGoal.kickPose.relX) < 10.0:
        print "WAS TRUE"
        player.brain.nav.stand()
        return player.goLater('watch')

    return player.stay()

@superState('gameControllerResponder')
def repositionAfterWhiff(player):
    if player.firstFrame():
        # reset odometry
        player.brain.interface.motionRequest.reset_odometry = True
        player.brain.interface.motionRequest.timestamp = int(player.brain.time * 1000)

        if player.kick in [kicks.RIGHT_SIDE_KICK, kicks.LEFT_SIDE_KICK]:
            pass
        elif player.brain.ball.rel_y < 0.0:
            player.kick = kicks.RIGHT_SHORT_STRAIGHT_KICK
        else:
            player.kick = kicks.LEFT_SHORT_STRAIGHT_KICK

        kickPose = player.kick.getPosition()
        repositionAfterWhiff.ballDest = RelRobotLocation(player.brain.ball.rel_x -
                                                         kickPose[0],
                                                         player.brain.ball.rel_y -
                                                         kickPose[1],
                                                         0.0)
        player.brain.nav.goTo(repositionAfterWhiff.ballDest,
                              nav.CLOSE_ENOUGH,
                              nav.GRADUAL_SPEED)

    # if it took more than 5 seconds, forget it
    if player.counter > 150:
        returnToGoal.kickPose.relX += player.brain.interface.odometry.x
        returnToGoal.kickPose.relY += player.brain.interface.odometry.y
        returnToGoal.kickPose.relH += player.brain.interface.odometry.h

        return player.goLater('returnToGoal')

    kickPose = player.kick.getPosition()
    repositionAfterWhiff.ballDest.relX = (player.brain.ball.rel_x -
                                          kickPose[0])
    repositionAfterWhiff.ballDest.relY = (player.brain.ball.rel_y -
                                          kickPose[1])

    return Transition.getNextState(player, repositionAfterWhiff)


#############################################################################################

@superState('gameControllerResponder')
def changePost(player):
    rgp = player.brain.interface.visionField.goal_post_r.visual_detection
    lgp = player.brain.interface.visionField.goal_post_l.visual_detection
    if lgp.distance != 0.0 and lgp.distance > rgp.distance:
        post = lgp
        tpost = LEFT
    else:
        post = rgp
        tpost = RIGHT
    y = 0.0
    x = post.distance
    if player.firstFrame():
        changePost.counter = 0
        player.brain.tracker.trackPost(tpost)
        changePost.dest = RelRobotLocation(x, y, 0.0)
        player.brain.nav.goTo(changePost.dest, nav.CLOSE_ENOUGH, nav.MEDIUM_SPEED)
    changePost.counter += 1

    if post.distance != 0.0:
        changePost.dest.relX = post.distance
        changePost.dest.relH = post.bearing_deg
    changePost.dest.relY = y
    return Transition.getNextState(player, changePost)

@superState('gameControllerResponder')
def approachPost(player):
    y = 0.0
    rgp = player.brain.interface.visionField.goal_post_r.visual_detection
    lgp = player.brain.interface.visionField.goal_post_l.visual_detection
    if lgp.bearing != 0.0 and lgp.distance > rgp.distance:
        approachPost.post = LEFT
        approachPost.targetpost = lgp
    else:
        approachPost.post = RIGHT
        approachPost.targetpost = rgp
        if approachPost.targetpost.distance < 120:
             y = -20.0

    if player.firstFrame():
        player.stand()
        approachPost.counter = 0
        player.zeroHeads()
        approachPost.dest = RelRobotLocation(approachPost.targetpost.distance, y,
                                approachPost.targetpost.bearing_deg)
        if player.post % 2 == 0:
            speed = nav.MEDIUM_SPEED
        else:
            speed = nav.BRISK_SPEED
        player.brain.nav.goTo(approachPost.dest, nav.CLOSE_ENOUGH, speed)

    if approachPost.targetpost.distance != 0.0:
        approachPost.dest.relX = approachPost.targetpost.distance
        approachPost.dest.relH = approachPost.targetpost.bearing_deg
    approachPost.dest.relY = y
    approachPost.counter += 1

    return Transition.getNextState(player, approachPost)
approachPost.lastPostDist = -1.0