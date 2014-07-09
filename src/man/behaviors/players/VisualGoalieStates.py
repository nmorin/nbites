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
        #spinAtGoal.home = RelRobotLocation(0, 0, 0)
        ## Decide which way to rotate based on the way we came from
        #if player.side == RIGHT:
        #    spinAtGoal.home.relH = -90
        #else:
        #    spinAtGoal.home.relH = 90
        #player.brain.nav.goTo(spinAtGoal.home,
        #                      nav.CLOSE_ENOUGH, nav.CAREFUL_SPEED)

        player.brain.tracker.lookToAngle(0.0)
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
        clearIt.ballDest = RelRobotLocation(player.brain.ball.rel_x -
                                            kickPose[0],
                                            player.brain.ball.rel_y -
                                            kickPose[1],
                                            0.0)

        # reset odometry
        player.brain.interface.motionRequest.reset_odometry = True
        player.brain.interface.motionRequest.timestamp = int(player.brain.time * 1000)
        clearIt.odoDelay = True
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

    #print "Kick = " + str(kickPose)
    #print "Ball relx = " + str(player.brain.ball.rel_x)
    #print "Ball rely = " + str(player.brain.ball.rel_y)
    #print "relX = " + str(clearIt.ballDest.relX)
    #print "relY = " + str(clearIt.ballDest.relY)

    return Transition.getNextState(player, clearIt)

@superState('gameControllerResponder')
def didIKickIt(player):
    if player.firstFrame():
        player.brain.nav.stop()
    return Transition.getNextState(player, didIKickIt)

@superState('gameControllerResponder')
def spinToFaceBall(player):
    facingDest = RelRobotLocation(0.0, 0.0, 0.0)
    if player.brain.ball.bearing_deg < 0.0:
        player.side = RIGHT
        #facingDest.relH = -90
        facingDest.relH = player.brain.ball.bearing_deg + 10.0
    else:
        player.side = LEFT
        #facingDest.relH = 90
        facingDest.relH = player.brain.ball.bearing_deg - 10.0
    player.brain.nav.goTo(facingDest,
                          nav.CLOSE_ENOUGH,
                          nav.CAREFUL_SPEED)

    if player.counter > 180:
        return player.goLater('spinAtGoal')

    return Transition.getNextState(player, spinToFaceBall)

@superState('gameControllerResponder')
def waitToFaceField(player):
    if player.firstFrame():
        player.brain.tracker.lookToAngle(0)

    return Transition.getNextState(player, waitToFaceField)

@superState('gameControllerResponder')
def returnToGoal(player):
    if player.firstFrame():
        if player.lastDiffState == 'didIKickIt':
            correctedDest =(RelRobotLocation(0.0, 0.0, 0.0 ) -
                            returnToGoal.kickPose)
            print "Kick pose is: " + str(returnToGoal.kickPose)
        else:
            correctedDest = (RelRobotLocation(0.0, 0.0, 0.0) -
                             RelRobotLocation(player.brain.interface.odometry.x,
                                              0.0,
                                              0.0))

        if fabs(correctedDest.relX) < 5:
            correctedDest.relX = 0.0
        if fabs(correctedDest.relY) < 5:
            correctedDest.relY = 0.0
        if fabs(correctedDest.relH) < 5:
            correctedDest.relH = 0.0

        player.brain.nav.walkTo(correctedDest, nav.GRADUAL_SPEED)

    return Transition.getNextState(player, returnToGoal)

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
def centerWithPosts(player):
    vision = player.brain.interface.visionField
    lgp = vision.goal_post_l.visual_detection
    rgp = vision.goal_post_r.visual_detection
    if lgp.distance != 0.0 and rpg.distance != 0.0:
        avg = (lgp.distance + rgp.distance) * .5
    if lgp.bearing != 0.0 and rgp.bearing != 0.0:
        heading = (lgp.bearing + rgp.bearing) * .5
    if player.firstFrame():
        dest = RelRobotLocation(avg, y, heading)
        player.zeroHeads()
        player.brain.nav.goTo(dest,
                              nav.CLOSE_ENOUGH,
                              nav.MEDIUM_SPEED)

    dest.relX = avg
    dest.relH = heading

    return Transition.getNextState(player, centerWithPosts)

