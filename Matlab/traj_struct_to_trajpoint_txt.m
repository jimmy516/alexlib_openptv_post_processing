function traj_struct_to_trajpoint_txt(traj)
%
%
%
% Usage:
%
% TRAJ_STRUCT_TO_TRAJPOINT_TXT(TRAJ)
%
% Inputs:
%  TRAJ - structure of trajectories, generated by xuap2traj function
%
% Example:
% >> traj_struct_to_trajpoint(traj)
%

% Author: Alex Liberzon (alex.dot.liberzon.at.gmail.dot.com)
% Date: 12.02.10


fid = fopen('trajpoint.txt','w');
for i = 1:numel(traj)
    fprintf(fid,'%9.4f %9.4f %9.4f %5d %5d\n',[traj(i).xf,traj(i).yf,traj(i).zf,traj(i).t,repmat(i,1,length(traj(i).xf))']')
end
fclose(fid);
end

