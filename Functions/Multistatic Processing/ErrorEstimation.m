function [results] = ErrorEstimation(scenario)
%ERRORESTIMATION Calculates error between estimated results and true
%trajectory
%   Takes scenario object as input and returns scenario.results as output

%% Unpack Variables

results = scenario.results;
ts = scenario.tracking_single;
tm = scenario.tracking_multi;
multi = scenario.multi;

%% Calculate Multistatic Error

% Get true target positions
true_positions = scenario.traj.pos(scenario.traj, tm.time);
true_positions = true_positions(1:2,:);

% Get measurement locations
track_positions = nan(2,tm.num_fr);
for de = 1:tm.num_fr
    track_positions = tm.track_estimate{de}.pos;
end

% Calculate error
multistatic_error = track_positions - true_positions;


%% Calculate Single Unit Error

% Set up output structure
single_error = cell(multi.n_re, 1);

% Loop through radar units
for re = 1:multi.n_re
    
    % Initialize structures
    num_hits = sum(ts{re}.hit_list);
    true_positions = nan(2,num_hits);
    track_positions = nan(2,num_hits);
    
    % Loop through detections
    hit_de = 0;
    for de = 1:length(ts{re}.hit_list)
        
        % Check for detection
        if ~ts{re}.hit_list(de)
            continue;
        end
        
        % Increment index
        hit_de = hit_de + 1;
    
        % Get time of detection
        currentTime = multi.time{re}(de);

        % Get true target position
        currentPosition = scenario.traj.pos(scenario.traj, currentTime);
        true_positions(:,hit_de) = currentPosition(1:2);

        % Get measurement location
        currentTrack = ts{re}.estimate{de}.cart + multi.radar_pos(1:2,re);
        track_positions(:,hit_de) = currentTrack;
        
    end
    
    % Calculate error
    single_error{re} = track_positions - true_positions;
        
end


%% Pack Variables

results.multistatic = multistatic_error;
results.single = single_error;

end

