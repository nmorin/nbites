#include "nbfuncs.h"

#include "RoboGrams.h"
#include "Images.h"
#include "vision/VisionModule.h"
#include "vision/FrontEnd.h"
#include "vision/Homography.h"
#include "ParamReader.h"
#include "NBMath.h"
#include "vision/Vision.h"

#include <cstdlib>
#include <netinet/in.h>
#include <assert.h>
#include <vector>
#include <string>
#include <iostream>
#include <fstream>
#include <map>
#include <cmath>

using nblog::Log;
using nblog::SExpr;

//man::vision::Colors* getColorsFromSExpr(SExpr* params);
void getCalibrationOffsets(Log* l, double* r, double* p, int w, int h, bool t);
void updateSavedColorParams(std::string sexpPath, SExpr* params, bool top);
SExpr getSExprFromSavedParams(int color, std::string sexpPath, bool top);
std::string getSExprStringFromColorJSonNode(boost::property_tree::ptree tree);
SExpr treeFromBall(man::vision::Ball& b);
SExpr treeFromBlob(man::vision::Blob& b);

messages::YUVImage emptyTop(
    man::vision::DEFAULT_TOP_IMAGE_WIDTH * 2,
    man::vision::DEFAULT_TOP_IMAGE_HEIGHT
);

messages::YUVImage emptyBot(
    man::vision::DEFAULT_TOP_IMAGE_WIDTH,
    man::vision::DEFAULT_TOP_IMAGE_HEIGHT / 2
);

void imageSizeCheck(bool top, int width, int height) {
    if (top) {
        if (width != 2 * man::vision::DEFAULT_TOP_IMAGE_WIDTH ||
            height != man::vision::DEFAULT_TOP_IMAGE_HEIGHT ) {
            printf("WARNING! topCamera dimensions (%i, %i) NOT DEFAULT, VisionModule results undefined!\n",
                   width, height);
        }
    } else {
        //bot
        if ( // 2 / 2 == 1
            width != man::vision::DEFAULT_TOP_IMAGE_WIDTH ||
            height != ( man::vision::DEFAULT_TOP_IMAGE_HEIGHT / 2 ) ) {
            printf("WARNING! botCamera dimensions (%i, %i) NOT DEFAULT, VisionModule results undefined!\n",
                   width, height);
        }
    }
}

//robotName may be empty ("").
man::vision::VisionModule& getModuleRef(const std::string robotName);

