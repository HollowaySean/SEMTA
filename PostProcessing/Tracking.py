### Settings ###

# Import statements
import os
import numpy as np
import scipy.constants as constants
import scipy.io as sio
import csv
import json



### Function declarations ###

# Single unit Kalman filter
def KalmanFilterSingle(trackSingleIn, trackParams, frame, passDirection):

    # Unpack variables
    numFr = trackSingleIn['n_fr']

    # Unpack measurement values
    meas = dict()
    for key in trackSingleIn['meas'].keys():
        meas[key] = trackSingleIn['meas'][key][frame]

    # Check if track needs to be initialized
    if (passDirection == 'forward' and frame == 0) or (passDirection == 'reverse' and frame == numFr-1):

        # Use measurement as state prediction
        X_init = np.matrix([[
            meas['range'] * np.cos(meas['az'] * np.pi / 180),
            meas['vel'] * np.cos(meas['az'] * np.pi / 180),
            0,
            meas['range'] * np.sin(meas['az'] * np.pi / 180),
            meas['vel'] * np.sin(meas['az'] * np.pi / 180),
            0
        ]]).T

        # Use measurement uncertainties as covariance prediction
        P_init = GenerateStateCovariance(meas, trackParams)

        # Save results
        return SaveStepData(trackSingleIn, frame, X_init, P_init, X_init, P_init, meas['time'])

    else:

        # Calculate time step since previous hit
        if passDirection == 'forward':
            lastHitFrame = frame-1
        else:
            lastHitFrame = frame+1
        Tm = trackSingleIn['meas']['time'][frame] - trackSingleIn['meas']['time'][lastHitFrame]


    ## Calculate Model Matrices

    # Measurement covariance matrix
    if meas:
        R_full = np.diag(GenerateStateCovariance(meas, trackParams))
    else:
        meas_temp = dict()
        for key in trackSingleIn['meas'].keys():
            meas_temp[key] = trackSingleIn['meas'][key][lastHitFrame]
        R_full = np.diag(GenerateStateCovariance(meas_temp, trackParams))

    R = np.diag([R_full[i] for i in [0, 3]])

    # Process covariance matrix (NCA model)
    Q_1d = np.array([[(Tm**4)/4, (Tm**3)/2, (Tm**2)/2],
                     [(Tm**3)/2, (Tm**2),   (Tm)],
                     [(Tm**2)/2, (Tm),      1]])
    Q = np.asmatrix(np.concatenate((
                np.concatenate((Q_1d*(trackParams['sigma_v'][0]**2), np.zeros(Q_1d.shape)), axis=1), 
                np.concatenate((np.zeros(Q_1d.shape), Q_1d*(trackParams['sigma_v'][1]**2)), axis=1)), 
                axis=0))

    # Kinematic process matrix (NCA model)
    F_1d = np.array([[1,    (Tm),   (Tm**2)/2],
                     [0,    1,      (Tm)],
                     [0,    0,      1]])
    F = np.asmatrix(np.concatenate((
                np.concatenate((F_1d, np.zeros(F_1d.shape)), axis=1), 
                np.concatenate((np.zeros(F_1d.shape), F_1d), axis=1)), 
                axis=0))


    ## Prediction step

    # Predict kinematic vector
    X_pre = F * np.asmatrix(trackSingleIn['estimate'][lastHitFrame]['state'])

    # Predicted kinematic covariance
    P_pre = (F * (np.asmatrix(trackSingleIn['estimate'][lastHitFrame]['covar'])* F.T)) + Q


    ## Calculate measurement matrices

    # Measurement vector
    Z = np.matrix([
            meas['range'] * np.cos(meas['az'] * np.pi / 180),
            meas['range'] * np.sin(meas['az'] * np.pi / 180)])

    # Measurement matrix
    H = np.matrix([[1, 0, 0, 0, 0, 0],
                  [0, 0, 0, 1, 0, 0]])

    # Measurement residual
    Z_res = Z.T - (H * X_pre)


    ## Estimation Step

    # Measurement residual covariance
    S = H * (P_pre * H.T) + R

    # Kalman matrix
    K = (P_pre * H.T) * S.I

    # Estimated kinematic vector
    X_est = X_pre + (K * Z_res)

    # Estimated kinematic covariance
    P_est = P_pre - (K * (H * P_pre))

    # Save data
    return SaveStepData(trackSingleIn, frame, X_est, P_est, X_pre, P_pre, meas['time'])

