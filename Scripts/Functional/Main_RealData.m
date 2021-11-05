%% SEMTA Radar System - Main Simulation Loop
%{

    Sean Holloway
    SEMTA Real Data Processing
    
%}

%% Main Loop

% Start timing for estimation
startProgressTimer(scenario);

% Get list of input files
file_list = dir(fullfile('Input', scenario.simsetup.input_subfolder, '*.bin'));

% Loop through
for file_ind = 1:length(file_list)
    
    % Set current file name
    scenario.flags.filename = file_list(file_ind).name;
    
    % Set out-of-data flag
    scenario.flags.out_of_data = false;    

    % Loop until out of data
    while ~scenario.flags.out_of_data

        %% Read in radar data

        % Set current frame flag
        scenario.flags.frame = scenario.flags.frame + 1;

        % Read input file
        scenario.rx_sig = RealDataInput(scenario);

        %% Signal Processing (Single frame)

        % Perform signal processing on received signal
        scenario.cube = SignalProcessing(scenario);

        %% Data Processing (Single frame)

        % Perform radar detection
        scenario.detection = Detection(scenario);

        % Perform single unit tracking
        scenario = Tracking_SingleUnit(scenario);

        % Store and clear target information
        storeMulti(scenario);

        %% Read Out Progress

        % Read out target information
        readOut(scenario);

        % Read out current progress in simulation
        frameUpdate(scenario, 1);

        % Estimate remaining time in simulation
        updateProgressTimer(scenario, 5, 'frames');

    end

    % Save single unit tracking
    if scenario.simsetup.save_track_single
        SaveTrackingSingle(scenario, unit);
    end

    % Post-process tracking
    if scenario.radarsetup.tracking_single.bi_single
        scenario = Tracking_SingleUnit_Bidirectional(scenario);
    end

    end
    

%% Visualize Monostatic Results

% View Range-Slow Time heat map
% viewRangeCube(scenario);

% View Range-Doppler heat map
% viewRDCube(scenario);

% View radar detections
% viewDetections(scenario);

% View tracking results
% viewTrackingSingle(scenario);

% View SNR of each radar unit
% viewSNR(scenario);


%% Multistatic Processing

% Fuse data between multiple estimations
scenario.tracking_multi = DataFusion(scenario);

% Perform Kalman filter tracking on fused sensor data
if scenario.radarsetup.tracking_single.bi_multi
    scenario.tracking_multi = Tracking_Multi_Bidirectional(scenario);
else
    scenario.tracking_multi = Tracking_Multi(scenario, 'forward');
end

% Visualize multilateration result
viewTrackingMulti(scenario);

%% Results Processing

% Estimate error of results
% scenario.results = ErrorEstimation(scenario);

% View plots of errors
% viewErrors(scenario);