int Vision_func() {

    assert(args.size() == 1);

    printf("Vision_func()\n");

    Log* copy = new Log(args[0]);
    size_t length = copy->data().size();
    uint8_t buf[length];
    memcpy(buf, copy->data().data(), length);

    // Parse YUVImage S-expression
    // Determine if we are looking at a top or bottom image from log description
    bool topCamera = copy->description().find("camera_TOP") != std::string::npos;
    int width, height;
    std::vector<SExpr*> vec = copy->tree().recursiveFind("width");
    if (vec.size() != 0) {
        SExpr* s = vec.at(vec.size()-1);
        width = 2*s->get(1)->valueAsInt();
    } else {
        std::cout << "Could not get width from description!\n";
    }
    vec = copy->tree().recursiveFind("height");
    if (vec.size() != 0) {
        SExpr* s = vec.at(vec.size()-1);
        height = s->get(1)->valueAsInt();
    } else {
        std::cout << "Could not get height from description!\n";
    }
    
    imageSizeCheck(topCamera, width, height);

    // Location of lisp text file with color params
    std::string sexpPath = std::string(getenv("NBITES_DIR"));
    sexpPath += "/src/man/config/colorParams.txt";

    // Read number of bytes of image, inertials, and joints if exist
    messages::JointAngles joints;
    if (copy->tree().find("contents")->get(2)) {
        int numBytes[3];
        for (int i = 0; i < 3; i++)
            numBytes[i] = atoi(copy->tree().find("contents")->get(i+1)->
                                            find("nbytes")->get(1)->value().c_str());
        uint8_t* ptToJoints = buf + (numBytes[0] + numBytes[1]);
        joints.ParseFromArray((void *) ptToJoints, numBytes[2]);
    }

    // If log includes robot name (which it always should), pass to module
    SExpr* robotName = args[0]->tree().find("from_address");
    std::string rname;
    if (robotName != NULL) {
        rname = robotName->get(1)->value();
    }

    //man::vision::VisionModule module(width / 2, height, rname);
    man::vision::VisionModule& module = getModuleRef(rname);

    // Images to pass to vision module, top & bottom
    messages::YUVImage realImage(buf, width, height, width);

    // Setup module
    portals::Message<messages::YUVImage> rImageMessage(&realImage);
    portals::Message<messages::YUVImage> eImageMessage(
                                topCamera ? &emptyBot : & emptyTop );
    portals::Message<messages::JointAngles> jointsMessage(&joints);

    if (topCamera) {
        module.topIn.setMessage(rImageMessage);
        module.bottomIn.setMessage(eImageMessage);
    }
    else {
        module.topIn.setMessage(eImageMessage);
        module.bottomIn.setMessage(rImageMessage);
    }
    
    module.jointsIn.setMessage(jointsMessage);

    // If log includes color parameters in description, have module use those
    SExpr* colParams = args[0]->tree().find("Params");
    if (colParams != NULL) {

        // Set new parameters as frontEnd colorParams
        man::vision::Colors* c = module.getColorsFromLisp(colParams, 2);
        module.setColorParams(c, topCamera);

        // Look for atom value "SaveParams", i.e. "save" button press
        SExpr* save = colParams->get(1)->find("SaveParams");
        if (save != NULL) {
            // Save attached parameters to txt file
            updateSavedColorParams(sexpPath, colParams, topCamera);
        }
    }

    // If log includes calibration parameters in description, have module use those
    std::vector<SExpr*> calParamsVec = args[0]->tree().recursiveFind("CalibrationParams");
    if (calParamsVec.size() != 0) {
        SExpr* calParams = calParamsVec.at(calParamsVec.size()-2);
        calParams = topCamera ? calParams->find("camera_TOP") : calParams->find("camera_BOT");
        if (calParams != NULL) {
            std::cout << "Found and using calibration params in log description: "
            << "Roll: " << calParams->get(1)->valueAsDouble() << " Tilt: " <<  calParams->get(2)->valueAsDouble()<< std::endl;
            man::vision::CalibrationParams* ncp =
            new man::vision::CalibrationParams(calParams->get(1)->valueAsDouble(),
                                           calParams->get(2)->valueAsDouble());

            module.setCalibrationParams(ncp, topCamera);
        }
    }

	// if log specified debug drawing parameters then set them
	SExpr* debugDrawing = args[0]->tree().find("DebugDrawing");
	if (debugDrawing != NULL) {
		module.setDebugDrawingParameters(debugDrawing);
	}

    // If log includes "BlackStar," set flag
    std::vector<SExpr*> blackStarVec = args[0]->tree().recursiveFind("BlackStar");
    if (blackStarVec.size() != 0)
        module.blackStar(true);
    
    // Run it!
    module.run();

    // -----------
    //   Y IMAGE
    // -----------
    man::vision::ImageFrontEnd* frontEnd = module.getFrontEnd(topCamera);

    Log* yRet = new Log();
    int yLength = (width / 4) * (height / 2) * 2;

    // Create temp buffer and fill with yImage from FrontEnd
    uint8_t yBuf[yLength];
    memcpy(yBuf, frontEnd->yImage().pixelAddr(), yLength);

    // Convert to string and set log
    std::string yBuffer((const char*)yBuf, yLength);
    yRet->setData(yBuffer);

    rets.push_back(yRet);

    // ---------------
    //   WHITE IMAGE
    // ---------------
    Log* whiteRet = new Log();
    int whiteLength = (width / 4) * (height / 2);

    // Create temp buffer and fill with white image 
    uint8_t whiteBuf[whiteLength];
    memcpy(whiteBuf, frontEnd->whiteImage().pixelAddr(), whiteLength);

    // Convert to string and set log
    std::string whiteBuffer((const char*)whiteBuf, whiteLength);
    whiteRet->setData(whiteBuffer);

    // Read params from Lisp and attach to image 
    whiteRet->setTree(getSExprFromSavedParams(0, sexpPath, topCamera));

    rets.push_back(whiteRet);

    // ---------------
    //   GREEN IMAGE
    // ---------------
    Log* greenRet = new Log();
    int greenLength = (width / 4) * (height / 2);

    // Create temp buffer and fill with gree image 
    uint8_t greenBuf[greenLength];
    memcpy(greenBuf, frontEnd->greenImage().pixelAddr(), greenLength);

    // Convert to string and set log
    std::string greenBuffer((const char*)greenBuf, greenLength);
    greenRet->setData(greenBuffer);

    // Read params from JSon and attach to image 
    greenRet->setTree(getSExprFromSavedParams(1, sexpPath, topCamera));

    rets.push_back(greenRet);

    // ----------------
    //   ORANGE IMAGE
    // ----------------
    Log* orangeRet = new Log();
    int orangeLength = (width / 4) * (height / 2);

    // Create temp buffer and fill with orange image 
    uint8_t orangeBuf[orangeLength];
    memcpy(orangeBuf, frontEnd->orangeImage().pixelAddr(), orangeLength);

    // Convert to string and set log
    std::string orangeBuffer((const char*)orangeBuf, orangeLength);
    orangeRet->setData(orangeBuffer);

    // Read params from JSon and attach to image 
    SExpr oTree = getSExprFromSavedParams(2, sexpPath, topCamera);
    oTree.append(SExpr::keyValue("width", width / 4));
    oTree.append(SExpr::keyValue("height", height / 2));

    orangeRet->setTree(oTree);

    rets.push_back(orangeRet);

    //-------------------
    //  SEGMENTED IMAGE
    //-------------------
    Log* colorSegRet = new Log();
    int colorSegLength = (width / 4) * (height / 2);

    // Create temp buffer and fill with segmented image
    uint8_t segBuf[colorSegLength];
    memcpy(segBuf, frontEnd->colorImage().pixelAddr(), colorSegLength);

    // Convert to string and set log
    std::string segBuffer((const char*)segBuf, colorSegLength);
    colorSegRet->setData(segBuffer);

    rets.push_back(colorSegRet);
    
    //-------------------
    //  EDGES
    //-------------------

    man::vision::EdgeList* edgeList = module.getEdges(topCamera);
    
    // Uncomment to display rejected edges used in center detection
    // man::vision::EdgeList* edgeList = module.getRejectedEdges(topCamera);

    Log* edgeRet = new Log();
    std::string edgeBuf;

    man::vision::AngleBinsIterator<man::vision::Edge> abi(*edgeList);
    for (const man::vision::Edge* e = *abi; e; e = *++abi) {
        uint32_t x = htonl(e->x() + (width / 8));
        edgeBuf.append((const char*) &x, sizeof(uint32_t));
        uint32_t y = htonl(-e->y() + (height / 4));
        edgeBuf.append((const char*) &y, sizeof(uint32_t));
        uint32_t mag = htonl(e->mag());
        edgeBuf.append((const char*) &mag, sizeof(uint32_t));
        uint32_t angle = htonl(e->angle());
        edgeBuf.append((const char*) &angle, sizeof(uint32_t));
    }

    edgeRet->setData(edgeBuf);
    rets.push_back(edgeRet);

    //-------------------
    //  LINES
    //-------------------
    man::vision::HoughLineList* lineList = module.getHoughLines(topCamera);

    Log* lineRet = new Log();
    std::string lineBuf;

    bool debugLines = false;
    if (debugLines)
        std::cout << std::endl << "Hough lines in image coordinates:" << std::endl;

    for (auto it = lineList->begin(); it != lineList->end(); it++) {
        man::vision::HoughLine& line = *it;

        // Get image coordinates
        double icR = line.r();
        double icT = line.t();
        double icEP0 = line.ep0();
        double icEP1 = line.ep1();

        int houghIndex = line.index();
        int fieldIndex = line.fieldLine();

        // Get field coordinates
        double fcR = line.field().r();
        double fcT = line.field().t();
        double fcEP0 = line.field().ep0();
        double fcEP1 = line.field().ep1();

        // Java uses big endian representation
        endswap<double>(&icR);
        endswap<double>(&icT);
        endswap<double>(&icEP0);
        endswap<double>(&icEP1);
        endswap<int>(&houghIndex);
        endswap<int>(&fieldIndex);
        endswap<double>(&fcR);
        endswap<double>(&fcT);
        endswap<double>(&fcEP0);
        endswap<double>(&fcEP1);


        lineBuf.append((const char*) &icR, sizeof(double));
        lineBuf.append((const char*) &icT, sizeof(double));
        lineBuf.append((const char*) &icEP0, sizeof(double));
        lineBuf.append((const char*) &icEP1, sizeof(double));
        lineBuf.append((const char*) &houghIndex, sizeof(int));
        lineBuf.append((const char*) &fieldIndex, sizeof(int));
        lineBuf.append((const char*) &fcR, sizeof(double));
        lineBuf.append((const char*) &fcT, sizeof(double));
        lineBuf.append((const char*) &fcEP0, sizeof(double));
        lineBuf.append((const char*) &fcEP1, sizeof(double));

        if (debugLines)
            std::cout << line.print() << std::endl;
    }

    if (debugLines)
        std::cout << std::endl << "Hough lines in field coordinates:" << std::endl;

    int i = 0;
    for (auto it = lineList->begin(); it != lineList->end(); it++) {
        man::vision::HoughLine& line = *it;
        if (debugLines)
            std::cout << line.field().print() << std::endl;
    }

    if (debugLines) {
        std::cout << std::endl << "Field lines:" << std::endl;
        std::cout << "0.idx, 1.idx, id, idx" << std::endl;
    }
    man::vision::FieldLineList* fieldLineList = module.getFieldLines(topCamera);

    for (int i = 0; i < fieldLineList->size(); i++) {
        man::vision::FieldLine& line = (*fieldLineList)[i];
        if (debugLines)
            std::cout << line.print() << std::endl;
    }

    if (debugLines)
        std::cout << std::endl << "Goalbox and corner detection:" << std::endl;
    man::vision::GoalboxDetector* box = module.getBox(topCamera);
    man::vision::CornerDetector* corners = module.getCorners(topCamera);

    if (debugLines) {
       if (box->first != NULL)
          std::cout << box->print() << std::endl;
    }

    if (debugLines) {
        std::cout << "    line0, line1, type (concave, convex, T)" << std::endl;
        for (int i = 0; i < corners->size(); i++) {
            const man::vision::Corner& corner = (*corners)[i];
           std::cout << corner.print() << std::endl;
        }
    }

    lineRet->setData(lineBuf);
    rets.push_back(lineRet);

    //-----------
    //  BALL
    //-----------
    man::vision::BallDetector* detector = module.getBallDetector(topCamera);

    Log* ballRet = new Log();
    std::vector<man::vision::Ball> balls = detector->getBalls();
    std::list<man::vision::Blob> blobs = detector->getBlobber()->blobs;

    SExpr allBalls;
    int count = 0;
    for (auto i=balls.begin(); i!=balls.end(); i++) {
        SExpr ballTree = treeFromBall(*i);
        SExpr next = SExpr::keyValue("ball" + std::to_string(count), ballTree);
        allBalls.append(next);
        count++;
    }
    count = 0;
    for (auto i=blobs.begin(); i!=blobs.end(); i++) {
        SExpr blobTree = treeFromBlob(*i);
        SExpr next = SExpr::keyValue("blob" + std::to_string(count), blobTree);
        allBalls.append(next);
        count++;
    }

    ballRet->setTree(allBalls);
    rets.push_back(ballRet);

    //---------------
    // Center Circle
    //---------------

    man::vision::CenterCircleDetector* ccd = module.getCCD(topCamera);
    Log* ccdRet = new Log();
    std::string pointsBuf;

    std::vector<std::pair<double, double>> points = ccd->getPotentials();
    for (std::pair<double, double> p : points) {
        endswap<double>(&(p.first));
        endswap<double>(&(p.second));
        pointsBuf.append((const char*) &(p.first), sizeof(double));
        pointsBuf.append((const char*) &(p.second), sizeof(double));
    }

    // Add 0,0 point if cc if off so tool doesn't display a rejected one
    std::pair<double, double> zero(0.0, 0.0);
    if (!ccd->on()) {
        pointsBuf.append((const char*) &(zero.first), sizeof(double));
        pointsBuf.append((const char*) &(zero.second), sizeof(double));
    }

    ccdRet->setData(pointsBuf);
    rets.push_back(ccdRet);

	std::cout << "Debug image" << std::endl;
    //-------------------
    //  DEBUG IMAGE
    //-------------------
    Log* debugImage = new Log();
    int debugImageLength = (width / 2) * (height / 2);

    // Create temp buffer and fill with debug image
    uint8_t debBuf[debugImageLength];
    memcpy(debBuf, module.getDebugImage(topCamera)->pixArray(), debugImageLength);

    // Convert to string and set log
    std::string debBuffer((const char*)debBuf, debugImageLength);
    debugImage->setData(debBuffer);

    rets.push_back(debugImage);

    return 0;
}

