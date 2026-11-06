% BEV closed-loop prototype in base Simulink.
% Generates ev_bev_closed_loop.slx and runs a synthetic torque-inhibition test.
% Requires Simulink. No motor/vehicle/ISO 26262 compliance is implied.

if isempty(ver('simulink'))
    error('Simulink is not installed or licensed in this MATLAB environment.');
end

model = 'ev_bev_closed_loop';
if bdIsLoaded(model)
    close_system(model, 0);
end
if exist([model '.slx'], 'file')
    error('%s.slx already exists in this folder. Move or rename it before generating.', model);
end

new_system(model);
open_system(model);
set_param(model, 'StopTime', '25', 'Solver', 'ode45', 'MaxStep', '0.02');

% Simplified vehicle and PI parameters (illustrative only).
mass_kg = 1450;
wheel_radius_m = 0.31;
final_drive = 9;
drivetrain_eff = 0.90;
rolling_drag_N_per_mps = 80; % lumped longitudinal resistance
kp = 16;                    % torque per speed error
ki = 4;                     % torque per integral speed error
max_torque_nm = 200;

% Fixed block locations, so the diagram is readable in Simulink.
add_block('simulink/Sources/Step', [model '/Target speed'], 'Position', [35 100 95 140], ...
    'Time', '0.5', 'Before', '0', 'After', '15');
add_block('simulink/Math Operations/Sum', [model '/Speed error'], 'Position', [140 100 175 140], ...
    'Inputs', '+-');
add_block('simulink/Math Operations/Gain', [model '/Kp'], 'Position', [225 65 290 105], ...
    'Gain', num2str(kp));
add_block('simulink/Continuous/Integrator', [model '/Integral error'], 'Position', [225 160 270 200]);
add_block('simulink/Math Operations/Gain', [model '/Ki'], 'Position', [320 160 385 200], ...
    'Gain', num2str(ki));
add_block('simulink/Math Operations/Sum', [model '/PI torque'], 'Position', [425 108 460 147], ...
    'Inputs', '++');
add_block('simulink/Discontinuities/Saturation', [model '/Torque demand limit'], ...
    'Position', [500 108 590 147], 'UpperLimit', num2str(max_torque_nm), 'LowerLimit', '0');

% Safety surrogate: at 12 s an injected fault reduces allowed torque to zero.
% This is a test injection, NOT a real C++ supervisor integration.
add_block('simulink/Sources/Step', [model '/Safety torque cap'], 'Position', [485 235 555 275], ...
    'Time', '12', 'Before', num2str(max_torque_nm), 'After', '0');
add_block('simulink/Math Operations/MinMax', [model '/Applied torque min'], ...
    'Position', [635 115 675 170], 'Function', 'min', 'Inputs', '2');
add_block('simulink/Math Operations/Gain', [model '/Wheel force conversion'], ...
    'Position', [735 120 830 160], ...
    'Gain', num2str(final_drive*drivetrain_eff/wheel_radius_m, '%.12g'));
add_block('simulink/Math Operations/Sum', [model '/Net longitudinal force'], ...
    'Position', [880 120 925 160], 'Inputs', '+-');
add_block('simulink/Math Operations/Gain', [model '/Inverse mass'], ...
    'Position', [970 120 1055 160], 'Gain', num2str(1/mass_kg, '%.12g'));
add_block('simulink/Continuous/Integrator', [model '/Vehicle speed mps'], ...
    'Position', [1100 120 1150 160], 'InitialCondition', '0');
add_block('simulink/Math Operations/Gain', [model '/Speed dependent resistance'], ...
    'Position', [1130 245 1220 285], 'Gain', num2str(rolling_drag_N_per_mps));

add_block('simulink/Sinks/To Workspace', [model '/Log vehicle speed'], ...
    'Position', [1250 100 1355 130], 'VariableName', 'vehicle_speed_ts', 'SaveFormat', 'Timeseries');
add_block('simulink/Sinks/To Workspace', [model '/Log applied torque'], ...
    'Position', [730 35 840 65], 'VariableName', 'applied_torque_ts', 'SaveFormat', 'Timeseries');
add_block('simulink/Sinks/To Workspace', [model '/Log target speed'], ...
    'Position', [135 15 235 45], 'VariableName', 'target_speed_ts', 'SaveFormat', 'Timeseries');
