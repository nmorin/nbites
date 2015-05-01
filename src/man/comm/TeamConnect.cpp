/**
 * Class to handle team communications.
 * @author Josh Zalinger and Wils Dawson 4/30/12
 */

#include "TeamConnect.h"

#include <unistd.h>
#include <iostream>
#include <string>
#include <math.h>

#include "CommDef.h"
#include "DebugConfig.h"
#include "Profiler.h"
#include "SPLStandardMessage.h"
#include "NBMath.h"
#include "FieldConstants.h"

namespace man {

namespace comm {

TeamConnect::TeamConnect(CommTimer* t, NetworkMonitor* m)
    : timer(t), monitor(m), myLastSeqNum(0)
{
    socket = new UDPSocket();
    setUpSocket();
}

TeamConnect::~TeamConnect()
{
    delete socket;
}

void TeamConnect::setUpSocket()
{
    socket->setBlocking(false);
    socket->setBroadcast(true);

    socket->setTarget(IP_TARGET, TEAM_PORT);
    socket->bind("", TEAM_PORT); // listen for anything on our port
}

void TeamConnect::send(const messages::WorldModel& model,
                       int player, int team, int burst = 1)
{
    if (!model.IsInitialized())
    {
#ifdef DEBUG_COMM
        std::cerr << "Comm does not have a valid input to send." << std::endl;
#endif
        return;
    }

    // create instance SPLStandardMessage
    struct SPLStandardMessage splMessage;

PROF_ENTER(P_COMM_BUILD_PACKET);

    portals::Message<messages::TeamPacket> teamMessage(0);

    messages::TeamPacket* arbData = teamMessage.get();

    // create packet from message fields
    arbData->mutable_payload()->CopyFrom(model);
    arbData->set_sequence_number(myLastSeqNum++);
    arbData->set_player_number(player);
    arbData->set_team_number(team);
    arbData->set_header(UNIQUE_ID);
    arbData->set_timestamp(timer->timestamp());

    // build packet the regular way, using arbData
    strncpy(splMessage.header, SPL_STANDARD_MESSAGE_STRUCT_HEADER, sizeof(splMessage.header));
    splMessage.version = SPL_STANDARD_MESSAGE_STRUCT_VERSION;
    splMessage.playerNum = (uint8_t)arbData->player_number();
    splMessage.teamNum = (uint8_t)arbData->team_number();
    splMessage.fallen = (uint8_t)model.fallen();
    
    splMessage.pose[0] = (model.my_x()-CENTER_FIELD_X)*CM_TO_MM;
    splMessage.pose[1] = (model.my_y()-CENTER_FIELD_Y)*CM_TO_MM;
    splMessage.pose[2] = model.my_h();
   
    splMessage.walkingTo[0] = (model.walking_to_x()-CENTER_FIELD_X)*CM_TO_MM;
    splMessage.walkingTo[1] = (model.walking_to_y()-CENTER_FIELD_Y)*CM_TO_MM;
    
    if (model.in_kicking_state()) {
        splMessage.shootingTo[0] = (model.kicking_to_x()-CENTER_FIELD_X)*CM_TO_MM;
        splMessage.shootingTo[1] = (model.kicking_to_y()-CENTER_FIELD_Y)*CM_TO_MM;
    }
    else {
        splMessage.shootingTo[0] = splMessage.pose[0];
        splMessage.shootingTo[1] = splMessage.pose[1];
    }
    
    splMessage.ballAge = model.ball_age()*1000; // seconds to milliseconds

    // @TODO: the logic for this conversion is somewhere else in the code, use it
    splMessage.ball[0] = model.ball_dist()*CM_TO_MM * (float)cos(model.ball_bearing()*TO_RAD);
    splMessage.ball[1] = model.ball_dist()*CM_TO_MM * (float)sin(model.ball_bearing()*TO_RAD);

    splMessage.ballVel[0] = model.ball_vel_x()*CM_TO_MM;
    splMessage.ballVel[1] = model.ball_vel_y()*CM_TO_MM;

    // describes what robot intends to do (which player they intend to be)
    switch(arbData->player_number()) {
        case 1:
            splMessage.intention = (uint8_t)1;
            break;
        case 2:
        case 3:
            splMessage.intention = (uint8_t)2;
            break;
        case 4:
        case 5:
            splMessage.intention = (uint8_t)3;
            break;
        default:
            splMessage.intention = (uint8_t)0;
    }

    splMessage.averageWalkSpeed = (uint16_t)117;
    splMessage.maxKickDistance = (uint16_t)500;
    splMessage.currentPositionConfidence = (uint16_t)70;
    splMessage.currentSideConfidence = (uint16_t)70;

    // std::cout << "----------------------" << std::endl;
    // std::cout << "header:" << splMessage.header << std::endl;
    // std::cout << "version:" << unsigned(splMessage.version) << std::endl;
    // std::cout << "playerNum:" << static_cast<int16_t>(splMessage.playerNum) << std::endl;
    // std::cout << "teamNum:" << splMessage.teamNum << std::endl;
    // std::cout << "fallen:" << splMessage.fallen << std::endl;
    // std::cout << "pose:" << splMessage.pose[0] << " " << splMessage.pose[1] << " " << splMessage.pose[2] << std::endl;
    // std::cout << "walkingTo:" << splMessage.walkingTo[0] << " " << splMessage.walkingTo[1] << std::endl;
    // std::cout << "shootingTo:" << splMessage.shootingTo[0] << " " << splMessage.shootingTo[1] << std::endl;
    // std::cout << "ballAge:" << splMessage.ballAge << std::endl;
    // std::cout << "ball:" << splMessage.ball[0] << " " << splMessage.ball[1] << std::endl;
    // std::cout << "ballVel:" << splMessage.ballVel[0] << " " << splMessage.ballVel[1] << std::endl;

    // std::cout << "intention:" << static_cast<int16_t>(splMessage.intention) << std::endl;
    // std::cout << "averageWalkSpeed:" << splMessage.averageWalkSpeed << std::endl;
    // std::cout << "maxKickDistance:" << splMessage.maxKickDistance << std::endl;
    // std::cout << "currentSideConfidence:" << static_cast<int16_t>(splMessage.currentSideConfidence) << std::endl;
    // std::cout << "currentPositionConfidence:" << static_cast<int16_t>(splMessage.currentPositionConfidence) << std::endl;

PROF_EXIT(P_COMM_BUILD_PACKET);

PROF_ENTER(P_COMM_SERIALIZE_PACKET);

    // serialize the teamMessage for putting into the final field of the packet
    int dataByteSize = arbData->ByteSize();
    char datagram_arbdata[dataByteSize];
    arbData->SerializeToArray(datagram_arbdata, dataByteSize);

    // put it into the packet, along with its size
    memcpy(splMessage.data, datagram_arbdata, dataByteSize);
    splMessage.numOfDataBytes = (uint16_t) dataByteSize;

PROF_EXIT(P_COMM_SERIALIZE_PACKET);

PROF_ENTER(P_COMM_TO_SOCKET);
    for (int i = 0; i < burst; ++i)
    {
        socket->sendToTarget((char*) &splMessage, sizeof(SPLStandardMessage));
    }
PROF_EXIT(P_COMM_TO_SOCKET);
}

void TeamConnect::receive(portals::OutPortal<messages::WorldModel>* modelOuts [NUM_PLAYERS_PER_TEAM],
                          int player, int team)
{
    // std::cout << "Should NOT receive anything in drop in" << std::endl;
            // Don't receive anything if drop in
}

bool TeamConnect::verify(SPLStandardMessage* splMessage, int seqNumber, int64_t timestamp, llong recvdtime,
                        int player, int team)
{
    if (!memcmp(splMessage->header, SPL_STANDARD_MESSAGE_STRUCT_HEADER, sizeof(SPL_STANDARD_MESSAGE_STRUCT_HEADER)))
    {
#ifdef DEBUG_COMM
        std::cout << "Received packet with bad header"
                  << " in TeamConnect::verifyHeader()" << std::endl;
#endif
        return false;
    }

    if (splMessage->teamNum != team)
    {
#ifdef DEBUG_COMM
        std::cout << "Received packet with bad teamNumber"
                  << " in TeamConnect::verifyHeader()" << std::endl;
#endif
        return false;
    }

    int playerNum = splMessage->playerNum;

    if (playerNum < 0 || playerNum > NUM_PLAYERS_PER_TEAM)
    {
#ifdef DEBUG_COMM
        std::cout << "Received packet with bad playerNumber"
                  << " in TeamConnect::verify()" << std::endl;
#endif
        return false;
    }

    // if we care about who we recieve from:
    if (player != 0 && player != playerNum)
    {
#ifdef DEBUG_COMM
        std::cout << "Received packet with unwanted playerNumber"
                  << " in TeamConnect::verify()" << std::endl;
#endif
        return false;
    }

    if (seqNumber <= teamMates[playerNum-1].seqNum)
    {
        if (teamMates[playerNum-1].seqNum - seqNumber < RESET_SEQ_NUM_THRESHOLD)
        {
#ifdef DEBUG_COMM
            std::cout << "Received packet with old sequenceNumber"
                      << " in TeamConnect::verify()" << std::endl;
#endif
            return false;
        }
        // else we've restarted a robot, so consider it's packets new
    }

    // success, update seqNum and timeStamp and parse
    int lastSeqNum = teamMates[playerNum-1].seqNum;
    int delayed = seqNumber - lastSeqNum - 1;
    teamMates[playerNum-1].seqNum = seqNumber;
    
    // now attempt to syncronize the clocks of this robot and
    // the robot from which we just received, eventually the
    // two clocks will reach an equilibrium point (within a
    // reasonable margin of error) without the use of internet
    // based clock syncronizing (don't need outside world)
    llong newOffset = 0;

    if (timestamp + MIN_PACKET_DELAY > recvdtime)
    {
        newOffset = timestamp + MIN_PACKET_DELAY - recvdtime;
        timer->addToOffset(newOffset);
    }
    teamMates[playerNum-1].timestamp = timer->timestamp(); // @TODO: why is this not recvdtime (the time when the packet was recieved)?

    // update the monitor
    monitor->packetsDropped(delayed);
    monitor->packetReceived(timestamp, recvdtime + newOffset);

    return true;
}

void TeamConnect::checkDeadTeammates(portals::OutPortal<messages::WorldModel>* modelOuts [NUM_PLAYERS_PER_TEAM],
                                     llong time, int player)
{
    for (int i = 0; i < NUM_PLAYERS_PER_TEAM; ++i)
    {
        if (i+1 == player)
        {
            continue;
        }
        else if (time - teamMates[i].timestamp > TEAMMATE_DEAD_THRESHOLD)
        {
            portals::Message<messages::WorldModel> msg(0);
            msg.get()->set_active(false);
            modelOuts[i]->setMessage(msg);
        }
    }
}

}
}
