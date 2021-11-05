function [detection] = Detection_FixedPoint(scenario)
%DETECTION_SEMTA Performs target detection for SEMTA project
%   Takes scenario object as input, provides scenario.detection object as
%   output, containing information about detected targets.

%% Unpack Variables

radarsetup = scenario.radarsetup;
cube = scenario.cube;

%% Perform Detection

% Estimate noise power
detection.noise_pow = pow2db(median(mean(sum(cube.pow_cube, 4), 1), 'all'));

% Generate detection map
sz = size(cube.pow_cube);
sz = sz(1:2);

% Load in offsets
filein = load('Reference/CFAROffsets.mat');
offsetList = filein.offsetList;

% Calculate threshold factor
N = length(offsetList);
threshFactor = N * (radarsetup.Pfa ^ (-1/N) - 1);

% Set variables
Nguard_rng = radarsetup.num_guard(1);
Nguard_dop = radarsetup.num_guard(2);
Ntrain_rng = radarsetup.num_train(1);
Ntrain_dop = radarsetup.num_train(2);
Nr = sz(1);
Nd = sz(2);
maxNumOutputs = 65536;

% Branch depending on integration type
switch radarsetup.int_type
    case 'binary'
        num_loops = radarsetup.cpi_fr;
    case 'incoherent'
        num_loops = 1;
end

detection.single_ind_list = cell(num_loops, 1);
detection.pow_list = cell(num_loops, 1);

% Loop across CPIs
for loop = 1:num_loops
    
    % Branch depending on integration type
    switch radarsetup.int_type
        case 'binary'
            
            % Set cube to examine
            rd_cube = sum(cube.pow_cube(:,:,loop,:), 4);
            
            % Estimate noise power
            detection.noise_pow = pow2db(median(mean(sum(cube.pow_cube, 4), 1), 'all'));

        case 'incoherent'
            
            % Set cube to examine
            rd_cube = sum(cube.pow_cube, [3 4]);
            
            % Estimate noise power
            detection.noise_pow = pow2db(median(mean(rd_cube, 1), 'all'));

    end
    
    
    %% Perform CFAR Detection
    
    % Call fixed point function (binary executable)
    det_list = CFARDetectionFP_wrapper_fixpt_mex( ...
        'CFARDetectionFP_wrapper_fixpt', rd_cube, ...
        offsetList, maxNumOutputs, threshFactor, ...
        Nr, Nd, Ntrain_rng, Ntrain_dop, Nguard_rng, Nguard_dop);
    
    % Call fixed point function (wrapper)
%     det_list = CFARDetectionFP(rd_cube, ...
%         offsetList, maxNumOutputs, threshFactor, ...
%         Nr, Nd, Ntrain_rng, Ntrain_dop, Nguard_rng, Nguard_dop);
    
    % Save single loop detection list
    detection.single_ind_list{loop} = sort(nonzeros(det_list));
    
    % Perform range migration compensation
    if radarsetup.vel_comp && strcmp(radarsetup.int_type, 'binary')
        
        % Loop through detection indices
        compensated_list = [];
        for n = 1:length(detection.single_ind_list{loop})
            
            % Convert to subscripts
            [rngI, dopI] = ind2sub(sz, detection.single_ind_list{loop}(n));
            
            % Determine number of range bins covered
            binsPerCPI = cube.vel_axis(dopI) * radarsetup.cpi_time / cube.range_res;
            offsetBins = round(binsPerCPI * ((1:num_loops)-loop));
            
            % Generate subscripts
            rngIdxComp = rngI + offsetBins;
            dopIdxComp = dopI * ones(size(rngIdxComp));
            
            % Add linear index to list
            linIdxComp = sub2ind(sz, rngIdxComp, dopIdxComp);
            compensated_list = [compensated_list; linIdxComp(:)]; 
        end
        
        % Remove duplicates and update saved list
        detection.single_ind_list{loop} = unique(compensated_list);
    end
    
    % Generate power list
    [rngI, dopI] = ind2sub(sz, detection.single_ind_list{loop});
    for n = 1:2
        linI = sub2ind(size(cube.pow_cube), rngI, dopI, loop*ones(size(rngI)), n*ones(size(rngI)));
        detection.pow_list{loop}(:,n) = cube.pow_cube(linI);
    end
    
