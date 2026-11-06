% Build a new anti-windup model from the validated nominal BEV baseline.
% Requires Simulink. Not executed in automated CI; validate locally in MATLAB.
source = 'ev_bev_closed_loop_nominal';
target = 'ev_bev_closed_loop_antiwindup_v2';
assert(exist([source '.slx'],'file') == 2, 'Baseline .slx not found in MATLAB current folder.');
assert(exist([target '.slx'],'file') ~= 2, 'Destination exists: preserve your previous model; rename before retry.');
if bdIsLoaded(source), save_system(source); end
copyfile([source '.slx'], [target '.slx']);
load_system(target);

% Anti-windup by back calculation: d(integrator state)/dt = speed_error +
% (Kaw/Ki) * (applied_torque - unsaturated_PI_torque).
% Kp=10, Ki=1 in the baseline; Kaw is an illustrative tuning parameter.
intblk=[target '/Integral error'];
p=get_param(intblk,'PortHandles');
line=get_param(p.Inport(1),'Line');
assert(line~=-1,'Integral input must be connected');
src=get_param(line,'SrcPortHandle');
delete_line(target,p.Inport(1));
add_block('simulink/Math Operations/Sum',[target '/AW difference'], ...
    'Inputs','+-','Position',[650 420 690 450]);
add_block('simulink/Math Operations/Gain',[target '/AW gain'], ...
    'Gain','0.1','Position',[730 415 795 455]);
add_block('simulink/Math Operations/Sum',[target '/AW integrator input'], ...
    'Inputs','++','Position',[165 280 205 315]);
pa=get_param([target '/Applied torque min'],'PortHandles');
pr=get_param([target '/PI torque'],'PortHandles');
pd=get_param([target '/AW difference'],'PortHandles');
pg=get_param([target '/AW gain'],'PortHandles');
ps=get_param([target '/AW integrator input'],'PortHandles');
add_line(target,pa.Outport(1),pd.Inport(1),'autorouting','on');
add_line(target,pr.Outport(1),pd.Inport(2),'autorouting','on');
add_line(target,pd.Outport(1),pg.Inport(1),'autorouting','on');
add_line(target,src,ps.Inport(1),'autorouting','on');
add_line(target,pg.Outport(1),ps.Inport(2),'autorouting','on');
add_line(target,ps.Outport(1),p.Inport(1),'autorouting','on');
save_system(target);
out=sim(target);
v=out.vehicle_speed_ts.Data(:)*3.6;
fprintf('Anti-windup: max=%.3f km/h, final=%.3f km/h\n',max(v),v(end));
open_system(target);
