"""Narrow CARLA 0.9.15 compatibility fixes; imported only for live navigation."""

from agents.navigation.basic_agent import BasicAgent


COLLINEAR_ANGLE_EPSILON_DEG = 0.001


class CollinearSafeBasicAgent(BasicAgent):
    """Include directly-ahead vehicles in the stock obstacle detector.

    CARLA 0.9.15 uses a strict min_angle < angle comparison. With its default
    lower bound of zero, an exactly aligned target is accidentally excluded.
    Widen just that default boundary; keep positive caller-specified bounds,
    lane checks, junction handling, braking, and the official planner unchanged.
    """

    def _vehicle_obstacle_detected(
        self, vehicle_list=None, max_distance=None,
        up_angle_th=90, low_angle_th=0, lane_offset=0,
    ):
        if low_angle_th == 0:
            low_angle_th = -COLLINEAR_ANGLE_EPSILON_DEG
        return super()._vehicle_obstacle_detected(
            vehicle_list, max_distance, up_angle_th, low_angle_th, lane_offset
        )