# Save data for each Kalman filter step
def SaveStepData(trackIn, frame, X_est, P_est, X_pre, P_pre, time):

    # Save estimates
    trackIn['estimate'][frame] = dict(
        state   = X_est,
        covar   = P_est,
        cart    = [X_est[i] for i in [0, 3]],
        az      = np.arctan(X_est[3] / X_est[0]) * 180 / np.pi,
        range   = np.linalg.norm([X_est[i] for i in [0, 3]]),
        speed   = np.linalg.norm([X_est[i] for i in [1, 4]]),
        time    = time
    )

    # Save predictions
    trackIn['prediction'][frame] = dict(
        state   = X_pre,
        covar   = P_pre,
        cart    = [X_pre[i] for i in [0, 3]],
        az      = np.arctan(X_pre[3] / X_pre[0]) * 180 / np.pi,
        range   = np.linalg.norm([X_pre[i] for i in [0, 3]]),
        speed   = np.linalg.norm([X_pre[i] for i in [1, 4]]),
        time    = time
    )

    # Return data structure
    return trackIn

# Calculate state uncertainty matrix
def GenerateStateCovariance(meas, trackParams):

    # Calculate measurement variances
    sig_R, sig_A, sig_V = CalculateVariance(meas)

    # Convert to radians
    sig_A = sig_A * np.pi / 180

    # Calculate speed variance (assuming symmetric uniform distribution)
    speed_unc = 0.57735 * trackParams['max_vel']
    accel_unc = 0.57735 * trackParams['max_acc']

    # Calculate uncertainty matrix
    az_rad = meas['az'] * np.pi / 180
    P = np.diag([
        (sig_R * np.cos(az_rad))**2 
            + (sig_A * meas['range'] * np.sin(az_rad))**2,
        (sig_V * np.cos(az_rad))**2 
            + (speed_unc * meas['range'] * np.sin(az_rad))**2
            + (sig_A * meas['vel'] * np.sin(az_rad))**2,
        accel_unc,
        (sig_R * np.sin(az_rad))**2 
            + (sig_A * meas['range'] * np.cos(az_rad))**2,
        (sig_V * np.sin(az_rad))**2 
            + (speed_unc * meas['range'] * np.cos(az_rad))**2
            + (sig_A * meas['vel'] * np.cos(az_rad))**2,
        accel_unc
    ])
    return P

# Calculate measurement variance from empirical curves
def CalculateVariance(meas):

    # Unpack variables
    steer = meas['steer']
    range = meas['range']
    theta = meas['az']
    SNR = meas['SNR']
    C = constants.speed_of_light
    

    ## Calculate range variance

    # Calculate fading factor due to incomplete pulse return
    fade = np.min([1,
        2 * range / (C * 10e-6),
        (5e-5 - (2 * range / C)) / 10e-6
    ])

    # Calculate variance accounting only for SNR
    sig_R = 7.8927 * np.power(10, -SNR / 20)

    # Incorporate fading resolution loss
    sig_R /= fade**2


    ## Calculate angle variance

    # Calculate variance accounting only for SNR
    sig_A = (6.335 / 1.4817) / np.sqrt(2 * np.power(10, SNR / 10))

    # Adjust variance for beam steering loss
    sig_A /= np.cos(steer * np.pi / 180)**2

    # Adjust vaiance for offest from beam center
    offset = np.abs(theta - steer)
    sig_A *= np.sqrt(1 + (1.4817 * offset / 6.335)**2)


    ## Calculate velocity variance

    # Variance due only to SNR
    sig_V = np.power(10, -1.2517 - 0.0044602 * SNR)

    # Return tuple of results
    return (sig_R, sig_A, sig_V)

