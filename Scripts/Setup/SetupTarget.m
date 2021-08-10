%% SEMTA Radar System - Target Initialization File
%{

    Sean Holloway
    SEMTA Target Init File
    
    This file specifies the properties of the target used in the SEMTA 
    simulation system.

    Use script 'FullSystem.m' to run scenarios.
    
%}

%% Target RCS Setup

% Options setup
scenario.rcs = struct( ...
    ...
    ... % RCS options
    'rcs_model',    'model', ...     % Set 'model' or 'constant'
    'ave_rcs',      -20, ...             % Target RCS in dBm^2
    ...
    ... % Model options
    'dim',      [6; 3; 0], ...          % [x; y; z] size of target
    'n_sc',     50, ...                 % Number of point scatterers
    'res_a',    0.1, ...                % Angle resolution in degrees
    'freq',     9e9:10e6:10e9);         % Frequency range to model

% Run RCS model
scenario.rcs = TargetRCSModel(scenario.rcs);

% View RCS results
% viewRCSFreq(scenario);
% viewRCSAng(scenario);

%% Target Trajectory Setup

% Options setup
scenario.traj = struct( ...
    ...
    ... % Trajectory model options
    'alt',      100, ...                % Altitude in meters
    'yvel',     400, ...                % Along track velocity in m/s
    'exc',      100, ...                % Excursion distance in meters
    'per',      0.1, ...                % Excursion period (Nominally 0.05 to 0.2)
    ...
    ... % Static options
    'pos_st',   [0; 0; 0], ...          % Position input if 'static' is used
    'vel_st',   [0; 0; 0], ...          % Velocity input if 'static' is used
    ...
    ... % Model options
    'model',    'static');              % Set 'static' or 'model'

% Run Trajectory model
scenario.traj = TrajectoryModel(scenario.traj);

% View Trajectory
% viewTraj(scenario);