int CameraCalibration_func() {
    printf("CameraCalibrate_func()\n");

    int failures = 0;
    double totalR = 0;
    double totalT = 0;
    
    man::vision::VisionModule& module = getModuleRef("");

    // Repeat for each log
    for (int i = 0; i < 7; i++) {
        module.reset();
        
        Log* l = new Log(args[i]);

        size_t length = l->data().size();
        uint8_t buf[length];
        memcpy(buf, l->data().data(), length);

        // Determine description
        bool top = l->description().find("camera_TOP") != std::string::npos;
        
        int width = 2*atoi(l->tree().find("contents")->get(1)->
                                        find("width")->get(1)->value().c_str());
        int height = atoi(l->tree().find("contents")->get(1)->
                                       find("height")->get(1)->value().c_str());

        imageSizeCheck(top, width, height);
        
        double rollChange, pitchChange;

        // Read number of bytes of image, inertials, and joints if exist
        int numBytes[3];
        std::vector<SExpr*> vec = l->tree().recursiveFind("YUVImage");
        if (vec.size() != 0) {
            SExpr* s = vec.at(vec.size()-2)->find("nbytes");
            if (s != NULL) {
                numBytes[0] = s->get(1)->valueAsInt();
            }
        }

        vec = l->tree().recursiveFind("InertialState");
        if (vec.size() != 0) {
            SExpr* s = vec.at(vec.size()-2)->find("nbytes");
            if (s != NULL) {
                numBytes[1] = s->get(1)->valueAsInt();
            }
        }

        messages::JointAngles joints;
        vec = l->tree().recursiveFind("JointAngles");
        if (vec.size() != 0) {
            SExpr* s = vec.at(vec.size()-2)->find("nbytes");
            if (s != NULL) {
                numBytes[2] = s->get(1)->valueAsInt();
                uint8_t* ptToJoints = buf + (numBytes[0] + numBytes[1]);
                joints.ParseFromArray((void *) ptToJoints, numBytes[2]);
            } else {
                std::cout << "Could not load joints from description.\n";
                rets.push_back(new Log("((failure))"));
                return 0;
            }
        }

        // If log includes "BlackStar," set flag
        std::vector<SExpr*> blackStarVec = args[0]->tree().recursiveFind("BlackStar");
        if (blackStarVec.size() != 0)
            module.blackStar(true);
        
        // Create messages
        messages::YUVImage image(buf, width, height, width);
        portals::Message<messages::YUVImage> imageMessage(&image);
        portals::Message<messages::JointAngles> jointsMessage(&joints);

        if (top) {
            portals::Message<messages::YUVImage> emptyMessage(&emptyBot);
            module.topIn.setMessage(imageMessage);
            module.bottomIn.setMessage(emptyMessage);
        } else {
            portals::Message<messages::YUVImage> emptyMessage(&emptyTop);
            module.topIn.setMessage(emptyMessage);
            module.bottomIn.setMessage(imageMessage);
        }
        
        module.jointsIn.setMessage(jointsMessage);

        module.run();

        man::vision::FieldHomography* fh = module.getFieldHomography(top);

        double rollBefore, tiltBefore, rollAfter, tiltAfter;

        rollBefore = fh->roll();
        tiltBefore = fh->tilt();

        std::cout << "Calibrating log " << i+1 << ": "; 

        bool success = fh->calibrateFromStar(*module.getFieldLines(top));

        if (!success) {
            failures++;
        } else {
            rollAfter = fh->roll();
            tiltAfter = fh->tilt();
            totalR += rollAfter - rollBefore;
            totalT += tiltAfter - tiltBefore;
        }
    }

    if (failures > 4) {
        // Handle failure
        printf("Failed calibration %d times\n", failures);
        rets.push_back(new Log("(failure)"));
    } else {
        printf("Success calibrating %d times\n", 7 - failures);

        totalR /= (args.size() - failures);
        totalT /= (args.size() - failures);

        // Pass back averaged offsets to Tool
        std::string sexp = "((roll " + std::to_string(totalR) + ")(tilt " + std::to_string(totalT) + "))";
        rets.push_back(new Log(sexp));
    }
}