# Single unit, single pass processing
def TrackingSingleUnit(trackSingleIn, trackParams, passDirection):
    
    # Unpack variables
    numFr = trackSingleIn['n_fr']

    # Set up output data structure
    trackOut = dict(
        n_fr        = numFr,
        meas        = trackSingleIn['meas'],
        estimate    = [None]*numFr,
        prediction  = [None]*numFr
    )

    # Generate frame list
    if passDirection == 'forward':
        frList = range(0,numFr,1)
    elif passDirection == 'reverse':
        frList = range(numFr-1,-1,-1)

    # Loop through frames
    for fr in frList:
        trackOut = KalmanFilterSingle(trackOut, trackParams, fr, passDirection)

    # Return data object
    return trackOut

# Single unit, both pass processing
def TrackingSingleUnitBidirectional(trackSingleIn, trackParams):

    # Unpack variables
    numFr = trackSingleIn['n_fr']

    # Set up output data structure
    trackEstimate = [None]*numFr

    # Run forward and backward passes
    trackForward = TrackingSingleUnit(trackSingleIn, trackParams, 'forward')
    trackReverse = TrackingSingleUnit(trackSingleIn, trackParams, 'reverse')

    # Fuse data for each frame
    for fr in range(numFr):

        # Get current time
        currentTime = trackForward['meas']['time'][fr]

        # Unpack structures
        estF = trackForward['estimate'][fr]
        estR = trackReverse['estimate'][fr]

        # Perform inverse variance weighting
        varSum = np.asmatrix((1 / np.diagonal(estF['covar'])) + (1 / np.diagonal(estR['covar']))).T
        stateSum = (estF['state'] / np.asmatrix(np.diagonal(estF['covar'])).T) + (estR['state'] / np.asmatrix(np.diagonal(estR['covar'])).T)

        varNew = np.diag((1 / varSum.T).tolist()[0])
        stateNew = stateSum / varSum

        # Save data back to struct
        trackEstimate[fr] = dict(
            state   = stateNew,
            covar   = varNew,
            cart    = [stateNew[i] for i in [0, 3]],
            az      = np.arctan(stateNew[3] / stateNew[0]) * 180 / np.pi,
            range   = np.linalg.norm([stateNew[i] for i in [0, 3]]),
            speed   = np.linalg.norm([stateNew[i] for i in [1, 4]]),
            time    = currentTime
        )
            
    # Return data structure
    return trackEstimate

# Multi unit data fusion
def DataFusion(trackSingleIn):

    # Unpack variables
    numRx = len(trackSingleIn)
    numFr = 0
    for unitData in trackSingleIn:
        numFr = numFr + unitData['n_fr']

    # Set up data structure
    trackingMulti = dict(
        estimate         = [None]*numFr,
        forward          = [None]*numFr,
        reverse          = [None]*numFr,
        prediction       = [None]*numFr,
        meas_estimate    = [None]*numFr,
        meas_prediction  = [None]*numFr,
        time             = [None]*numFr,
        unit             = [None]*numFr,
        numFr            = numFr
    )

    # Aggregate list of times and receiver indices
    outList = []
    for unit in range(numRx):

        # Access list of time stamps
        timeList = trackSingleIn[unit]['meas']['time']

        # Append time stamp, frame index, and unit index to list
        outData = [(timeList[fr], fr, unit) for fr in range(len(timeList))]
        outList += outData

    # Sort list by timestamp
    detectionList = sorted(outList, key = lambda x: x[0])

    # Loop through detections
    for de in range(numFr):

        # Get unit and frame
        (deTime, deFrame, deUnit) = detectionList[de]

        # Calculate state offset
        radarPos = trackSingleIn[deUnit]['radar_pos']
        offset = np.matrix([[radarPos[0][0]],[0],[0],[radarPos[1][0]],[0],[0]])

        # Get state and variance information
        newState = trackSingleIn[deUnit]['estimate'][deFrame]['state'] + offset
        newCovar = trackSingleIn[deUnit]['estimate'][deFrame]['covar']

        # Initialize single frame data structure
        trackingMulti['meas_estimate'][de] = dict(
            state       = newState,
            covar       = newCovar,
            time        = deTime)
        trackingMulti['time'][de] = deTime
        trackingMulti['unit'][de] = deUnit

    # Return data structure
    return trackingMulti

