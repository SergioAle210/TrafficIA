"""Route-distance speed envelope and stopped/aligned arrival checks.

No CARLA controller gains are changed. The runner feeds the target speed to
BasicAgent and retains its steering and obstacle/traffic-light decisions.
"""

import math

from src.navigation.navigation_diagnostics import wrap_degrees


APPROACH_DECELERATION_MPS2 = 1.5
STOP_MARGIN_M = 0.5
STOPPED_SPEED_MPS = 0.05
ALIGNMENT_TOLERANCE_DEG = 10.0
CENTER_TOLERANCE_M = 0.5
STEERING_CONTINUATION_M = 6.0
ALIGNMENT_SPEED_KMH = 1.0
ARRIVAL_CONTINUATION_LIMIT_M = 3.0


class ArrivalLaneCorridor:
    """A bounded part of the already verified, unique forward continuation.

    CARLA changes road/lane IDs at seams in a continuous driving lane. Accept
    only IDs and longitudinal intervals actually traversed by that support;
    retaining the 3 m goal radius bounds alignment beyond the stopping point.
    This does not add new steering targets or relax stopped/aligned checks.
    """

    def __init__(self, continuation):
        """Store the verified lane sections allowed just beyond the destination."""
        self.goal = continuation[0][0].transform.location
        self.intervals = {}
        distance = 0.0
        previous = self.goal
        for wp, _ in continuation:
            distance += previous.distance(wp.transform.location)
            previous = wp.transform.location
            if distance > ARRIVAL_CONTINUATION_LIMIT_M + 1e-6:
                break
            key = (wp.road_id, wp.section_id, wp.lane_id)
            low, high = self.intervals.get(key, (wp.s, wp.s))
            self.intervals[key] = (min(low, wp.s), max(high, wp.s))

    def contains(self, waypoint, location):
        """Check whether a position lies in the allowed continuation near the destination."""
        if location.distance(self.goal) > ARRIVAL_CONTINUATION_LIMIT_M:
            return False
        interval = self.intervals.get((waypoint.road_id, waypoint.section_id, waypoint.lane_id))
        # Support is sampled at 0.5 m. Include the seam before the first sample
        # of a new road, while the physical goal radius still bounds extension.
        return interval is not None and interval[0] - 0.5 <= waypoint.s <= interval[1] + 0.5


class ArrivalApproach:
    """Track ordered progress to the actual goal, excluding steering support.

    Search only the next 20 m of the route at each tick. A nearby destination
    on a later leg of a loop must not trigger braking or complete the trip.
    """

    def __init__(self, route):
        """Convert the route into segments and initialize distance remaining to the destination."""
        self.segments = []
        total = 0.0
        for (a, _), (b, _) in zip(route, route[1:]):
            a, b = a.transform.location, b.transform.location
            dx, dy = b.x-a.x, b.y-a.y
            length = math.hypot(dx, dy)
            if length > 1e-6:
                self.segments.append((a.x, a.y, dx, dy, length, total))
                total += length
        if not self.segments:
            raise ValueError("La aproximación requiere una ruta no degenerada.")
        self.total_m = total
        self.progress_m = 0.0
        self.remaining_m = total
        self.settling = False

    def update(self, location):
        """Update forward progress along nearby route segments and return the remaining distance."""
        nearest = None
        for x, y, dx, dy, length, start in self.segments:
            if start + length < self.progress_m - 2.0:
                continue
            if start > self.progress_m + 20.0:
                break
            fraction = max(0.0, min(1.0, ((location.x-x)*dx + (location.y-y)*dy) / length**2))
            error2 = (location.x-x-fraction*dx)**2 + (location.y-y-fraction*dy)**2
            if nearest is None or error2 < nearest[0]:
                nearest = error2, start + fraction*length
        if nearest is not None:
            self.progress_m = max(self.progress_m, nearest[1])
        self.remaining_m = max(0.0, self.total_m-self.progress_m)
        return self.remaining_m

    def target_speed_kmh(self, cruise_speed_kmh):
        """Reduce target speed near the destination, allowing slow movement to finish alignment."""
        if self.settling and self.remaining_m <= STOP_MARGIN_M:
            return min(cruise_speed_kmh, ALIGNMENT_SPEED_KMH)
        distance = max(0.0, self.remaining_m - STOP_MARGIN_M)
        # Inverting the constant-deceleration stopping distance gives a speed
        # in m/s. BasicAgent expects its target in km/h.
        return min(cruise_speed_kmh, 3.6*math.sqrt(2*APPROACH_DECELERATION_MPS2*distance))


def alignment_errors(transform, waypoint):
    """Return heading error in degrees and sideways offset in meters from the lane center."""
    yaw = math.radians(waypoint.transform.rotation.yaw)
    dx = transform.location.x-waypoint.transform.location.x
    dy = transform.location.y-waypoint.transform.location.y
    return (wrap_degrees(transform.rotation.yaw-waypoint.transform.rotation.yaw),
            -math.sin(yaw)*dx + math.cos(yaw)*dy)


def is_aligned(vehicle, waypoint):
    """Check that the vehicle's heading and sideways offset are within arrival limits."""
    if waypoint is None:
        return False
    heading, lateral = alignment_errors(vehicle.get_transform(), waypoint)
    return abs(heading) <= ALIGNMENT_TOLERANCE_DEG and abs(lateral) <= CENTER_TOLERANCE_M


def stopped_and_aligned(vehicle, waypoint, speed):
    """Check that the vehicle is slow enough and aligned with its lane."""
    return speed <= STOPPED_SPEED_MPS and is_aligned(vehicle, waypoint)


def approach_control(agent, approach, cruise_speed_kmh):
    """Keep the official steering and hazard braking, even at the stop point."""
    target = approach.target_speed_kmh(cruise_speed_kmh)
    agent.set_arrival_speed(target, cruise_speed_kmh)
    control = agent.run_step()
    if target == 0.0:
        control.throttle = 0.0
        control.brake = 1.0
    return control
