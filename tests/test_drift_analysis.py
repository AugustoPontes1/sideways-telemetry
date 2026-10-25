import math
import pytest
from drift_analysis import analyze_drift, steering_events, throttle_events, compare_trajectories, build_recorded_reference

EPOCH_NS = 1_760_000_000_000_000_000

def sample(i, *, yaw=0, vx=0, vz=20, steer=0.0, throttle=0.5, rpm=4500,
           gear=2, x=None, z=None, track="test-track"):
    return {
        "sequence": i,
        "telemetry": {
            "timestamp_unix_ns": EPOCH_NS + i*20_000_000,
            "heading_rad": yaw, "velocity_world_mps": [vx,0,vz],
            "position_world_m": [i if x is None else x,0,i if z is None else z],
            "steer_angle_rad": steer, "throttle": throttle, "rpm": rpm,
            "gear":gear, "speed_kmh":72, "track":track,
        },
    }

def test_drift_detector_requires_calibration_and_time():
    points = [sample(i,vx=8,vz=18) for i in range(35)]
    with pytest.raises(ValueError, match="calibrated"):
        analyze_drift(points)
    detected = analyze_drift(points, yaw_calibrated=True)
    assert len(detected) == 1
    assert detected[0].peak_abs_angle_deg == pytest.approx(math.degrees(math.atan2(8,18)))
    assert detected[0].end_s-detected[0].start_s == pytest.approx(.68)
    assert analyze_drift([sample(i) for i in range(35)],yaw_calibrated=True) == []


def test_drift_detector_breaks_on_time_gap():
    points = [sample(i,vx=8,vz=18) for i in range(5)] + [sample(i,vx=8,vz=18) for i in range(100,105)]
    assert analyze_drift(points,yaw_calibrated=True,min_duration_s=.3)==[]


def test_steering_analysis_spikes_and_reversals():
    points = [sample(0,steer=0.1),sample(1,steer=.25),sample(2,steer=-.25),sample(3,steer=-.3)]
    result = steering_events(points,cooldown_s=0)
    assert any(event.kind == "rapid_steering_input" for event in result)
    assert any(event.kind == "direction_reversal" for event in result)


def test_throttle_changes_gear_and_rpm():
    points = [sample(0,throttle=.2,rpm=6500),sample(1,throttle=.9,rpm=5500,gear=3),sample(2,throttle=.1,rpm=4500,gear=3)]
    kinds = {event.kind for event in throttle_events(points,cooldown_s=0)}
    assert {"rapid_throttle_tip_in", "rapid_throttle_lift_off", "gear_change", "rapid_rpm_drop"}.issubset(kinds)


def test_compare_reference_same_track_and_progress():
    a = [sample(i,x=i,z=0) for i in range(10)]
    ref = [sample(i,x=i,z=1) for i in range(10)]
    result = compare_trajectories(a,ref,count=20)
    assert result.mean_deviation_m == pytest.approx(1)
    assert result.max_deviation_m == pytest.approx(1)
    assert not result.reference_is_ideal
    wrong_track = [sample(i,track="another") for i in range(10)]
    with pytest.raises(ValueError, match="different tracks"):
        compare_trajectories(a,wrong_track)


def test_recorded_reference_keeps_rpm_profile_but_not_ideal():
    samples = [sample(i,rpm=4000+i*100,x=i,z=i*.5) for i in range(11)]
    recorded = build_recorded_reference(samples,count=6)
    assert recorded["type"] == "recorded_reference" and recorded["ideal"] is False
    assert len(recorded["points"]) == 6
    assert recorded["points"][0]["rpm"] == pytest.approx(4000)
    assert recorded["points"][-1]["rpm"] == pytest.approx(5000)


def test_django_rest_shape_supported():
    a=[{"sampled_at":"2026-10-22T12:00:00Z", "position_world_m":[0,0,0],"track":"x","rpm":4000,"speed_kmh":40},
       {"sampled_at":"2026-10-22T12:00:01Z", "position_world_m":[1,0,0],"track":"x","rpm":4200,"speed_kmh":50}]
    result=build_recorded_reference(a,count=2)
    assert result["points"][-1]["position_world_m"] == pytest.approx([1,0,0])
