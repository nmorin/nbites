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
        #spinAtGoal.home = RelRobotLocation(0, 0, 0)
        ## Decide which way to rotate based on the way we came from
        #if player.side == RIGHT:
        #    spinAtGoal.home.relH = -90
        #else:
        #    spinAtGoal.home.relH = 90
        #player.brain.nav.goTo(spinAtGoal.home,
        #                      nav.CLOSE_ENOUGH, nav.CAREFUL_SPEED)

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
            print "Player ball angle = " + str(player.ballAngle)

            # if player.ballAngle < -10.0:
            #     clearIt.near = False
            #     player.side = RIGHT
            #     player.kick = kicks.RIGHT_SHORT_STRAIGHT_KICK
            # elif player.ballAngle > 10.0:
            #     clearIt.near = False
            #     player.side = LEFT
            #     player.kick = kicks.LEFT_SHORT_STRAIGHT_KICK
            # elif player.brain.ball.rel_y < 0.0:
            #     clearIt.near = True
            #     player.side = RIGHT
            #     player.kick = kicks.RIGHT_SHORT_STRAIGHT_KICK
            # else:
            #     clearIt.near = True
            #     player.side = LEFT
            #     player.kick = kicks.LEFT_SHORT_STRAIGHT_KICK

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
        # if player.brain.ball.rel_x < 90.0:
        #     clearIt.near = True
        #     clearIt.xDest = player.brain.ball.rel_x - kickPose[0]
        # else:
        #     print "makeing clearit xdest = to 5!"
        #     clearIt.xDest = 5.0

        clearIt.ballDest = RelRobotLocation(player.brain.ball.rel_x - kickPose[0],
                                            player.brain.ball.rel_y -
                                            kickPose[1],
                                            0.0)

        # # reset odometry
        # player.brain.interface.motionRequest.reset_odometry = True
        # player.brain.interface.motionRequest.timestamp = int(player.brain.time * 1000)
        # clearIt.odoDelay = True
        return Transition.getNextState(player, clearIt)

    if clearIt.odoDelay:
        clearIt.odoDelay = False
        player.brain.nav.goTo(clearIt.ballDest,
                              nav.CLOSE_ENOUGH,
                              nav.MEDIUM_SPEED,
                              adaptive = False)

    kickPose = player.kick.getPosition()
    # if player.brain.ball.rel_x < 90.0:
    #     clearIt.near = True
    #     clearIt.xDest = player.brain.ball.rel_x - kickPose[0]

    clearIt.ballDest.relX = player.brain.ball.rel_x - kickPose[0]
    clearIt.ballDest.relY = player.brain.ball.rel_y - kickPose[1]

    # if not clearIt.near:
    #     clearIt.ballDest.relY = player.brain.ball.rel_y - kickPose[1] - 20.0

    # if fabs(clearIt.ballDest.relX) < 60.0 and fabs(clearIt.ballDest.relY) < 80.0 \
    #     and not clearIt.near:
    #     clearIt.ballDest.relH = - player.ballAngle
    #     clearIt.count += 1
    #     if clearIt.count > 45:
    #         clearIt.ballDest.relH = 0.0
    #         clearIt.ballDest.relY = player.brain.ball.rel_y - kickPose[1]

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

        if clearIt.near:
            y = - player.brain.interface.odometry.y
        elif player.side == LEFT:
            y = - player.brain.interface.odometry.y - 20.0
        else:
            y = - player.brain.interface.odometry.y + 20

        # newDest = RelRobotLocation(-returnToGoal.kickPose.relX, -returnToGoal.kickPose.relY,
                                    # -returnToGoal.kickPose.relH)
        newDest = RelRobotLocation(-90, -18, .09)

        if player.lastDiffState == 'didIKickIt':
            print "IN HERE!"
            returnToGoal.correctedDest =(RelRobotLocation(0.0, 0.0, 0.0 ) - returnToGoal.kickPose)
                            # RelRobotLocation(returnToGoal.kickPose.relX,
                            #                 returnToGoal.kickPose.relY,#- player.brain.interface.odometry.y,
                             #               0.0)) #player.brain.interface.odometry.h))
            # returnToGoal.correctedDest =(RelRobotLocation(0.0, 0.0, 0.0 ) -
                            # returnToGoal.kickPose)
            print "Kick pose is: " + str(returnToGoal.kickPose)
        else:
            print "NO HERE"
            returnToGoal.correctedDest = (RelRobotLocation(0.0, 0.0, 0.0) -
                                        RelRobotLocation(player.brain.interface.odometry.x,
                                              0.0,
                                              0.0))

        if fabs(returnToGoal.correctedDest.relX) < 5:
            returnToGoal.correctedDest.relX = 0.0
        if fabs(returnToGoal.correctedDest.relY) < 5:
            returnToGoal.correctedDest.relY = 0.0
        if fabs(returnToGoal.correctedDest.relH) < 5:
            returnToGoal.correctedDest.relH = 0.0

        print "Odometry y = " + str(returnToGoal.kickPose.relY)
        print "Odometry x = " + str(returnToGoal.kickPose.relX)
        print "Odometry H = " + str(returnToGoal.kickPose.relH)

        # player.brain.nav.destinationWalkTo(returnToGoal.correctedDest, nav.GRADUAL_SPEED)
        player.brain.nav.destinationWalkTo(newDest)

    # if player.side == RIGHT:
    #     returnToGoal.correctedDest.relY = -20.0
    # else:
    # returnToGoal.correctedDest.relY = 0.0

    # print "Odometry y = " + str(player.brain.interface.odometry.y)
    # print "Odometry x = " + str(player.brain.interface.odometry.x)
    # print "Odometry H = " + str(player.brain.interface.odometry.h)


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
def changePost(player):
    rgp = player.brain.interface.visionField.goal_post_r.visual_detection
    lgp = player.brain.interface.visionField.goal_post_l.visual_detection
    if lgp.distance != 0.0 and lgp.distance > rgp.distance:
        post = lgp
        tpost = LEFT
    else:
        post = rgp
        tpost = RIGHT
    #if post.bearing_deg < 0:
    #    y = -10.0
    #else:
    #    y = 5.0
    y = 0.0
    x = post.distance
    if player.firstFrame():
        changePost.counter = 0
        #print "post dist at first is: " + str(x)
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
        # player.brain.tracker.trackPost(approachPost.post)
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
    # if approachPost.counter % 10 == 0:
        # print "distance = " + str(approachPost.targetpost.distance)

    return Transition.getNextState(player, approachPost)
approachPost.lastPostDist = -1.0