int Synthetics_func() {
    assert(args.size() == 1);

    printf("Synthetics_func()\n");
    
    double x = std::stod(args[0]->tree().find("contents")->get(1)->find("params")->get(1)->value().c_str());
    double y = std::stod(args[0]->tree().find("contents")->get(1)->find("params")->get(2)->value().c_str());
    double h = std::stod(args[0]->tree().find("contents")->get(1)->find("params")->get(3)->value().c_str());
    bool fullres = args[0]->tree().find("contents")->get(1)->find("params")->get(4)->value() == "true";
    bool top = args[0]->tree().find("contents")->get(1)->find("params")->get(5)->value() == "true";

    int wd = (fullres ? 320 : 160);
    int ht = (fullres ? 240 : 120);
    double flen = (fullres ? 544 : 272);

    int size = wd*4*ht*2;
    uint8_t pixels[size];
    man::vision::YuvLite synthetic(wd, ht, wd*4, pixels);

    man::vision::FieldHomography homography(top);
    homography.wx0(x);
    homography.wy0(y);
    homography.azimuth(h*TO_RAD);
    homography.flen(flen);

    man::vision::syntheticField(synthetic, homography);

    std::string sexpr("(nblog (version 6) (contents ((type YUVImage) ");
    sexpr += top ? "(from camera_TOP) " : "(from camera_BOT) ";
    sexpr += "(nbytes ";
    sexpr += std::to_string(size);
    sexpr += ") (width " + std::to_string(2*wd);
    sexpr += ") (height " + std::to_string(2*ht);
    sexpr += ") (encoding \"[Y8(U8/V8)]\"))))";

    Log* log = new Log(sexpr);
    std::string buf((const char*)pixels, size);
    log->setData(buf);

    rets.push_back(log);
}

// Save the new color params to the colorParams.txt file
void updateSavedColorParams(std::string sexpPath, SExpr* params, bool top) {
    std::cout << "Saving params!" << std::endl;
    std::ifstream textFile;
    textFile.open(sexpPath);

    // Get size of file
    textFile.seekg (0, textFile.end);
    long size = textFile.tellg();
    textFile.seekg(0);
    
    // Read file into buffer and convert to string
    char* buff = new char[size];
    textFile.read(buff, size);
    std::string sexpText(buff);

    // Get SExpr from string
    SExpr* savedParams, * savedSExpr = SExpr::read((const std::string)sexpText);
    
    if (top) {
        savedParams = savedSExpr->get(1)->find("Top");
    } else {
        savedParams = savedSExpr->get(1)->find("Bottom");
    }

    // Remove "SaveParams True" pair from expression
    params->get(1)->remove(3);

    const std::vector<SExpr>& newParams = *params->get(1)->getList();
    savedParams->get(1)->setList(newParams);
       
    // Write out
    size = savedSExpr->print().length();
    char* buffer = new char[size + 1];
    std::strcpy(buffer, savedSExpr->print().c_str());
    std::ofstream out;
    out.open(sexpPath);
    out.write(buffer, savedSExpr->print().length());

    delete[] buff;
    delete[] buffer;
    textFile.close();
    out.close();
}

SExpr getSExprFromSavedParams(int color, std::string sexpPath, bool top) {
    std::ifstream textFile;
    textFile.open(sexpPath);

    // Get size of file
    textFile.seekg (0, textFile.end);
    long size = textFile.tellg();
    textFile.seekg(0);

    // Read file into buffer and convert to string
    char* buff = new char[size];
    textFile.read(buff, size);
    std::string sexpText(buff);

    // Get SExpr from string
    SExpr* savedSExpr = SExpr::read((const std::string)sexpText);

    // Point to required set of 6 params
    if (top)
        savedSExpr = savedSExpr->get(1)->find("Top");
    else
        savedSExpr = savedSExpr->get(1)->find("Bottom");

    if (color == 0)                                         // White
        savedSExpr = savedSExpr->get(1)->find("White");
    else if (color == 1)                                    // Green
        savedSExpr = savedSExpr->get(1)->find("Green");
    else                                                    // Orange
        savedSExpr = savedSExpr->get(1)->find("Orange");


    // Build SExpr from params
    std::vector<SExpr> atoms;
    for (SExpr s : *(savedSExpr->getList()))
        atoms.push_back(s);

    return SExpr(atoms);
}

SExpr treeFromBall(man::vision::Ball& b)
{
    SExpr x(b.x_rel);
    SExpr y(b.y_rel);
    SExpr p = SExpr::list({x, y});
    SExpr bl = treeFromBlob(b.getBlob());

    SExpr rel = SExpr::keyValue("rel", p);
    SExpr blob = SExpr::keyValue("blob", bl);
    SExpr exDiam = SExpr::keyValue("expectedDiam", b.expectedDiam);
    SExpr toRet = SExpr::list({rel, blob, exDiam});

    return toRet;
}