# Multi unit, single pass processing
def TrackingMulti(trackMultiIn, trackParams, passDirection):

    # Unpack variables
    numFr = trackMultiIn['numFr']

    # Generate frame list
    if passDirection == 'forward':
        frList = range(0,numFr,1)
    elif passDirection == 'reverse':
        frList = range(numFr-1,-1,-1)
        
    # Set up field
    trackMultiIn[passDirection] = dict(
        estimate     = [None]*numFr,
        prediction   = [None]*numFr)


    # Loop through frames
    for fr in frList:

        # Check if track needs to be initialized
        if (passDirection == 'forward' and fr == 0) or (passDirection == 'reverse' and fr == numFr-1):

            # Use measurement as state prediction
            X_init = trackMultiIn['meas_estimate'][fr]['state']
            P_init = trackMultiIn['meas_estimate'][fr]['covar']

            # Save results
            trackMultiIn[passDirection] = SaveStepData(trackMultiIn[passDirection], fr, X_init, P_init, X_init, P_init, trackMultiIn['time'][fr])
            continue

        else:

            # Calculate time step since previous hit
            if passDirection == 'forward':
                lastHitFrame = fr-1
            else:
                lastHitFrame = fr+1
            Tm = trackMultiIn['time'][fr] - trackMultiIn['time'][lastHitFrame]


            ## Calculate Model Matrices

            # Measurement covariance matrix
            R = trackMultiIn['meas_estimate'][fr]['covar']

            # Process covariance matrix (NCA model)
            Q_1d = np.array([[(Tm**4)/4, (Tm**3)/2, (Tm**2)/2],
                            [(Tm**3)/2, (Tm**2),   (Tm)],
                            [(Tm**2)/2, (Tm),      1]])
            Q = np.asmatrix(np.concatenate((
                        np.concatenate((Q_1d*(trackParams['sigma_v'][0]**2), np.zeros(Q_1d.shape)), axis=1), 
                        np.concatenate((np.zeros(Q_1d.shape), Q_1d*(trackParams['sigma_v'][1]**2)), axis=1)), 
                        axis=0))

            # Kinematic process matrix (NCA model)
            F_1d = np.array([[1,    (Tm),   (Tm**2)/2],
                            [0,    1,      (Tm)],
                            [0,    0,      1]])
            F = np.asmatrix(np.concatenate((
                        np.concatenate((F_1d, np.zeros(F_1d.shape)), axis=1), 
                        np.concatenate((np.zeros(F_1d.shape), F_1d), axis=1)), 
                        axis=0))


            ## Prediction step

            # Predict kinematic vector
            X_pre = F * np.asmatrix(trackMultiIn[passDirection]['estimate'][lastHitFrame]['state'])

            # Predicted kinematic covariance
            P_pre = (F * (np.asmatrix(trackMultiIn[passDirection]['estimate'][lastHitFrame]['covar'])* F.T)) + Q

            ## Calculate measurement matrices

            # Measurement vector
            Z = np.asmatrix(trackMultiIn['meas_estimate'][fr]['state'])

            # Measurement matrix
            H = np.eye(6)

            # Measurement residual
            Z_res = Z - (H * X_pre)


            ## Estimation Step

            # Measurement residual covariance
            S = H * (P_pre * H.T) + R

            # Kalman matrix
            K = (P_pre * H.T) * S.I

            # Estimated kinematic vector
            X_est = X_pre + (K * Z_res)

            # Estimated kinematic covariance
            P_est = P_pre - (K * (H * P_pre))

            # Save data
            trackMultiIn[passDirection] = SaveStepData(trackMultiIn[passDirection], fr, X_est, P_est, X_pre, P_pre, trackMultiIn['time'][fr])

    return trackMultiIn

