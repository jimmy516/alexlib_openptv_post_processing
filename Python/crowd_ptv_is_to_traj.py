""" Python script and functions that convert the ptv_is.* database 
generated by OpenPTV (for the crowd tracking experiment) into the Python data
structures of Particles, Frames, List of Frames, Trajectories and plots the data
"""
import os
import glob
import numpy as np
import matplotlib.pyplot as plt


class Particle(object):
    """ Particle object that defines every single tracked point
    the attributes are position (x,y,z) and velocities (u,v,w), time instance (t)
    and trajectory identity (id)
    """
    def __init__(self,p=0,n=0, x=0.0,y=0.0,z=0.0,t=0,id=None,\
    u=0.0,v=0.0,w=0.0,ax=0.0,ay=0.0,az=0.0):
        self.p = p
        self.n = n
        self.x = x
        self.y = y
        self.z = z
        self.t = t
        self.id = id
        self.u = u
        self.v = v
        self.w = w
        self.ax = ax
        self.ay = ay
        self.az = az
        
    def __str__(self):
        return '%.2f %.2f %.2f %.2f %.2f %.2f %d %d' % (self.x,self.y,self.z,\
        self.u,self.v,self.w,self.t,self.id)
        
    def __repr__(self):
        return str(self)
        
        
class Frame(list):
    """ Frame class is a list of Particles in the given frame, sharing the same
    time instance (t)
    """
    def __new__(cls, data=None,len=0):
        obj = super(Frame, cls).__new__(cls, data)
        return obj

    def __str__(self):
        s = 'Frame(['
        for i in self:
            s += str(i)
        s += '])'
        return s
        # return 'Traj(%s)' % list(self)
        
    def __repr__(self):
        return str(self)

    def __add__(self, other):
        return Frame(list(self) + list(other))
        
    def len(self):
        return len(list(self))
        

class Trajectory(list):
    """ Trajectory class is a list of Particles that are linked together in 
    time
    """
    def __new__(cls, data=None):
        obj = super(Trajectory, cls).__new__(cls, data)
        return obj

    def __str__(self):
        s = 'Traj(['
        for i in self:
            s += str(i)
        s += '])'
        return s
        # return 'Traj(%s)' % list(self)
        
    def __repr__(self):
        return str(self)

    def __add__(self, other):
        return Trajectory(list(self) + list(other))

        
def frame_from_file(filename):
    """ frame_from_file(filename) reads the data
    in the given file into a frame as a list
    of the particles
    """
    t = int(filename.split('.')[-1])
    with open(filename) as f:
        np = int(f.readline())
        frame = Frame()
        for i in range(np):
            p = Particle()
            vals = f.readline().split()
            p.p = int(vals[0])
            p.n = int(vals[1])
            p.x = float(vals[2])/1000. # mm to meter
            p.y = float(vals[3])/1000. # mm to meter
            p.z = float(vals[4])/1000. # mm to meter
            p.t = t
            frame.append(p)
    return frame
                        
def read_ptv_data_from_directory(directory,first=None,last=None):
	""" 
        directory = '/Users/alex/Desktop/crowd_tracking/res/'
        data = read_ptv_data_from_directory(directory,38940,38970)
	"""
	d = glob.glob(os.path.join(directory,'ptv_is.*'))
	d.sort()
	dlist = [int(os.path.splitext(name)[1][1:]) for name in d]
	if first is None or first < dlist[0]:
		first = 0
	else:
		first = dlist.index(first)
#
	if last is None or last > dlist[-1]:
		last = -1
	else:
		last = dlist.index(last)
	
	
	d = d[first:last] # only files between first and last
	dlist = dlist[first:last]
	data = []
	
	for ind,filename in enumerate(d):
		data.append(frame_from_file(filename))
	
	return data
    
    
def link_trajectories(data):
    """ performs linking of the particles in the frame according to their
    attributes provided by the OpenPTV: previous and next (or left and right)
    Particles are assigned a unique identity during this operation
    """
    id = 0
    # first frame, assign the id to the first frame
    # particles in ascending order, starting from 0
    for particle in data[0]:
        if particle.n != -2:
            particle.id = id
            id += 1
    for ind,frame in enumerate(data[1:]):
        # print ind
        past = data[ind]
        for particle in frame:
            # print 'prev = ', particle.p
            if particle.p == -1: # no past
                if particle.n == -2: # no future
                    pass
                    # frame.remove(particle)
                else:
                    particle.id = id #  new id
                    id += 1 # update lastid
            else:
                # print 'prev =',particle.p
                # print 'id = ',past[int(particle.p)].id
                particle.id = past[int(particle.p)].id
    return id #lastid