SExpr treeFromBlob(man::vision::Blob& b)
{
    SExpr x(b.centerX());
    SExpr y(b.centerY());
    SExpr p = SExpr::list({x, y});

    SExpr center = SExpr::keyValue("center", p);
    SExpr area = SExpr::keyValue("area", b.area());
    SExpr count = SExpr::keyValue("count", b.count());
    SExpr len1 = SExpr::keyValue("len1", b.firstPrincipalLength());
    SExpr len2 = SExpr::keyValue("len2", b.secondPrincipalLength());
    SExpr ang1 = SExpr::keyValue("ang1", b.firstPrincipalAngle());
    SExpr ang2 = SExpr::keyValue("ang2", b.secondPrincipalAngle());
    SExpr toRet = SExpr::list({center, area, count, len1, len2, ang1, ang2});

    return toRet;
}

int Scratch_func() {}

#include <map>
std::map<const std::string, man::vision::VisionModule *> vmRefMap;

man::vision::VisionModule& getModuleRef(const std::string robotName) {
    if (vmRefMap.find(robotName) != vmRefMap.end()) {
        printf("nbcross-getModuleRef REUSING MODULE [%s]\n",
               robotName.c_str() );
		man::vision::VisionModule* module = vmRefMap[robotName];
		module->reset();
        return *module;
        
    } else {
        printf("nbcross-getModuleRef CREATING NEW MODULE [%s]\n",
               robotName.c_str() );
        man::vision::VisionModule * newInst =
            new man::vision::VisionModule(man::vision::DEFAULT_TOP_IMAGE_WIDTH,
                                      man::vision::DEFAULT_TOP_IMAGE_HEIGHT, robotName);
        vmRefMap[robotName] = newInst;
        return *newInst;
    }
}

// - - -  - - - ---------------------------------------------------------------------

int findMaxKeyOfMap(std::map<int, int> *val_map) {
    int max_count = -1;
    int max_key = -1;
    int count, key;

    std::map<int, int>::iterator it;
    for ( it = val_map->begin(); it != val_map->end(); it++ ) {
        key = it->first;
        count = it->second;
        if (count > max_count) { 
            max_count = count;
            max_key = key;
        }
    }
    return max_key;
}

int findMaxKeyOfMapFloat(std::map<int, float> *val_map) {
    float max_count = -1;
    float max_key = -1;
    float count;
    int key;

    std::map<int, float>::iterator it;
    for ( it = val_map->begin(); it != val_map->end(); it++ ) {
        key = it->first;
        count = it->second;
        if (count > max_count) { 
            max_count = count;
            max_key = key;
        }
    }
    return max_key;
}

float calcWeightedGreenUVal(int u, int standard_u_green_val) {
    // weight function: y = 250 - x
    float uFloat = (float)u;
    float weightedCount = 255 - .5*uFloat;
    return weightedCount;
    float error = std::abs((float)u - (float)standard_u_green_val); 
    if (error == 0)
        return 1;
    return ((float)1 / (error*error + 1));
}

std::string compressIntMapToString(std::map<int, int> values, int min = -1) {
    std::string val_buffer;
    std::map<int, int>::iterator it;
    for ( it = values.begin(); it != values.end(); it++ ) {

        int val = it->first;
        int count = it->second;

        if (count < min)
            continue;
        endswap<int>(&val);
        endswap<int>(&count);

        val_buffer.append((const char*) &val, sizeof(int));
        val_buffer.append((const char*) &count, sizeof(int));
    }
    return val_buffer;
}

void setLogImageDataInShort(Log* logRet, man::vision::ImageLiteU8 *image, int width, int height) {
    int imageLength = (width / 4) * (height / 2) * 2;

    // Create temp buffer and fill with yImage from FrontEnd
    short imageBuf[imageLength];
    memcpy(imageBuf, image->pixelAddr(), imageLength);

    // Convert to string and set log
    std::string imageBuffer((const char*)imageBuf, imageLength);
    logRet->setData(imageBuffer);
}