@superState('gameControllerResponder')
def positionWithPost(player):
    vision = player.brain.interface.visionField

    #e= 0.0

    if player.firstFrame():
        player.brain.tracker.trackPost()
        if positionWithPost.tCornerCloserThanPost:
            positionWithPost.y = 50.0
        else:
            positionWithPost.y = -10.0
        if vision.goal_post_r.visual_detection.distance != 0.0:
            post = vision.goal_post_r
            positionWithPost.post = RIGHT
        else:
            post = vision.goal_post_l
            positionWithPost.post = LEFT
        positionWithPost.counter = 0
        positionWithPost.dest = RelRobotLocation(post.visual_detection.distance,
                                                 positionWithPost.y,
                                                 0.0)
        player.brain.nav.goTo(positionWithPost.dest,
                              nav.CLOSE_ENOUGH,
                              nav.MEDIUM_SPEED)


    changeTarget(player)
    if positionWithPost.post == RIGHT:
        post = vision.goal_post_r
    else:
        post = vision.goal_post_l

    if post.visual_detection.distance != 0.0:
        positionWithPost.dest.relX = post.visual_detection.distance
    positionWithPost.dest.relY = positionWithPost.y
    positionWithPost.counter += 1

    print "dist = " + str(post.visual_detection.distance)
    print "y = " + str(positionWithPost.y)
    return Transition.getNextState(player, positionWithPost)

@superState('gameControllerResponder')
def approachPost(player):
    vision = player.brain.interface.visionField
    if approachPost.post == RIGHT:
        post = vision.goal_post_r.visual_detection
        y = -20.0
        print "right post dist is " + str(post.distance)
    else:
        post = vision.goal_post_l.visual_detection
        y = 0.0
        print "left post dist is " + str(post.distance)


    if player.firstFrame():
        approachPost.counter = 0
        #player.zeroHeads()
        player.stand()
        player.brain.tracker.trackPost(approachPost.post)
        approachPost.dest = RelRobotLocation(post.distance,
                                y,
                                post.bearing)
        player.brain.nav.goTo(approachPost.dest,
                              nav.CLOSE_ENOUGH,
                              nav.MEDIUM_SPEED)
    if post.distance != 0.0:
        approachPost.dest.relX = post.distance
    if post.bearing != 0.0:
        approachPost.dest.relH = post.bearing
    approachPost.dest.relY = y
    approachPost.counter += 1
    #print "post dist = " + str(post.distance)
    print "y = " + str(y)

    return Transition.getNextState(player, approachPost)

def changeTarget(player):
    vision = player.brain.interface.visionField
    lgp = vision.goal_post_l.visual_detection
    rgp = vision.goal_post_r.visual_detection
    if positionWithPost.post == RIGHT:
        if lgp.distance > rgp.distance and positionWithPost.counter > 50:
            positionWithPost.post = LEFT
            positionWithPost.y = 0.0
    else:
        if rgp.distance > lgp.distance and positionWithPost.counter > 50:
            positionWithPost.post = RIGHT
            positionWithPost.y = 0.0

@superState('gameControllerResponder')
def changePost(player):
    if changePost.post == RIGHT:
        post = player.brain.interface.visionField.goal_post_r.visual_detection
        y = 10.0
    else:
        post = player.brain.interface.visionField.goal_post_l.visual_detection
        y = -10.0
    x = post.distance
    if player.firstFrame:
        player.brain.tracker.trackPost(changePost.post)
        dest = RelRobotLocation(x, y, 0.0)
        player.brain.nav.goTo(dest, nav.CLOSE_ENOUGH, nav.MEDIUM_SPEED)

    if post.distance != 0.0:
        dest.relX = post.distance
    dest.relY = y
    return Transition.getNextState(player, changePost)
changePost.post = 0