def clean_data(data):
    """ clean_data(data) removes the unlinked
    particles and empty frames
    """
    for frame in data:
        for particle in frame:
            if particle.id == None:
                frame.remove(particle)
        
    for frame in data[-1:0:-1]: # reverse reading
         if len(frame) == 0:
            data.remove(frame)
            
    return data
            
 
def frames_to_traj(data,lastid=None):
    """ converts data from frames of particles into 
    trajectories of particles, using unique identities
    """
    if lastid == None:
        id = []
        for f in data:
            for p in f:
                id.append(p.id)
        
        lastid = max(id)
                
    # prepare the dataset
    traj = [Trajectory() for i in range(lastid+1)]    
    for frame in data:
        for particle in frame:
            try:
                traj[particle.id].append(particle)
            except:
                print len(traj)
                print particle
                print particle.id
                
                
    for t in traj:
        if len(t) < 3:
            traj.remove(t)
            
    return traj 
            
 
        
def calculate_velocity(traj,fps):
    """ estimates velocity of the particles along the trajectory using simple
    forward and backward difference scheme
    Inputs:
        traj = Trajectory(), a list of Particle() objects linked in time
        fps = frame-per-second rate of recording, converts the frames to seconds
    Output: traj.{u,v,w} in meters/second    
    TODO: to be improved using smooth splines and higher order differentation 
    schemes
    """
    for t in traj: # for each trajectory
        # last particle use backward difference
        t[-1].u = (t[-1].x - t[-2].x)*fps # m/s
        t[-1].v = (t[-1].y - t[-2].y)*fps
        t[-1].w = (t[-1].z - t[-2].z)*fps
        #first particle use forward difference
        t[0].u = (t[1].x - t[0].x)*fps # m/s
        t[0].v = (t[1].y - t[0].y)*fps
        t[0].w = (t[1].z - t[0].z)*fps        
        for i,p in enumerate(t[1:-1]): # for other particles
            p.u = (t[i+1].x - t[i].x)/2.*fps
            p.v = (t[i+1].y - t[i].y)/2.*fps
            p.w = (t[i+1].z - t[i].z)/2.*fps
    
    return traj
    
def calculate_acceleration(traj,fps):
    """ estimates acceleration of the person along the trajectory using simple
    forward and backward difference scheme
    Inputs:
        traj = Trajectory(), a list of Particle() objects linked in time
        fps = frame-per-second rate of recording, converts the frames to seconds
    Output: traj.{ax,ay,az} in meters/second**2    
    TODO: to be improved using smooth splines and higher order differentation 
    schemes
    """
    for t in traj: # for each trajectory
        # last particle use backward difference
        t[-1].ax = (t[-1].u - t[-2].u)*fps # m/s
        t[-1].ay = (t[-1].v - t[-2].v)*fps
        t[-1].az = (t[-1].w - t[-2].w)*fps
        #first particle use forward difference
        t[0].ax = (t[1].u - t[0].u)*fps # m/s
        t[0].ay = (t[1].v - t[0].v)*fps
        t[0].az = (t[1].w - t[0].w)*fps        
        for i,p in enumerate(t[1:-1]): # for other particles
            p.ax = (t[i+1].u - t[i].u)/2.*fps
            p.ay = (t[i+1].v - t[i].v)/2.*fps
            p.az = (t[i+1].w - t[i].w)/2.*fps
    
    return traj

def plot_traj(traj,fig=None):
    """ plots single trajectory as dots, curves and arrows
    using matplotlib
    """
    if fig == None:
        plt.figure()
        
    x,y,z,u,v,w = [],[],[],[],[],[]
    for p in traj: # for all particles
        x.append(p.x)
        y.append(p.y)
        z.append(p.z)
        u.append(p.u)
        v.append(p.v)
        w.append(p.w)
        
    plt.plot(x,y,'o--')
    plt.quiver(x,y,u,v)
        
 
def plot_all_trajectories(list_of_traj):
    """ plots all the trajectories in a given list of trajectories on a single
    figure, overlapping the curves
    """
    fig = plt.figure()
    plt.hold(True)
    for traj in list_of_traj:
           plot_traj(traj,fig)
    fig.show()


def plot_colored_trajectories(list_of_traj):
    """ plots all the trajectories in a given list of trajectories on a single
    figure, overlapping the curves
    """
    fig = plt.figure()
    plt.hold(True)
    for traj in list_of_traj:
        x,y,z,u,v,w = [],[],[],[],[],[]
        for p in traj: # for all particles
            x.append(p.x)
            y.append(p.y)
            z.append(p.z)
            u.append(p.u)
            v.append(p.v)
            w.append(p.w)
        
        if np.median(u) > 0:
            plt.plot(x,y,'bo--')
            plt.quiver(x,y,u,v,color='b')
        else:
            plt.plot(x,y,'rs-.')
            plt.quiver(x,y,u,v,color='r')   
    plt.xlabel('x [m]')
    plt.ylabel('y [m]')
    plt.title('Direction-colored velocity map')
    fig.show()
 