int ColorLearnTest_func() {
    assert(args.size() == 1);
    printf("= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =\n");
    printf("ColorLearnTest_func()\n");
    int y_thresh = 90;
    //work on a copy of the arg so we can safely push to rets.
    
    Log * copy = new Log(args[0]);
    size_t length = copy->data().size();
    uint8_t buf[length];
    memcpy(buf, copy->data().data(), length);

    // Determine if top or bottom image from log description
    bool topCamera = copy->description().find("camera_TOP") != std::string::npos;
    int width, height;
    std::vector<SExpr*> vec = copy->tree().recursiveFind("width");
    if (vec.size() != 0) {
        SExpr *s = vec.at(vec.size()-1);
        width = 2*s->get(1)->valueAsInt();
        // TODO question for Bill, this was originally doubled, why? 
    } else {
        std::cout << "Could not find width in the description\n";
    }
    vec = copy->tree().recursiveFind("height");
    if (vec.size() != 0) {
        SExpr* s = vec.at(vec.size()-1);
        height = s->get(1)->valueAsInt();
    } else {
        std::cout << "Could not find height in description\n";
    }

    std::cout << " HEIGHT: " << height << " WIDTH " << width << std::endl;

    imageSizeCheck(topCamera, width, height);

    // joints if exist
    messages::JointAngles joints;
    if (copy->tree().find("contents")->get(2)) {
        int numBytes[3];
        for (int i = 0; i < 3; i++)
            numBytes[i] = atoi(copy->tree().find("contents")->get(i+1)->
                                            find("nbytes")->get(1)->value().c_str());
        uint8_t* ptToJoints = buf + (numBytes[0] + numBytes[1]);
        joints.ParseFromArray((void *) ptToJoints, numBytes[2]);
    }

    SExpr* robotName = args[0]->tree().find("from_address");
    std::string rname;
    if (robotName != NULL) {
        rname = robotName->get(1)->value();
    }

    // instance of vision module
    man::vision::VisionModule& module = getModuleRef(rname);

    messages::YUVImage realImage(buf, width, height, width);

    // setup module
    portals::Message<messages::YUVImage> rImageMessage(&realImage);
    portals::Message<messages::YUVImage> eImageMessage(topCamera ? &emptyBot : &emptyTop);
    portals::Message<messages::JointAngles> jointsMessage(&joints);

    if (topCamera) {
        module.topIn.setMessage(rImageMessage);
        module.bottomIn.setMessage(eImageMessage);
    } else {
        module.topIn.setMessage(eImageMessage);
        module.bottomIn.setMessage(rImageMessage);
    }
    module.jointsIn.setMessage(jointsMessage);

    // run module
    module.run();

    // - - - - - - -  -  - - - - - --  this was setup
    bool test = realImage.pixelExists(19, 123);
    std::cout << "TEST TEST : " << test << std::endl;

    // get field line list
    man::vision::ImageFrontEnd* frontEnd = module.getFrontEnd(topCamera);


    // ---------------
    //   U IMAGE
    // ---------------
    std::cout << "[UV IMAGE TEST] Beg of get u image\n";

    Log* uRet = new Log();
    int uLength = (width / 4) * (height / 2);

    // Create temp buffer and fill with white image 
    uint8_t uBuf[uLength];
    memcpy(uBuf, frontEnd->uImage().pixelAddr(), uLength);

    // Convert to string and set log
    std::string uBuffer((const char*)uBuf, uLength);
    uRet->setData(uBuffer);

    rets.push_back(uRet);

    std::cout << "[UV IMAGE TEST] End of get u image\n";

    // ---------------
    //   V IMAGE
    // ---------------
    std::cout << "[UV IMAGE TEST] Beg of v image\n";

    Log* vRet = new Log();
    int vLength = (width / 4) * (height / 2);

    // Create temp buffer and fill with white image 
    uint8_t vBuf[vLength];
    memcpy(vBuf, frontEnd->vImage().pixelAddr(), vLength);

    // Convert to string and set log
    std::string vBuffer((const char*)vBuf, vLength);
    vRet->setData(vBuffer);

    rets.push_back(vRet);

    std::cout << "[UV IMAGE TEST] End of get u image\n";

    // -----------
    //   Y IMAGE
    // -----------

    Log* yRet = new Log();
    int yLength = (width / 4) * (height / 2) * 2;

    // Create temp buffer and fill with yImage from FrontEnd
    short yBuf[yLength];
    memcpy(yBuf, frontEnd->yImage().pixelAddr(), yLength);

    // Convert to string and set log
    std::string yBuffer((const char*)yBuf, yLength);
    yRet->setData(yBuffer);

    rets.push_back(yRet);

    // -------------
    // -------------

    // -----------
    //   PIXELS INSIDE FIELD LINES
    // -----------
    



    man::vision::ImageLiteU8 uImageLite = frontEnd->uImage();
    man::vision::ImageLiteU8 vImageLite = frontEnd->vImage();
    man::vision::ImageLiteU16 yImageLite = frontEnd->yImage();
    int liteWidth = uImageLite.width();
    int liteHeight = uImageLite.height();

    // make copies to alter
    uint8_t destFieldUImage[liteHeight * liteWidth];
    memcpy(destFieldUImage, uImageLite.pixelAddr(), (liteWidth*liteHeight*sizeof(uint8_t)));
    uint8_t destFieldUImageFloat[liteHeight * liteWidth];
    memcpy(destFieldUImageFloat, uImageLite.pixelAddr(), (liteWidth*liteHeight*sizeof(uint8_t)));
    uint8_t destFieldUVImage[liteHeight * liteWidth];
    memcpy(destFieldUVImage, uImageLite.pixelAddr(), (liteWidth*liteHeight*sizeof(uint8_t)));

    man::vision::ImageLiteU8 fieldUImageLite =  man::vision::ImageLiteU8(liteWidth, 
        liteHeight, uImageLite.pitch(), destFieldUImage);
    man::vision::ImageLiteU8 fieldUImageLiteFloat =  man::vision::ImageLiteU8(liteWidth, 
        liteHeight, uImageLite.pitch(), destFieldUImageFloat);
    man::vision::ImageLiteU8 fieldUVImageLite =  man::vision::ImageLiteU8(liteWidth, 
        liteHeight, uImageLite.pitch(), destFieldUVImage);


    // Get field line list
    man::vision::FieldLineList* fieldLineList = module.getFieldLines(topCamera);
    std::cout << "Found field line list\n";
    std::cout << "Size of fieldLineList: " << (*fieldLineList).size() << std::endl;

    // iterate over every pixel in image
    // perform check: if pixel exists
    // then use pDist(x, y) and test if positive; will be positive if the point is
    // on the brighter side of the line
    std::cout << "imageLite height: " << liteHeight << " width: " << liteWidth << std::endl;

    int lineCenterY = liteHeight / 2;
    int lineCenterX = liteWidth / 2;
    std::cout << "lineCenterX: " << lineCenterX << " lineCenterY: " << lineCenterY << std::endl;

    struct yuv_struct {
        yuv_struct(int y_, int u_, int v_) {
            y = y_;
            u = u_;
            v = v_;
        }
        int y;
        int u;
        int v;

        bool operator=(const yuv_struct &o) const {
            return y == o.y && u == o.u && v == o.v;
        }

        bool operator<(const yuv_struct &o) const {
            return y < o.y || (y == o.y && u < o.u) || (y == o.y && u == o.u && v < o.v);
        }
    };

    std::map<int, int> u_line_vals, v_line_vals, y_line_vals;
    std::map<int, int> yuv_line_vals;
    std::map<int, int> all_pixel_u_vals;
    std::map<int, float> all_pixel_u_vals_float_count;
    std::map<yuv_struct,int> all_pixels_yuv;

    int STANDARD_U_GREEN_VAL = 137;

    for (int y = 0; y < uImageLite.height(); y++) {
        for (int x = 0; x < uImageLite.width(); x++) {
            int u_val = *uImageLite.pixelAddr(x,y);
            int v_val = *vImageLite.pixelAddr(x,y);
            int y_val = *yImageLite.pixelAddr(x,y);
            y_val = y_val >> 2;
            // int yuv_val = (y_val << 16) & (u_val << 8) & y_val;

            yuv_struct pixel_yuv = yuv_struct(y_val, u_val, v_val);


            // std::cout << "[COLOR DEBUG] Y_val: " << y_val << "\n";
            // ---------------
            // track the u values of ALL the pixels in the image (for field color)
            // NORMAL, UNWEIGHTED:
            if (all_pixel_u_vals.count(u_val))
                all_pixel_u_vals[u_val]++;
            else
                all_pixel_u_vals.insert(std::pair<int, int>(u_val, 1));

            // std::cout << "[FIELDCOLORDEBUG] Weighted count of u val, instead of one: " << calcWeightedGreenUVal(u_val, STANDARD_U_GREEN_VAL) << "\n";
            
            // WEIGHTED ?? :
            if (all_pixel_u_vals_float_count.count(u_val)) {
                all_pixel_u_vals_float_count[u_val] += calcWeightedGreenUVal(u_val, STANDARD_U_GREEN_VAL);
            } else {
                all_pixel_u_vals_float_count.insert(std::pair<int, float>(u_val, calcWeightedGreenUVal(u_val, STANDARD_U_GREEN_VAL)));
            }
            // ---------------

            if (all_pixels_yuv.count(pixel_yuv))
                all_pixels_yuv[pixel_yuv]++;
            else
                all_pixels_yuv.insert(std::pair<yuv_struct, int>(pixel_yuv, 1));

            for (int i = 0; i < (*fieldLineList).size(); i++) {
                man::vision::FieldLine& line = (*fieldLineList)[i];
                man::vision::HoughLine& houghLine1 = line[0];
                man::vision::HoughLine& houghLine2 = line[1];
                int pixLineCoordX = x - lineCenterX;    // get pixel in line coordinates
                int pixLineCoordY = lineCenterY - y;

                double houghLine1X0, houghLine1Y0, houghLine1X1, houghLine1Y1;
                double houghLine2X0, houghLine2Y0, houghLine2X1, houghLine2Y1;
                houghLine1.rawEndPoints(0, 0, houghLine1X0, houghLine1Y0, houghLine1X1, houghLine1Y1);
                houghLine2.rawEndPoints(0, 0, houghLine2X0, houghLine2Y0, houghLine2X1, houghLine2Y1);
                
                // TODO add check for endpoints
                if (houghLine1.pDist(pixLineCoordX, pixLineCoordY) > 0 && 
                    houghLine2.pDist(pixLineCoordX, pixLineCoordY) > 0 &&
                    houghLine1.qDist(pixLineCoordX, pixLineCoordY) < houghLine1.ep1() &&
                    houghLine2.qDist(pixLineCoordX, pixLineCoordY) < houghLine2.ep1()
                    ) 
                {
                    
                    if (u_line_vals.count(u_val))
                        u_line_vals[u_val]++;
                    else
                        u_line_vals.insert(std::pair<int, int>(u_val, 1));

                    if (v_line_vals.count(v_val))
                        v_line_vals[v_val]++;
                    else
                        v_line_vals.insert(std::pair<int, int>(v_val, 1));

                    if (y_line_vals.count(y_val))
                        y_line_vals[y_val]++;
                    else
                        y_line_vals.insert(std::pair<int, int>(y_val, 1));

                    // if (yuv_line_vals.count(yuv_val))
                    //     yuv_line_vals[yuv_val]++;
                    // else
                    //     yuv_line_vals.insert(std::pair<int, int>(yuv_val, 1));
                    
                    // make pixel darker just for debug viewing
                    *(uImageLite.pixelAddr(x,y)) = (uint8_t)(0);

                } 
            }
        }
    }

    // ------------------------
    // Return u image with darkened pixels inside the field lines
    Log* linePixRet = new Log();
    setLogImageDataInShort(linePixRet, &uImageLite, width, height);
    rets.push_back(linePixRet);

    // ------------------------
    // Return u histogram vals
    Log* u_line_ret = new Log();
    u_line_ret->setData(compressIntMapToString(u_line_vals));
    rets.push_back(u_line_ret);
        
    // ------------------------
    // Return v histogram vals
    Log* v_line_ret = new Log();
    v_line_ret->setData(compressIntMapToString(v_line_vals));
    rets.push_back(v_line_ret);

    // ------------------------
    // Return y histogram vals

    // get y min cut off value 
    int yMin = -1;
    std::vector<SExpr*> yMinValS = args[0]->tree().recursiveFind("yMinVal");
    if (yMinValS.size() != 0) {
        SExpr* s = yMinValS.at(yMinValS.size()-1);
        yMin = s->get(1)->valueAsInt();
        std::cout << "[FIELDCOLORDEBUG] Found yMin: ";
        std::cout << yMin << "\n";
    } else {
        std::cout << "[FIELDCOLORDEBUG] did not find yMin\n";
    }


    Log* y_line_ret = new Log();
    y_line_ret->setData(compressIntMapToString(y_line_vals, yMin));
    rets.push_back(y_line_ret);

    // ------------------------
    // Return yuv histogram vals
    // Log* yuv_line_ret = new Log();
    // std::string yuv_line_val_buf;
    // std::map<int, int>::iterator ityuv;
    // for ( ityuv = yuv_line_vals.begin(); ityuv != yuv_line_vals.end(); ityuv++ ) {

    //     int val = ityuv->first;
    //     int count = ityuv->second;
    //     std::cout << "[CROSS HISTOGRAM] Val: " << val << " count: " << count << "\n";
    //     endswap<int>(&val);
    //     endswap<int>(&count);

    //     yuv_line_val_buf.append((const char*) &val, sizeof(int));
    //     yuv_line_val_buf.append((const char*) &count, sizeof(int));
    // }
    // y_line_ret->setData(y_line_val_buf);
    // rets.push_back(y_line_ret);


    // -----------
    // -----------
    //   DETERMINE FIELD COLOR
    // -----------

    // FIND USER SET VALUES FROM VIEW
    std::map<int, int> v_values_in_u_mask;
    int u_threshold_width = 3, v_threshold_width = 3;
    int uUV_threshold_width = 3, vUV_threshold_width = 3;
    int u_weighted_threshold_width = 3;
    int user_u_mode = 0;

    // get u threshold from slider
    std::vector<SExpr*> uThresholdS = args[0]->tree().recursiveFind("uThreshold");
    if (uThresholdS.size() != 0) {
        SExpr* s = uThresholdS.at(uThresholdS.size()-1);
        u_threshold_width = s->get(1)->valueAsInt();
        std::cout << "[FIELDCOLORDEBUG] Found u_threshold_width: ";
        std::cout << u_threshold_width << "\n";
    } else {
        std::cout << "[FIELDCOLORDEBUG] did not find u_threshold_width\n";
    }

    // get u weighted threshold from slider
    std::vector<SExpr*> uWeightedThresholdS = args[0]->tree().recursiveFind("uWeightedThreshold");
    if (uWeightedThresholdS.size() != 0) {
        SExpr* s = uWeightedThresholdS.at(uWeightedThresholdS.size()-1);
        u_weighted_threshold_width = s->get(1)->valueAsInt();
        std::cout << "[FIELDCOLORDEBUG] Found uWeightedThreshold: ";
        std::cout << u_weighted_threshold_width << "\n";
    } else {
        std::cout << "[FIELDCOLORDEBUG] did not find uWeightedThreshold\n";
    }

    // get user-defined u max
    std::vector<SExpr*> uFieldValS = args[0]->tree().recursiveFind("uFieldVal");
    if (uFieldValS.size() != 0) {
        SExpr* s = uFieldValS.at(uFieldValS.size()-1);
        user_u_mode = s->get(1)->valueAsInt();
        std::cout << "[FIELDCOLORDEBUG] Found user_u_mode: ";
        std::cout << user_u_mode << "\n";
    } else {
        std::cout << "[FIELDCOLORDEBUG] did not find user_u_mode\n";
    }

    // get u UV threshold from slider
    std::vector<SExpr*> uUVThresholdS = args[0]->tree().recursiveFind("uUVThresh");
    if (uUVThresholdS.size() != 0) {
        SExpr* s = uUVThresholdS.at(uUVThresholdS.size()-1);
        uUV_threshold_width = s->get(1)->valueAsInt();
        std::cout << "[FIELDCOLORDEBUG] Found uUV_threshold_width: ";
        std::cout << uUV_threshold_width << "\n";
    } else {
        std::cout << "[FIELDCOLORDEBUG] did not find uUV_threshold_width\n";
    }

    // get v UV threshold from slider
    std::vector<SExpr*> vUVThresholds = args[0]->tree().recursiveFind("vUVThresh");
    if (vUVThresholds.size() != 0) {
        SExpr* s = vUVThresholds.at(vUVThresholds.size()-1);
        vUV_threshold_width = s->get(1)->valueAsInt();
        std::cout << "[FIELDCOLORDEBUG] Found vUV_threshold_width: ";
        std::cout << vUV_threshold_width << "\n";
    } else {
        std::cout << "[FIELDCOLORDEBUG] did not find vUV_threshold_width\n";
    }




    int GREEN_THRESHOLD = (user_u_mode == 0) ? findMaxKeyOfMap(&all_pixel_u_vals) : user_u_mode;
    // NAIVE APPROACH
    // traverse each pixel in the image; if it is below a certain threshold, assume green
    // for (int y = 0; y < fieldUImageLite.height(); y++) {
    //     for (int x = 0; x < fieldUImageLite.width(); x++) {

    //         int uVal = *(fieldUImageLite.pixelAddr(x,y));   
    //         if (uVal < GREEN_THRESHOLD) {
    //             *(fieldUImageLite.pixelAddr(x,y)) = (uint8_t)(0);
    //         }         
    //     }
    // }

    // SLIGHTLY BETTER? ??? ?? 
    int mostCommonUVal = (user_u_mode == 0) ? findMaxKeyOfMap(&all_pixel_u_vals) : user_u_mode;
    std::cout << "[FIELDCOLORDEBUG] Most common u val: " << mostCommonUVal << "\n";

    for (int y = 0; y < fieldUImageLite.height(); y++) {
        for (int x = 0; x < fieldUImageLite.width(); x++) {

            int uVal = *(fieldUImageLite.pixelAddr(x,y));   
            int vVal = *vImageLite.pixelAddr(x,y);

            if (std::abs(uVal - mostCommonUVal) <= u_threshold_width) {
                *(fieldUImageLite.pixelAddr(x,y)) = (uint8_t)(0);

                // add to the mask of v values
                if (v_values_in_u_mask.count(vVal))
                    v_values_in_u_mask[vVal]++;
                else
                    v_values_in_u_mask.insert(std::pair<int, int>(vVal, 1));
            }         
        }
    }    

    // WITH WEIGHTS
    float mostCommonUValFloat = (user_u_mode == 0) ? findMaxKeyOfMapFloat(&all_pixel_u_vals_float_count) : (float)user_u_mode;
    std::cout << "[FIELDCOLORDEBUG] Most common float u val: " << mostCommonUValFloat << "\n";

    for (int y = 0; y < fieldUImageLiteFloat.height(); y++) {
        for (int x = 0; x < fieldUImageLiteFloat.width(); x++) {

            float uVal = (float) *(fieldUImageLiteFloat.pixelAddr(x,y));   
            if (std::abs(uVal - mostCommonUValFloat) <= u_weighted_threshold_width) {
                *(fieldUImageLiteFloat.pixelAddr(x,y)) = (uint8_t)(0);
            }         
        }
    }    

    // return the green field color
    Log* fieldURet = new Log();
    setLogImageDataInShort(fieldURet, &fieldUImageLite, width, height);
    rets.push_back(fieldURet);

    // -------------
    // Return the u whole field histogram vals
    int U_MIN_T = 10;
    Log* u_field_ret = new Log();
    u_field_ret->setData(compressIntMapToString(all_pixel_u_vals, U_MIN_T));
    rets.push_back(u_field_ret);

    // return the green field color with weighted function
    Log* fieldUFloatRet = new Log();
    setLogImageDataInShort(fieldUFloatRet, &fieldUImageLiteFloat, width, height);
    rets.push_back(fieldUFloatRet);

    // -------------
    // FIELD COLOR AGAIN with V FILTER
    // apply the v filter to the filtered u's
    int mostCommonVVal = findMaxKeyOfMap(&v_values_in_u_mask);
    std::cout << "[FIELDCOLORDEBUG] Most common v val in u vals: " << mostCommonUVal << "\n";

    for (int y = 0; y < fieldUVImageLite.height(); y++) {
        for (int x = 0; x < fieldUVImageLite.width(); x++) {

            int uVal = *(fieldUVImageLite.pixelAddr(x,y));   
            int vVal = *vImageLite.pixelAddr(x,y);

            if (std::abs(uVal - mostCommonUVal) <= uUV_threshold_width &&
                std::abs(vVal - mostCommonVVal) <= vUV_threshold_width) {
                *(fieldUVImageLite.pixelAddr(x,y)) = (uint8_t)(0);
            }         
        }
    } 

    // ------------------------
    // Return uv histogram vals
    Log* uv_field_ret = new Log();
    uv_field_ret->setData(compressIntMapToString(v_values_in_u_mask));
    rets.push_back(uv_field_ret);

    // return the green field color with weighted function
    Log* fieldUVRet = new Log();
    setLogImageDataInShort(fieldUVRet, &fieldUVImageLite, width, height);
    rets.push_back(fieldUVRet);

    // ------------------------
    // Return all pixel yuv histogram vals
    // Log* allPixYuvRet = new Log();
    // std::string all_pix_yuv_buf;
    // // int u_line_val_buf[u_line_vals.size() * 4]; 
    // std::map<yuv_struct, int>::iterator it_all_pix;
    // for ( it_all_pix = all_pixels_yuv.begin(); it_all_pix != all_pixels_yuv.end(); it_all_pix++ ) {

    //     yuv_struct pixYuv = it_all_pix->first;
    //     int y = pixYuv.y;
    //     int u = pixYuv.u;
    //     int v = pixYuv.v;
    //     int count = it_all_pix->second;
    //     endswap<int>(&y);
    //     endswap<int>(&u);
    //     endswap<int>(&v);
    //     endswap<int>(&count);

    //     all_pix_yuv_buf.append((const char*) &y, sizeof(int));
    //     all_pix_yuv_buf.append((const char*) &u, sizeof(int));
    //     all_pix_yuv_buf.append((const char*) &v, sizeof(int));
    //     all_pix_yuv_buf.append((const char*) &count, sizeof(int));
    // }
    // allPixYuvRet->setData(all_pix_yuv_buf);
    // rets.push_back(allPixY
    
    return 0;
}

