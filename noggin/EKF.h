/**
 * EKF.h - Header file for the EKF class
 *
 * @author Tucker Hermans
 */

#ifndef EKF_h_DEFINED
#define EKF_h_DEFINED

// Boost libraries
#include <boost/numeric/ublas/matrix.hpp>
#include <boost/numeric/ublas/vector.hpp>

// Local headers
#include "NogginStructs.h"
#include "VisualBall.h"

// Default parameters
#define DEFAULT_BETA 3.0f
#define DEFAULT_GAMMA 2.0f

/**
 * Measurement - A generic class for holding the basic type information required
 *               for running the correctionStep in EKF.
 */
struct Measurement
{
    float distance;
    float bearing;
    float distanceSD;
    float bearingSD;
};

/**
 * EKF - An abstract class which implements the computational components of
 *       an Extended Kalman Filter.
 *
 * @date August 2008
 * @author Tucker Hermans
 */
class EKF
{
protected:
    boost::numeric::ublas::vector<float> xhat_k; // Estimate Vector
    boost::numeric::ublas::vector<float> xhat_k_bar; // A priori Estimate Vector
    boost::numeric::ublas::matrix<float> Q_k; // Input noise covariance matrix
    boost::numeric::ublas::matrix<float> A_k; // Update measurement Jacobian
    boost::numeric::ublas::matrix<float> P_k; // Uncertainty Matrix
    boost::numeric::ublas::matrix<float> P_k_bar; // A priori uncertainty Matrix
    boost::numeric::ublas::identity_matrix<float> dimensionIdentity;
    unsigned int numStates; // number of states in the kalman filter
    float beta; // constant uncertainty increase
    float gamma; // scaled uncertainty increase

public:
    // Constructors & Destructors
    EKF(unsigned int dimension, float _beta, float _gamma);
    virtual ~EKF() {}

    // Core functions
    virtual void timeUpdate(MotionModel u_k);
    virtual void correctionStep(std::vector<Measurement> z_k);
    virtual void noCorrectionStep();
private:
    // Pure virtual methods to be specified by implementing class
    virtual boost::numeric::ublas::vector<float> associateTimeUpdate(MotionModel
                                                                     u_k) = 0;
    virtual void incorporateMeasurement(Measurement z,
                                        boost::numeric::ublas::
                                        matrix<float> &H_k,
                                        boost::numeric::ublas::
                                        matrix<float> &R_k,
                                        boost::numeric::ublas::
                                        vector<float> &V_k) = 0;
};

// Math helper functions
// Should probably be housed elswhere
boost::numeric::ublas::matrix<float> invert2by2(boost::numeric::ublas::
                                                matrix<float> toInvt);
/**
 * Given a float return its sign
 *
 * @param f the number to examine the sign of
 * @return -1.0f if f is less than 0.0f, 1.0f otherwise
 */
inline float sign(float f)
{
    if (f < 0.0f) {
        return -1.0f;
    } else if (f > 0.0f) {
        return 1.0f;
    } else {
        return 0.0f;
    }
}
#endif //EKF_h_DEFINED
