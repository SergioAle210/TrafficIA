"""Descriptive grouping of collision callbacks, without changing raw metrics."""
import math


def collision_episodes(events, actors, origin_s, gap_s=1.0):
    """Unordered actor pair + maximum inter-callback gap; both sensors count.

    Actor IDs belong to one run only. A group is not a verified accident.
    Unknown/static actor IDs can represent several objects and are flagged.
    """
    if gap_s < 0 or not math.isfinite(gap_s):
        raise ValueError('Invalid grouping gap')
    episodes, latest = [], {}
    rows = sorted((e for e in events if e['event_type']=='collision'),
                  key=lambda e:float(e['simulation_time_s']))
    for row in rows:
        now = float(row['simulation_time_s'])-origin_s
        if not math.isfinite(now) or now < -1e-5:
            raise ValueError('Invalid collision time')
        emitter = actors[row['vehicle_id']]
        other = int(row['other_actor_id'])
        pair = tuple(sorted((emitter, other)))
        prior = latest.get(pair)
        if prior is None or now-prior['last_elapsed_s'] > gap_s+1e-8:
            prior = dict(actor_pair=list(pair), first_elapsed_s=now, last_elapsed_s=now,
                         span_s=0., raw_callbacks=0, sensor_vehicles=[],
                         ambiguous_other_id=other<=0)
            latest[pair] = prior
            episodes.append(prior)
        prior['last_elapsed_s'] = now
        prior['span_s'] = now-prior['first_elapsed_s']
        prior['raw_callbacks'] += 1
        if row['vehicle_id'] not in prior['sensor_vehicles']:
            prior['sensor_vehicles'].append(row['vehicle_id'])
    return episodes
