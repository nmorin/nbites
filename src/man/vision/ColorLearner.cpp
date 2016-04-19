#include "ColorLearner.h"

#include <algorithm>
#include <iostream>


using std::to_string;

namespace man {
namespace vision {

	ColorLearner::ColorLearner()
	{
	}

	ColorLearner::~ColorLearner() { }

	Colors* ColorLearner::run(FieldLineList* fieldLines, bool topCamera, 
		Colors* colors, ImageLiteU8 uImage, ImageLiteU8 vImage)
	{

		std::cout << "[COLORLEARNER DEBUG] Entering ColorLearner.run()\n";
		// prep
		int lineCenterY = uImage.height() / 2;
		int lineCenterX = uImage.width() / 2;

		// Create statistics
		std::map<int, int> uLineVals, vLineVals;

		int pixLineX, pixLineY;
		double houghLine1X0, houghLine1Y0, houghLine1X1, houghLine1Y1;
        double houghLine2X0, houghLine2Y0, houghLine2X1, houghLine2Y1;

        // Collect the pixel information from the lines
		for (int y = 0; y < uImage.height(); y++) {
			for (int x = 0; x < uImage.width(); x++) {
				int u_val = *uImage.pixelAddr(x,y);
				int v_val = *vImage.pixelAddr(x,y);

				for (int i = 0; i < fieldLines->size(); i++) {
					FieldLine& line = (*fieldLines)[i];
					HoughLine& houghLine1 = line[0];
					HoughLine& houghLine2 = line[1];
					pixLineX = x - lineCenterX;
					pixLineY = lineCenterY - y;

					houghLine1.rawEndPoints(0, 0, houghLine1X0, houghLine1Y0, houghLine1X1, houghLine1Y1);
	                houghLine2.rawEndPoints(0, 0, houghLine2X0, houghLine2Y0, houghLine2X1, houghLine2Y1);
                
	                if (houghLine1.pDist(pixLineX, pixLineY) > 0 && 
	                    houghLine2.pDist(pixLineX, pixLineY) > 0 &&
	                    houghLine1.qDist(pixLineX, pixLineY) < houghLine1.ep1() &&
	                    houghLine2.qDist(pixLineX, pixLineY) < houghLine2.ep1()
	                    ) 
	                {
	                	if (uLineVals.count(u_val))
	                        uLineVals[u_val]++;
	                    else
	                        uLineVals.insert(std::pair<int, int>(u_val, 1));

	                    if (vLineVals.count(v_val))
	                        vLineVals[v_val]++;
	                    else
	                        vLineVals.insert(std::pair<int, int>(v_val, 1));
	                }	
				}
			}
		}

		// Create statistics
		Statistics *uStat = new Statistics(uLineVals);
		Statistics *vStat = new Statistics(vLineVals);
		double uAvg = uStat->getAvg();
		double vAvg = uStat->getAvg();

		

		// Adjust color parameters of visionModule

		Colors* ret = colors; 




		return ret;
	}

// 	bool BallDetector::findBall(ImageLiteU8 orange, double cameraHeight)
// 	{
// 		const double CONFIDENCE = 0.5;

// 		if (debugBall) {
// 			candidates.clear();
// 		}

// 		blobber.run(orange.pixelAddr(), orange.width(), orange.height(),
// 					orange.pitch());

// 		Ball reset;
// 		_best = reset;
// 		width = orange.width();
// 		height = orange.height();

// 		// TODO: Sort blobber list by size
// 		for (auto i=blobber.blobs.begin(); i!=blobber.blobs.end(); i++) {
// 			int centerX = static_cast<int>((*i).centerX());
// 			int centerY = static_cast<int>((*i).centerY());
// 			int principalLength = static_cast<int>((*i).firstPrincipalLength());
// 			int principalLength2 = static_cast<int>((*i).secondPrincipalLength());
// 			bool occludedSide = false;
// 			bool occludedTop = false;
// 			bool occludedBottom = false;

// 			double x_rel, y_rel;

// 			double bIX = ((*i).centerX() - width/2);
// 			double bIY = (height / 2 - (*i).centerY()) -
// 				(*i).firstPrincipalLength();

// 			bool belowHoriz = homography->fieldCoords(bIX, bIY, x_rel, y_rel);

// 			if (preScreen(centerX, centerY, principalLength, principalLength2,
// 						  occludedSide, occludedTop, occludedBottom)) {
// 				continue;
// 			}

// 			Ball b((*i), x_rel, -1 * y_rel, cameraHeight, height,
// 				   width, topCamera, occludedSide, occludedTop,
// 				   occludedBottom);

// 			if (b.confidence() > CONFIDENCE) {
// #ifdef OFFLINE
// 				// we always want to draw the ball, even when not debugging it
// 				candidates.push_back(b);
// #endif
// 				if (debugBall) {
// 					std::cout << "accepted ball at: " << centerX << " " <<
// 						centerY << " because:\n" << b.properties()
// 							  << std::endl;
// 				}
// 				if (b.dist < _best.dist) {
// 					_best = b;
// 				}
// 			}
// 			else {
// 				if (debugBall) {
// 					std::cout << "declined ball at " << centerX << " " <<
// 						centerY << " because:\n" << b.properties()
// 							  << std::endl;
// 				}
// 			}
// 		}
// 		if (_best.confidence() > CONFIDENCE) {
// 			return true;
// 		}
// 		else {
// 			return false;
// 		}
// 	}

}
}
