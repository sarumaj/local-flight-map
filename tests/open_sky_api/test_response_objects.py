from local_flight_map.api.response_objects import (
    StateVector,
    States,
    Waypoint,
    FlightTrack
)


def test_state_vector_serialization():
    # Create a test StateVector
    state = StateVector(
        icao24="abc123",
        callsign="TEST123",
        origin_country="United States",
        time_position=1234567890,
        last_contact=1234567890,
        longitude=45.0,
        latitude=30.0,
        geo_altitude=1000.0,
        on_ground=False,
        velocity=500.0,
        true_track=90.0,
        vertical_rate=10.0,
        sensors=[1, 2, 3],
        baro_altitude=1000.0,
        squawk="1234",
        spi=False,
        position_source=0,
        category=0
    )

    # Test to_dict
    state_dict = state.to_dict()
    assert state_dict["icao24"] == "abc123"
    assert state_dict["callsign"] == "TEST123"
    assert state_dict["origin_country"] == "United States"
    assert state_dict["longitude"] == 45.0
    assert state_dict["latitude"] == 30.0

    # Test to_json
    json_str = state.to_json()
    assert isinstance(json_str, str)

    # Test from_json
    new_state = StateVector.from_json(json_str)
    assert new_state.icao24 == state.icao24
    assert new_state.callsign == state.callsign
    assert new_state.origin_country == state.origin_country
    assert new_state.longitude == state.longitude
    assert new_state.latitude == state.latitude


def test_open_sky_states_serialization():
    # Create test states
    state1 = StateVector(
        icao24="abc123",
        callsign="TEST123",
        origin_country="United States",
        time_position=1234567890,
        last_contact=1234567890,
        longitude=45.0,
        latitude=30.0,
        geo_altitude=1000.0,
        on_ground=False,
        velocity=500.0,
        true_track=90.0,
        vertical_rate=10.0,
        sensors=[1, 2, 3],
        baro_altitude=1000.0,
        squawk="1234",
        spi=False,
        position_source=0,
        category=0
    )

    states = States(time=1234567890, states=[state1])

    # Test to_dict
    states_dict = states.to_dict()
    assert states_dict["time"] == 1234567890
    assert len(states_dict["states"]) == 1
    assert states_dict["states"][0]["icao24"] == "abc123"

    # Test to_json
    json_str = states.to_json()
    assert isinstance(json_str, str)

    # Test from_json
    new_states = States.from_json(json_str)
    assert new_states.time == states.time
    assert len(new_states.states) == 1
    assert new_states.states[0].icao24 == state1.icao24


def test_waypoint_serialization():
    # Create test Waypoint
    waypoint = Waypoint(
        time=1234567890,
        latitude=30.0,
        longitude=45.0,
        baro_altitude=1000.0,
        true_track=90.0,
        on_ground=False
    )

    # Test to_dict
    waypoint_dict = waypoint.to_dict()
    assert waypoint_dict["time"] == 1234567890
    assert waypoint_dict["latitude"] == 30.0
    assert waypoint_dict["longitude"] == 45.0

    # Test to_json
    json_str = waypoint.to_json()
    assert isinstance(json_str, str)

    # Test from_json
    new_waypoint = Waypoint.from_json(json_str)
    assert new_waypoint.time == waypoint.time
    assert new_waypoint.latitude == waypoint.latitude
    assert new_waypoint.longitude == waypoint.longitude


def test_flight_track_serialization():
    # Create test waypoints
    waypoint1 = Waypoint(
        time=1234567890,
        latitude=30.0,
        longitude=45.0,
        baro_altitude=1000.0,
        true_track=90.0,
        on_ground=False
    )
    waypoint2 = Waypoint(
        time=1234567891,
        latitude=31.0,
        longitude=46.0,
        baro_altitude=2000.0,
        true_track=91.0,
        on_ground=False
    )

    # Create test FlightTrack
    track = FlightTrack(
        icao24="abc123",
        startTime=1234567890,
        endTime=1234567899,
        callsign="TEST123",
        path=[waypoint1, waypoint2]
    )

    # Test to_dict
    track_dict = track.to_dict()
    assert track_dict["icao24"] == "abc123"
    assert track_dict["callsign"] == "TEST123"
    assert len(track_dict["path"]) == 2
    assert track_dict["path"][0]["latitude"] == 30.0
    assert track_dict["path"][1]["latitude"] == 31.0

    # Test to_json
    json_str = track.to_json()
    assert isinstance(json_str, str)

    # Test from_json
    new_track = FlightTrack.from_json(json_str)
    assert new_track.icao24 == track.icao24
    assert new_track.callsign == track.callsign
    assert len(new_track.path) == 2
    assert new_track.path[0].latitude == waypoint1.latitude
    assert new_track.path[1].latitude == waypoint2.latitude


def test_optional_fields():
    # Test StateVector with None values
    state = StateVector(
        icao24="abc123",
        callsign=None,
        origin_country="United States",
        time_position=None,
        last_contact=1234567890,
        longitude=None,
        latitude=None,
        geo_altitude=None,
        on_ground=False,
        velocity=None,
        true_track=None,
        vertical_rate=None,
        sensors=None,
        baro_altitude=None,
        squawk=None,
        spi=False,
        position_source=0,
        category=0
    )

    # Test serialization with None values
    json_str = state.to_json()
    new_state = StateVector.from_json(json_str)
    assert new_state.callsign is None
    assert new_state.time_position is None
    assert new_state.longitude is None
    assert new_state.latitude is None
