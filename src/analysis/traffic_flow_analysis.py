"""Offline space-time aggregation for straight, directed driving-lane sections."""
import math
from collections import defaultdict


def split_space_time_interval(s0, s1, t0, t1, road_length_m,
                              section_length_m=50.0, window_s=60.0):
    """Clip a linear trajectory to complete spatial cells and temporal windows.

    Returns (section index, time-window index, vehicle seconds, longitudinal
    distance in metres). No traffic-state or speed filtering is applied.
    Residual road length shorter than one section is outside the selected scope.
    """
    values=(s0,s1,t0,t1,road_length_m,section_length_m,window_s)
    if not all(math.isfinite(v) for v in values):
        raise ValueError('Nonfinite trajectory or aggregation parameter')
    if t1<=t0 or t0<0 or road_length_m<=0 or section_length_m<=0 or window_s<=0:
        raise ValueError('Invalid time interval or aggregation parameter')
    # Express section and time-window crossings as fractions of one trajectory
    # interval. Each resulting piece lies in the cell containing its midpoint.
    cuts={0.0,1.0}; ds=s1-s0; dt=t1-t0
    if ds:
        for n in range(math.floor(min(s0,s1)/section_length_m)+1,
                       math.ceil(max(s0,s1)/section_length_m)):
            a=(n*section_length_m-s0)/ds
            if 0<a<1:cuts.add(a)
    for n in range(math.floor(t0/window_s)+1,math.ceil(t1/window_s)):
        a=(n*window_s-t0)/dt
        if 0<a<1:cuts.add(a)
    edges=sorted(cuts); count=math.floor((road_length_m+1e-9)/section_length_m)
    result=[]
    for a,b in zip(edges,edges[1:]):
        mid=(a+b)/2; section=math.floor((s0+mid*ds)/section_length_m)
        if not 0<=section<count:continue
        window=math.floor((t0+mid*dt)/window_s)
        result.append((section,window,dt*(b-a),abs(ds)*(b-a)))
    return result


def edie_metrics(vehicle_seconds, distance_m, length_m, duration_s):
    """Compatible k [veh/km/lane], q [veh/h/lane], v [km/h] for one lane."""
    if min(vehicle_seconds,distance_m)<0 or min(length_m,duration_s)<=0:
        raise ValueError('Invalid exposure or cell dimensions')
    k=1000*vehicle_seconds/(length_m*duration_s)
    q=3600*distance_m/(length_m*duration_s)
    # A stopped vehicle contributes time at zero speed. An empty cell has no
    # speed observation.
    v=3.6*distance_m/vehicle_seconds if vehicle_seconds else None
    if not vehicle_seconds and distance_m:
        raise ValueError('Distance cannot occur without temporal exposure')
    return k,q,v


def density_band_guides(cells, width=10.0, min_cells=10, length_m=50.0):
    """Pool observed cells in fixed density bands, without fitting a model.

    A cell contributes its actual space-time area. The same (k,q,v) triple
    appears in every projection, so q=k*v is retained. Bands with too few
    cells remain in the output but break the displayed guide. Counts do not
    imply independent observations or a statistical confidence threshold.
    Input must describe one run; empty cells have no speed and are excluded.
    """
    if not math.isfinite(width) or width<=0 or not math.isfinite(length_m) or length_m<=0:
        raise ValueError('Invalid guide dimensions')
    if not isinstance(min_cells,int) or min_cells<1:
        raise ValueError('min_cells must be a positive integer')
    groups=defaultdict(lambda:[0,0.,0.,0.])
    for cell in cells:
        seconds=float(cell['vehicle_seconds']);metres=float(cell['longitudinal_distance_m'])
        duration=float(cell['duration_s'])
        if not all(math.isfinite(x) for x in (seconds,metres,duration)):
            raise ValueError('Nonfinite cell')
        k,q,v=edie_metrics(seconds,metres,length_m,duration)
        if v is None:continue
        bucket=groups[math.floor(k/width)]
        bucket[0]+=1;bucket[1]+=seconds;bucket[2]+=metres;bucket[3]+=length_m*duration
    result=[];segment=-1;previous=None
    for band,(count,seconds,metres,area) in sorted(groups.items()):
        supported=count>=min_cells
        if supported and previous!=band-1:segment+=1
        result.append(dict(band=band,density_low=band*width,density_high=(band+1)*width,
                           cells=count,vehicle_seconds=seconds,longitudinal_distance_m=metres,
                           space_time_area_m_s=area,density_veh_per_km_lane=1000*seconds/area,
                           flow_veh_per_h_lane=3600*metres/area,speed_kmh=3.6*metres/seconds,
                           supported=supported,segment=segment if supported else None))
        previous=band if supported else None
    return result