end
    
    
%% Binary Integration
switch radarsetup.int_type
    case 'binary'
        
        % Concatenate all result lists
        concat_list = [];
        concat_pow_list = [];
        for n = 1:num_loops
            concat_list = [concat_list; detection.single_ind_list{n}];
            concat_pow_list = [concat_pow_list; detection.pow_list{n}];
        end
        unique_list = unique(concat_list);
        
        % Loop through all unique detections
        detection.combined_ind_list = [];
        avg_list = nan(length(unique_list), 2);
        for n = 1:length(unique_list)
            
            % Count instances
            ind = unique_list(n);
            count = sum(concat_list == ind);
            
            % Continue if not enough detections
            if count < min(radarsetup.det_m, radarsetup.cpi_fr)
                continue;
            end
            
            % Update lists
            detection.combined_ind_list(end+1) = ind;
            avg_list(n,:) = sum(concat_pow_list(concat_list == ind)) / count;
            
        end
        
        % Remove NaNs
        avg_list = avg_list(~isnan(avg_list(:,1)),:);
        
    case 'incoherent'
        
        % Use CFAR result for integrated cube
        detection.combined_ind_list = detection.single_ind_list{1};
        
        % Generate power cube
        avg_list = detection.pow_list{1};
end

% Determine if any target is detected
detection.detect_logical = ~isempty(detection.combined_ind_list);



%% Find connected components

% Initialize labels
label_list = nan(size(detection.combined_ind_list));
equiv_list = {};

% Loop through list of detections (First pass)
for n = 1:length(detection.combined_ind_list)
    
    % Calculate subscript indices
    lin_ind = detection.combined_ind_list(n);
    [r_ind, d_ind] = ind2sub(sz, lin_ind);
    
    % Initialize neighbor list
    neighbor_labels = [];
    neighbor_inds = [...
         1, -1; ...
         0, -1; ...
        -1, -1; ...
        -1,  0];
    neighbor_inds = neighbor_inds + [r_ind, d_ind];
    
    % Check for out of bounds and convert to linear
    for m = 1:4
        
        % Check for bounds
        if (neighbor_inds(m,1) < 1) || (neighbor_inds(m,1) > sz(1)) || (neighbor_inds(m,2) < 1)
            continue;
        else
            
            % Get linear index
            lin = sub2ind(sz, neighbor_inds(m,1), neighbor_inds(m,2));
            
            % Check if label has detection
            list_ind = find(detection.combined_ind_list == lin, 1);
            neighbor_labels = [neighbor_labels; label_list(list_ind)];
        end
    end
    
    % If no neighbors have detections, add new label
    if isempty(neighbor_labels)
        new_label = length(equiv_list) + 1;
        equiv_list{new_label} = new_label;
        label_list(n) = new_label; 
        continue;
    end
    
    % If one detection, use that label for CUT
    if length(neighbor_labels) == 1
        label_list(n) = neighbor_labels;
    
    % If multiple detections, use lowest label and add equivalencies
    else
        
        new_label = min(neighbor_labels);
        label_list(n) = min(neighbor_labels);
        
        for k = 1:length(neighbor_labels)
            equiv_list{neighbor_labels(k)}(end+1) = new_label;
        end
    end
    
end

% Consolidate equivalences
for n = 1:length(equiv_list)
    for m = (n+1):length(equiv_list)
        if ~isempty(intersect(equiv_list{n}, equiv_list{m}))
            equiv_list{n} = unique(union(equiv_list{n}, equiv_list{m}));
            equiv_list{m} = equiv_list{n};
        end
    end
end


% Loop through list of detections (Second pass)
for n = 1:length(detection.combined_ind_list)
    
    % Assign lowest label to true detections
    label_list(n) = min(equiv_list{label_list(n)});
    
end

%% Separate data by regions

