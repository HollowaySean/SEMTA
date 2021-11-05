%% SEMTA Radar System - Example Radar Initialization File
%{

    Sean Holloway
    SEMTA Real Data Init File
    
%}

%% Processing Parameter Setup

save_format.list = {'.png','.fig'};

% Radar simulation and processing setup
scenario.simsetup = struct( ...
    ...
    ... % Simulation Properties
    'input_subfolder',      'Example', ...         % Filename of input real data file
    'readout',              true, ...                   % Read out target data T/F
    'send_alert',           false, ...                  % Send email alert T/F
    'attach_zip',           false, ...
    'alert_address',        'hollowayseanm@gmail.com', ...
    ...                                                 % Email address for status updates
    'par_cfar',             false, ...                  % Use parallel processing for CFAR T/F
    'filename',             'LiveServerTest', ...       % Filename to save data as
    'timestampfile',        true, ...                   % Add timestamp to file name
    'save_format',          save_format, ...            % File types to save figures
    'save_figs',            false, ...                  % Save figures T/F
    'save_mat',             false, ...                  % Save mat file T/F
    'reduce_mat',           false, ...                  % Reduce mat file for saving
    'save_track',           false, ...                  % Save tracking T/F
    'save_track_single',    true);                      % Save single unit tracking T/F

% Append timestamp to filename
if scenario.simsetup.timestampfile
    scenario.simsetup.filename = [scenario.simsetup.filename, '_', datestr(now, 'mmddyy_HHMM')];
end

%% Radar Parameter Setup

% Radar simulation and processing setup
scenario.radarsetup = struct( ...
    ...
    ... % Waveform Properties
    'f_c',      9.45e9, ...             % Operating frequency in Hz
    'f_s',      25e6, ...               % ADC sample frequency in Hz
    't_p',      10e-6, ...              % Chirp duration in seconds
    'bw',       10e6, ...               % Bandwidth of chirp
    'prf',      20e3, ...               % Pulse repetition frequency in Hz
    'n_p',      1024, ...               % Number of pulses to simulate
    'cpi_fr',   5, ...                  % Number of CPI per frame
    ...
    ... % Transceiver Properties
    'n_ant',        16, ...             % Number of elements in antenna array
    'range_off',    true, ...           % Correct range with offset function
    'beamwidth',    6.335, ...          % Antenna beamwidth in degrees
    'mono_coeff',   -1.4817, ...        % Coefficient in monopulse AoA linear approximation
    ...
    ... % Processing Properties
    'r_win',        'hamming', ...      % Type of window for range processing
    'd_win',        'none', ...         % Type of window for doppler processing
    ...
    ... % Detection Properties
    'detect_type',  'CFAR', ...         % Choose 'CFAR' or 'threshold'
    'int_type',     'binary', ...       % Choose 'binary' or 'incoherent'
    'thresh',       [], ...             % Threshold in dB for threshold detection
    'Pfa',          1e-6, ...           % Probability of false alarm for CFAR
    'num_guard',    [3 3], ...          % Number of R-D guard cells for CFAR detection
    'num_train',    [15 2], ...         % Number of R-D training cells for CFAR detection
    'rng_limits',   [500, 7000], ...    % Min/max range values, to avoid false alarms
    'vel_comp',     true, ...           % T/F compensate for range bin migration in binary integration
    'det_m',        2);                 % M for m-of-n processing

% Tracking Parameters
tracking = struct( ...
    'max_vel',           250, ...            % Maximum possible speed for coarse gating
    'max_acc',           1, ...              % Maximum possible acceleration for uncertainty estimation
    'dist_thresh',       Inf, ...13.8, ...           % Mahanalobis distance threshold for fine gating
    'miss_max',          5, ...              % Number of misses required to inactivate track
    'EKF',               false, ...          % T/F use extended Kalman filter
    'sigma_v',           [0.09, 0], ...       % XY target motion uncertainty 
    'sigma_v_multi',     [0.09, 0], ...       % Motion uncertainty for multilaterated tracking
    'bi_multi',          true, ...        % Use bidirectional tracking?
    'bi_single',         true, ...
    'limitSensorFusion', true);         % Only take top two sensor results

scenario.radarsetup.tracking_single = tracking;

% Calculate derived parameters
scenario.radarsetup.pri = 1/scenario.radarsetup.prf;
scenario.radarsetup.cpi_time = ...
    scenario.radarsetup.pri * scenario.radarsetup.n_p;
scenario.radarsetup.frame_time = ...
    scenario.radarsetup.cpi_time* scenario.radarsetup.cpi_fr;