add_block('simulink/Sinks/To Workspace', [model '/Log safety cap'], ...
    'Position', [600 300 710 330], 'VariableName', 'safety_cap_ts', 'SaveFormat', 'Timeseries');

% Connections.
add_line(model, 'Target speed/1', 'Speed error/1', 'autorouting', 'on');
add_line(model, 'Target speed/1', 'Log target speed/1', 'autorouting', 'on');
add_line(model, 'Speed error/1', 'Kp/1', 'autorouting', 'on');
add_line(model, 'Speed error/1', 'Integral error/1', 'autorouting', 'on');
add_line(model, 'Integral error/1', 'Ki/1', 'autorouting', 'on');
add_line(model, 'Kp/1', 'PI torque/1', 'autorouting', 'on');
add_line(model, 'Ki/1', 'PI torque/2', 'autorouting', 'on');
add_line(model, 'PI torque/1', 'Torque demand limit/1', 'autorouting', 'on');
add_line(model, 'Torque demand limit/1', 'Applied torque min/1', 'autorouting', 'on');
add_line(model, 'Safety torque cap/1', 'Applied torque min/2', 'autorouting', 'on');
add_line(model, 'Safety torque cap/1', 'Log safety cap/1', 'autorouting', 'on');
add_line(model, 'Applied torque min/1', 'Wheel force conversion/1', 'autorouting', 'on');
add_line(model, 'Applied torque min/1', 'Log applied torque/1', 'autorouting', 'on');
add_line(model, 'Wheel force conversion/1', 'Net longitudinal force/1', 'autorouting', 'on');
add_line(model, 'Net longitudinal force/1', 'Inverse mass/1', 'autorouting', 'on');
add_line(model, 'Inverse mass/1', 'Vehicle speed mps/1', 'autorouting', 'on');
add_line(model, 'Vehicle speed mps/1', 'Speed error/2', 'autorouting', 'on');
add_line(model, 'Vehicle speed mps/1', 'Speed dependent resistance/1', 'autorouting', 'on');
add_line(model, 'Speed dependent resistance/1', 'Net longitudinal force/2', 'autorouting', 'on');
add_line(model, 'Vehicle speed mps/1', 'Log vehicle speed/1', 'autorouting', 'on');

save_system(model);
fprintf('Created %s.slx\n', model);

out = sim(model);
spd = out.get('vehicle_speed_ts');
req = out.get('target_speed_ts');
tq = out.get('applied_torque_ts');
cap = out.get('safety_cap_ts');
figure('Name', 'BEV closed-loop with synthetic safety fault');
subplot(2,1,1);
plot(req.Time, req.Data * 3.6, '--', 'LineWidth', 1.3); hold on;
plot(spd.Time, spd.Data * 3.6, 'LineWidth', 1.5);
ylabel('Speed (km/h)'); grid on; legend('Target', 'Vehicle', 'Location', 'best');
title('BEV closed-loop speed control');
subplot(2,1,2);
plot(tq.Time, tq.Data, 'LineWidth', 1.5); hold on;
plot(cap.Time, cap.Data, '--', 'LineWidth', 1.2);
xlabel('Time (s)'); ylabel('Torque (Nm)'); grid on;
legend('Applied torque', 'Injected safety cap', 'Location', 'best');
sgtitle('Synthetic safety test: torque inhibition at t = 12 s');
saveas(gcf, 'bev_closed_loop_results.png');

% Export to CSV: common 0.1 s time base, using interpolation.
t = (0:0.1:25)';
v = interp1(spd.Time, squeeze(spd.Data), t, 'linear', 'extrap');
u = interp1(tq.Time, squeeze(tq.Data), t, 'previous', 'extrap');
c = interp1(cap.Time, squeeze(cap.Data), t, 'previous', 'extrap');
r = interp1(req.Time, squeeze(req.Data), t, 'previous', 'extrap');
T = table(t, r*3.6, v*3.6, u, c, 'VariableNames', ...
    {'timestamp_s','reference_kph','vehicle_speed_kph','applied_torque_nm','safety_cap_nm'});
writetable(T, 'bev_closed_loop_results.csv');
fprintf('Saved bev_closed_loop_results.csv and bev_closed_loop_results.png\n');