if __name__ == '__main__':
     directory = '/Users/alex/Desktop/crowd_tracking/res/'
     # Note that the data is stored in millimeters
     # time is given in frames
     fps = 5.0 # frames-per-second
     
     # data = read_ptv_data_from_directory(directory,38940,38999)
     data = read_ptv_data_from_directory(directory,38940,56656)
     link_trajectories(data)
     tmp = len(data)
     clean_data(data)
     while len(data) != tmp:
        clean_data(data)
        tmp = len(data)
     
     traj = frames_to_traj(data)
     
     calculate_velocity(traj,fps)
     calculate_acceleration(traj,fps)
     # plot_all_trajectories(traj)
     plot_colored_trajectories(traj)
     np.savez(os.path.join('/Users/alex/Desktop/crowd_tracking','ptv_is'),\
     data=data,traj=traj)
     
     # example of the histogram of velocity
     u = []
     v = []
     t = []
     x = []
     y = []
     id = []
     for f in data:
         for p in f:
             # vel.append(p.u**2 + p.v**2)
             x.append(p.x)
             y.append(p.y)
             u.append(p.u)
             v.append(p.v)
             t.append(p.t)
             id.append(p.id)
     
     x = np.asarray(x)
     y = np.asarray(y)
     u = np.asarray(u)
     v = np.asarray(v)
     t = np.asarray(t)
     id = np.asarray(id)
     t = (t - t[0])/fps  
     vel = u**2 + v**2 
              
     # vel = [i**2 + j**2 for i,j in zip(u,v)]  
     plt.figure()  
     plt.plot(t,vel)
     plt.xlabel('t')
     plt.ylabel('velocity')
     
     plt.figure()
     plt.hist(vel,100)
     plt.xlabel('velocity')
     plt.ylabel('histogram')
     
     
     np.savez(os.path.join('/Users/alex/Desktop/crowd_tracking','xyuvtid'),\
     x=x,y=y,u=u,v=v,t=t,id=id)
     
     
     plt.figure()
     plt.hist2d(x,u,bins=100,range=[[-1,1.3],[-2,2]])
     plt.title('speed vs position')
     plt.xlabel('x [m]')
     plt.ylabel('u [m/s]')
     plt.colorbar()
     
     plt.figure()
     plt.hist2d(x,v,bins=100,range=[[-1,1.3],[-2,2]])
     plt.title('transverse speed vs position')
     plt.xlabel('x [m]')
     plt.ylabel('v [m/s]')
     plt.colorbar()
     
     plt.figure()
     plt.hist2d(u,v,bins=100,range=[[-1,1],[-1,1]])
     plt.title('transverse speed vs position')
     plt.xlabel('u [m/s]')
     plt.ylabel('v [m/s]')
     plt.colorbar()
     
     
     # compare single person speed vs multi-person speed
     single_u, single_v, dense_u, dense_v = [],[],[],[]
     for f in data:
         if len(f) == 1: # single person frame
             single_u.append(f[0].u)
             single_v.append(f[0].v)
         elif len(f) > 3: # multi person frame
             for p in f:
                 dense_u.append(p.u)
                 dense_v.append(p.v)
                
     plt.figure()
     plt.hist(dense_u,100,color='b',normed=True)
     plt.hist(single_u,100,color='r',normed=True)
     plt.title('single vs dense velocity')
     plt.legend(('dense','single'))
     
     plt.figure()
     plt.hist(dense_v,100,color='b',normed=True)
     plt.hist(single_v,100,color='r',normed=True)
     plt.title('single vs dense transverse velocity')
          

     # compare single person speed vs multi-person speed
     single_ax, single_ay, dense_ax, dense_ay = [],[],[],[]
     for f in data:
         if len(f) == 1: # single person frame
             single_ax.append(f[0].ax)
             single_ay.append(f[0].ay)
         elif len(f) > 3: # multi person frame
             for p in f:
                 dense_ax.append(p.ax)
                 dense_ay.append(p.ay)
                
     plt.figure()
     plt.hist(dense_ax,100,color='b',normed=True)
     plt.hist(single_ax,100,color='r',normed=True)
     plt.title('single vs dense acceleration')
     plt.legend(('dense','single'))
     
     plt.figure()
     plt.hist(dense_ay,100,color='b',normed=True)
     plt.hist(single_ay,100,color='r',normed=True)
     plt.title('single vs dense transverse acceleration')
     plt.legend(('dense','single'))
     
    
                         
      