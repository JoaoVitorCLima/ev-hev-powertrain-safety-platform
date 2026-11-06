% Minimal BEV longitudinal plant producing CSV for the C++ supervisor.
% Synthetic / illustrative example; no Simulink or toolbox required.
% Run from the repository root: run('matlab/generate_ev_telemetry.m')
dt = 0.1; t = (0:dt:9.9)'; n = numel(t);
speed_kph = zeros(n,1);
soc_pct = zeros(n,1); soc_pct(1) = 68;
battery_temp_c = zeros(n,1); battery_temp_c(1) = 30;
battery_current_a = zeros(n,1);
requested_torque_nm = zeros(n,1);
can_age_ms = 20*ones(n,1);
can_counter = mod((0:n-1)',16);
% Highly simplified longitudinal dynamics, illustrative parameters.
mass = 1450; wheel_radius = 0.31; final_drive = 9.0;
eta_drive = 0.9; pack_v = 350; pack_capacity_kwh = 45;
for k = 1:n
    target_kph = 50 + 10*(t(k) >= 5);
    requested_torque_nm(k) = max(0, min(180, 3*(target_kph-speed_kph(k))));
    force_n = requested_torque_nm(k)*final_drive*eta_drive/wheel_radius;
    v = speed_kph(k)/3.6;
    resistive_n = 150 + 0.35*v*v;
    acceleration = (force_n-resistive_n)/mass;
    if k < n
        speed_kph(k+1) = max(0, speed_kph(k) + dt*3.6*acceleration);
        mech_kw = force_n*v/1000;
        battery_current_a(k) = mech_kw*1000/eta_drive/pack_v;
        pack_power_kw = battery_current_a(k)*pack_v/1000;
        soc_pct(k+1) = max(0, soc_pct(k) - pack_power_kw*dt/(3600*pack_capacity_kwh)*100);
        battery_temp_c(k+1) = battery_temp_c(k) + dt*(0.0004*battery_current_a(k)^2 - 0.03*(battery_temp_c(k)-25));
    end
end
if n > 1, battery_current_a(end) = battery_current_a(end-1); end
% Use fixed portable numeric CSV header (matches C++ main.cpp).
filename = fullfile('data','matlab_ev_telemetry.csv');
if ~exist('data','dir'), mkdir('data'); end
f = fopen(filename,'w');
assert(f>=0,'Unable to create CSV');
fprintf(f,'timestamp_s,speed_kph,soc_pct,battery_temp_c,battery_current_a,requested_torque_nm,can_age_ms,can_counter\n');
for k=1:n
    fprintf(f,'%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%d\n',t(k),speed_kph(k),soc_pct(k),battery_temp_c(k),battery_current_a(k),requested_torque_nm(k),can_age_ms(k),can_counter(k));
end
fclose(f);
fprintf('Generated %s (%d synthetic samples)\n',filename,n);
figure('Name','Synthetic BEV model');
subplot(2,2,1);plot(t,speed_kph);xlabel('s');ylabel('km/h');title('Vehicle speed');
subplot(2,2,2);plot(t,soc_pct);xlabel('s');ylabel('%');title('Battery SOC');
subplot(2,2,3);plot(t,requested_torque_nm);xlabel('s');ylabel('Nm');title('Requested motor torque');
subplot(2,2,4);plot(t,battery_current_a);xlabel('s');ylabel('A');title('Estimated pack current');
