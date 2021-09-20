%% SEMTA Radar System - Main Simulation Loop
%{

    Sean Holloway
    SEMTA Main Simulation Loop
    
    This file specifies performs simulation, signal processing, detection,
    data processing, multistatic processing, and results collection for
    SEMTA system. 

    Use script 'FullSystem.m' to run scenarios.
    
%}

%% Main Loop

% Start timing for estimation
timeStart(scenario);

% Loop through radar units
for unit = 1:scenario.multi.n_re
    
    % Set current unit flag
    scenario.flags.unit = unit;
    
    % Loop through simulation frames
    for frame = 1:scenario.multi.n_fr
        
        % Set current frame flag
        scenario.flags.frame = frame;
        
        %% Beam Steering Setup
        
        % Set beam steering direction
        scenario.multi.steering_angle(frame, unit) = BeamsteeringUpdate(scenario, true);
        
        %% Radar Simulation (Single frame)
        
        % Run simulation to retrieve fast time x slow time Rx signal
        scenario = RadarSimulation(scenario);
        
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
        
        % Check for mode changes
        scenario = ModeCheck(scenario, true);
        
        %% Read Out Progress
        
        % Read out target information
        readOut(scenario);
        
        % Read out current progress in simulation
        frameUpdate(scenario, 1);
        
        % Estimate remaining time in simulation
        timeUpdate(scenario, 5, 'frames');
        
    end
    
    % Reset parameters for new unit
    unitReset(scenario);
    
    % Read out current proress in simulation
    unitUpdate(scenario, 1);
    
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

% Perform multilateration on list of detected targets
scenario.tracking_multi = Tracking_Multi(scenario);

% Visualize multilateration result
% viewMultilateration(scenario);

%TEMP
MultiPlot_Scratch

%% Results Processing

% Save tracking data for offline processing
track_single = scenario.tracking_single;
track_multi = scenario.tracking_multi;
multi = scenario.multi;
traj = scenario.traj;
rs = scenario.radarsetup;
save(['Results/Tracking Results/', scenario.simsetup.filename, '.mat'], 'track_single', 'track_multi', 'multi', 'traj', 'rs');
track = [];
multi = [];
traj = [];
rs = [];

% Estimate error of results
% scenario.results = ErrorEstimation(scenario);

% View plots of errors
% viewErrors(scenario);

