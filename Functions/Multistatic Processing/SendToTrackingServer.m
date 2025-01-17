function [] = SendToTrackingServer(scenario, unitsToProcess)
%SENDTOTRACKINGSERVER Sends tracking data to post-processing server
%   Attaches single unit tracking data to HTTP POST request and attempts to
%   send to post-processing server

%% Ping post-processing server

% Create HTTP GET request object
request = matlab.net.http.RequestMessage;
uri = matlab.net.URI(['http://', scenario.simsetup.server_IP, '/']);
options = matlab.net.http.HTTPOptions('ConnectTimeout',20);

% Send request
try
    res = request.send(uri, options);
catch
    warning('Server not reachable. Sending failed.');
    return;
end

% Interpret result
if res.StatusCode ~= matlab.net.http.StatusCode(200)
    warning('Server not reachable. Sending failed.');
    return;
else
    disp('Successfully pinged post-processing server.');
end

%% Loop through units

for unit = unitsToProcess
    
    % Determine tracking results filenmae
    filename = ['Results/Tracking/', scenario.simsetup.filename, sprintf('/Unit_%d.mat', unit)];
    
    % Check if file exists
    if ~isfile(filename)
        fprintf('No file data found for unit %d.\n', unit);
        return;
    end
    
    % Assemble file provider object
    file_provider = matlab.net.http.io.FileProvider(filename);
    form_provider = matlab.net.http.io.MultipartFormProvider(...
        "test_id",      scenario.simsetup.filename, ...
        "file",         file_provider);
    
    % Create HTTP POST request
    request = matlab.net.http.RequestMessage('POST', [], form_provider);
    
    % Send request
    try
        res = request.send(uri, options);
    catch
        warning('Failed to upload to post-processing server.');
        return;
    end
    
    % Interpret result
    switch res.StatusCode
        case matlab.net.http.StatusCode(201)
            fprintf('Successfully uploaded unit %d tracking data post-processing server.\n', unit);
            continue;
        case matlab.net.http.StatusCode(403)
            warning('Unit %d data already exists on server. Skipping.', unit);
        otherwise
            warning('Failed to upload to post-processing server.\nReturned following status code:\n');
            disp(res.Body.Data)
            return;
    end
    
end


end