# Multi unit, both pass processing
def TrackingMultiBidirectional(trackMultiIn, trackParams):

    # Unpack variables
    numFr = trackMultiIn['numFr']

    # Run forward and backwards pass of tracking
    trackMultiIn = TrackingMulti(trackMultiIn, trackParams, 'forward')
    trackMultiIn = TrackingMulti(trackMultiIn, trackParams, 'reverse')
    
    # Loop through frames
    for fr in range(numFr):

        # Unpack structures
        estF = trackMultiIn['forward']['estimate'][fr]
        estR = trackMultiIn['reverse']['estimate'][fr]

        # Perform inverse variance weighting
        varSum = np.asmatrix((1 / np.diagonal(estF['covar'])) + (1 / np.diagonal(estR['covar']))).T
        stateSum = (estF['state'] / np.asmatrix(np.diagonal(estF['covar'])).T) + (estR['state'] / np.asmatrix(np.diagonal(estR['covar'])).T)

        varNew = np.diag((1 / varSum.T).tolist()[0])
        stateNew = stateSum / varSum

        # Save data back to struct
        trackMultiIn['estimate'][fr] = dict(
            state = stateNew,
            covar = varNew,
            pos   = [stateNew[i] for i in [0, 3]],
            vel   = [stateNew[i] for i in [1, 4]])

    # Return data structure
    return trackMultiIn

# Set up tracking parameters
def SetupParameters(instanceFolder):

    # Define defaults
    defaultParams = dict(
        max_vel = 250,
        max_acc = 1,
        sigma_v = (0.09, 0)
    )

    # Assemble file path
    paramFile = os.path.join(instanceFolder, 'params.json')

    # If file exists, read from file
    if os.path.exists(paramFile):
        with open(paramFile, 'r') as jsonFile:
            paramsIn = json.load(jsonFile)

    # Otherwise, save default parameters to file
    else:
        with open(paramFile, 'w') as jsonFile:
            json.dump(defaultParams, jsonFile, indent=4)
            paramsIn = defaultParams

    return paramsIn



### Main ###

