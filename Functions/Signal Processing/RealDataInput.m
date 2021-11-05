function [scenario] = RealDataInput(scenario)
%REALDATAINPUT Reads input from real data
%   NOTE: THIS FUNCTION SHOULD BE WRITTEN AFTER DATA FORMAT IS KNOWN

% To whoever is tasked with writing this function in the future:
%
% This function uses as input 'scenario.flags.filename', along with
% timing parameters from 'scenario.radarsetup'. 
%
% The output should be "rx_sig" in the format used by the function
% 'SignalProcessing'. This is an array of (num_samples) x (num_chirps *
% num_cpi) x (num_rx_channels). For example, for the case of 1250 samples
% per chirp, 1024 chirps per CPI, 5 CPI per frame, and 2 Rx channels, this
% would be an array of size 1250x5120x2.
%
% This script should also set the 'out_of_data' boolean in
% 'scenario.flags', signifying that the loop should break.
%
% If you have any further questions, feel free to email me at
% hollowayseanm@gmail.com, and I will get back with some advice.
%
% - Sean Holloway

% Read out current file
fprintf('Processing file %s, frame %d.\n\n', scenario.flags.filename, scenario.flags.frame);

% Get full file path
full_filename = fullfile('Input', scenario.simsetup.input_subfolder, scenario.flags.filename);

% THROW ERROR INCOMPLETE FUNCTION
error('RealDataInput function not implemented, see text in file Functions/Signal Processing/RealDataInput.m');

% Load file, something like this
file_id = fopen(full_filename, 'rb');
data_in = fread(file_id, sizeofinput, 'int32', skipValue);
fclose(file_id);

% Placeholder
scenario.rx_sig = nan;
scenario.flags.out_of_data = false;
end

