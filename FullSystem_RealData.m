%% SEMTA Radar System
%{

    Sean Holloway
    SEMTA (Sea-Skimming Missile Tracking Radar Array) System
    MATLAB Simulation & Processing

    This shell file runs successive scripts and gauges progress.
%}

%% Housekeeping, Timing, and Path Management

% Add current folders to path
addpath(genpath(pwd));

% Run all start-of-process tasks
StartProcess;

%% Initialize Scenario Object

% Initialization
scenario = RadarScenario;

%% Setup Structures for Simulation

% Set up simulation and processing parameters
SetupSimulation

% Set up real data input parameters
SetupRealData

%% Run Simulation

% Perform main loop of simulation, signal and data processing
Main_RealData

%% Save Figures and Data

% Run all end-of-simulation tasks
EndProcess