def ProcessFiles(foldername):

    ### Read input data ###

    # Get file directories
    dirPath = os.path.dirname(os.path.realpath(__file__))
    inputPath = os.path.join(dirPath, 'Input', foldername)
    outputPath = os.path.join(dirPath, 'Output', foldername)
    instancePath = os.path.join(dirPath, 'Instance')

    # Get tracking parameters
    trackParams = SetupParameters(instancePath)

    # Discover files in directory 
    dataIn = []
    fileList = sorted(os.listdir(inputPath))
    filenameList = [name.split('.')[0] for name in fileList]

    for filename in fileList:
        fullFilename = os.path.join(inputPath, filename)
        mat = sio.loadmat(fullFilename)
        trackOut = mat['track_out'][0][0]
        dataIn.append(trackOut)

    numFiles = len(dataIn)

    # Unpack .mat file
    matKeys = {'range', 'vel', 'SNR', 'az', 'steer', 'radar_pos', 'time', 'n_fr'}
    trackData = [None]*numFiles

    # Set up new data structure
    for idx in range(numFiles):
        trackData[idx] = dict()
        for key in matKeys:
            trackData[idx][key] = dataIn[idx][key]



    ### Single unit tracking ###

    # Set up data structure
    trackSingle = [None]*numFiles

    # Loop through receivers
    for rx in range(numFiles):

        # Set up data structures
        meas = dict()
        for key in matKeys:
            if key != 'n_fr' and key != 'radar_pos':
                meas[key] = np.array([val[0] for val in trackData[rx][key]])

        trackSingle[rx] = dict(
            radar_pos   = trackData[rx]['radar_pos'],
            n_fr        = trackData[rx]['n_fr'][0][0],
            meas        = meas,
            estimate    = [])
        
        # Pass to function
        trackSingle[rx]['estimate'] = TrackingSingleUnitBidirectional(trackSingle[rx], trackParams)



    ### Multistatic processing ###

    # Run data fusion
    trackingMulti = DataFusion(trackSingle)

    # Perform multistatic tracking
    trackingMulti = TrackingMultiBidirectional(trackingMulti, trackParams)



    ### Results processing ###

    # Get number of frames from data structure
    numFr = trackingMulti['numFr']

    # Create general output folder if it doesn't exist
    if not os.path.exists(os.path.join(dirPath, 'Output')):
        os.makedirs(os.path.join(dirPath, 'Output'))

    # Create specific output folder
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)
    
    # Set up data headers 
    headers = (
        'Measurement Number', 'Origin Unit', 'Time',
        'Cross-Track Radar Position',           'Along-Track Radar Position',
        'Cross-Track Position',                 'Along-Track Position',
        'Cross-Track Velocity',                 'Along-Track Velocity',
        'Cross-Track Acceleration',             'Along-Track Acceleration',
        'Cross-Track Position Variance',        'Along-Track Position Variance',
        'Cross-Track Velocity Variance',        'Along-Track Velocity Variance',
        'Cross-Track Acceleration Variance',    'Along-Track Acceleration Variance',
    )
    
    # Generate result matrix
    stateEstimate = [None]*numFr
    for fr in range(numFr):
        stateEstimate[fr] = \
            [fr+1] \
            + [trackingMulti['unit'][fr]+1] \
            + [trackingMulti['time'][fr]] \
            + [0, 0] \
            + [float(trackingMulti['estimate'][fr]['state'][ind]) for ind in [0, 3, 1, 4, 2, 5]] \
            + [float(trackingMulti['estimate'][fr]['covar'][ind, ind]) for ind in [0, 3, 1, 4, 2, 5]]

    # Save multistatic results
    with open(outputPath + '/multi.csv', mode='w', newline='') as csv_out:
        csvWriter = csv.writer(csv_out, delimiter=',', quotechar='"')
        csvWriter.writerow(headers)
        csvWriter.writerows(stateEstimate)

    # Save single unit results
    for rx in range(numFiles):
        with open(os.path.join(outputPath, filenameList[rx] + '.csv'), mode='w', newline='') as csv_out:
            
            # Align data for CSV input
            numFr = trackSingle[rx]['n_fr']
            singleEstimate = [None]*numFr
            for fr in range(numFr):
                singleEstimate[fr] = \
                [fr+1] + [rx] + [trackSingle[rx]['estimate'][fr]['time']] \
                + [float(trackSingle[rx]['radar_pos'][ind]) for ind in [0,1]] \
                + [float(trackSingle[rx]['estimate'][fr]['cart'][0] + trackSingle[rx]['radar_pos'][0])] \
                + [float(trackSingle[rx]['estimate'][fr]['cart'][1] + trackSingle[rx]['radar_pos'][1])] \
                + [float(trackSingle[rx]['estimate'][fr]['state'][ind]) for ind in [1, 4, 2, 5]] \
                + [float(trackSingle[rx]['estimate'][fr]['covar'][ind,ind]) for ind in [0, 3, 1, 4, 2, 5]]

            # Write to CSV file
            csvWriter = csv.writer(csv_out, delimiter=',', quotechar='"')
            csvWriter.writerow(headers)
            csvWriter.writerows(singleEstimate)


# Main method
if __name__ == '__main__':
    
    # Gather input path
    dirPath = os.path.dirname(os.path.realpath(__file__))
    inputPath = os.path.join(dirPath, 'Input')

    # Process all files
    for folder in os.listdir(inputPath):
        ProcessFiles(folder)

    