% Generate region struct
unique_list = unique(label_list);
regions = struct( ...
    'pixelIdxList',     cell(length(unique_list),1), ...
    'rngIdxList',       cell(length(unique_list),1), ...
    'dopIdxList',       cell(length(unique_list),1), ...
    'powerList',        cell(length(unique_list),1), ...
    'ratioList',        cell(length(unique_list),1), ...
    'weightedCentroid', cell(length(unique_list),1));

% Calculate region information
for n = 1:length(regions)
    
    % Lists of region indices
    regions(n).pixelIdxList = detection.combined_ind_list(label_list == unique_list(n));
    regions(n).pixelIdxList = regions(n).pixelIdxList(:);
    [regions(n).rngIdxList, regions(n).dopIdxList] = ind2sub(sz, regions(n).pixelIdxList);
    
    % Derived lists of power values
    regionAvgList = avg_list(label_list == unique_list(n),:);
    regions(n).powerList = sum(regionAvgList,2);
    regions(n).ratioList = diff(sqrt(regionAvgList), 1, 2) ./ sum(sqrt(regionAvgList), 2);
    
    % Centroid values
    powerSum = sum(regions(n).powerList);
    regions(n).weightedCentroid(1) = sum(regions(n).rngIdxList .* regions(n).powerList) / powerSum;
    regions(n).weightedCentroid(2) = sum(regions(n).dopIdxList .* regions(n).powerList) / powerSum;
    regions(n).weightedCentroid(3) = sum(regions(n).ratioList .* regions(n).powerList) / powerSum;
    
end

%% Estimate Target Coordinates

% Generate list of detection coordinates
detection.detect_list.range = [];
detection.detect_list.vel = [];
detection.detect_list.az = [];
detection.detect_list.cart = [];
detection.detect_list.SNR = [];
detection.detect_list.num_detect = length(regions);

% Load offset curve
if radarsetup.range_off
    loadIn = load('Results\Error Curves\RangeErrorCurveFixedWindow.mat', 'offsetAxis', 'offsetCurve');
    offsetCurve = loadIn.offsetCurve;
    offsetAxis = loadIn.offsetAxis;
end

% Determine Centroid of azimuth-elevation slice
for n = 1:length(regions)
    
    % Test coarse range calculation
    rangeMeas = interp1(cube.range_axis, regions(n).weightedCentroid(1));
    if (rangeMeas < radarsetup.rng_limits(1)) || (rangeMeas > radarsetup.rng_limits(2))
        detection.detect_list.num_detect = detection.detect_list.num_detect - 1;
        continue;
    end
    
    % Estimate angle-of-arrival using amplitude comparison monopulse
    monopulse_aoa = (cosd(scenario.multi.steering_angle(scenario.flags.frame, scenario.flags.unit))^-2) * ...
        regions(n).weightedCentroid(3) * radarsetup.beamwidth / radarsetup.mono_coeff;
    detection.detect_list.az(end+1) = monopulse_aoa ...
        + scenario.multi.steering_angle(scenario.flags.frame, scenario.flags.unit);
    
    % Calculate range estimate and correction
    if radarsetup.range_off
        nearest = scenario.cube.range_res * floor(rangeMeas / scenario.cube.range_res);
        resid = rangeMeas - nearest;
        offset = interp1(offsetAxis, offsetCurve, resid, 'linear', 'extrap');
        rangeCalc = nearest + offset;
    else
        rangeCalc = interp1(cube.range_axis, regions(n).weightedCentroid(1));
    end
        
    % Store direct coordinates
    detection.detect_list.range(end+1) = rangeCalc;
    detection.detect_list.vel(end+1) = interp1(cube.vel_axis, regions(n).weightedCentroid(2));
    
    % Store derived coordinates
    detection.detect_list.cart(:,end+1) = detection.detect_list.range(end) * ...
        [cosd(detection.detect_list.az(end)); sind(detection.detect_list.az(end))];
    
    % Store SNR
    detection.detect_list.SNR(end+1) = 10*log10(max(regions(n).powerList, [], 'all')) ...
        - detection.noise_pow;
end

% Write to true/false detection value
detection.detect_logical = detection.detect_list.num_detect > 0;

end