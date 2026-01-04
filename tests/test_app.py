"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestActivities:
    """Tests for retrieving activities"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_activities_have_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()

        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_activities_not_empty(self):
        """Test that activities list is not empty"""
        response = client.get("/activities")
        activities = response.json()
        assert len(activities) > 0

    def test_known_activity_exists(self):
        """Test that Chess Club exists in activities"""
        response = client.get("/activities")
        activities = response.json()
        assert "Chess Club" in activities


class TestSignup:
    """Tests for signing up for activities"""

    def test_signup_to_existing_activity(self):
        """Test signing up to an existing activity"""
        response = client.post(
            "/activities/Art%20Studio/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "test@mergington.edu" in result["message"]

    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant"""
        # First, get current participants
        response = client.get("/activities")
        activities_before = response.json()
        initial_count = len(activities_before["Drama Club"]["participants"])

        # Sign up a new participant
        client.post("/activities/Drama%20Club/signup?email=newuser@mergington.edu")

        # Check that participant was added
        response = client.get("/activities")
        activities_after = response.json()
        final_count = len(activities_after["Drama Club"]["participants"])

        assert final_count == initial_count + 1
        assert "newuser@mergington.edu" in activities_after["Drama Club"]["participants"]

    def test_signup_to_nonexistent_activity(self):
        """Test signing up to a non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email_returns_400(self):
        """Test that signing up with duplicate email returns 400"""
        # First signup
        client.post("/activities/Art%20Studio/signup?email=duplicate@test.edu")

        # Try to sign up same email again
        response = client.post(
            "/activities/Art%20Studio/signup?email=duplicate@test.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]


class TestUnregister:
    """Tests for unregistering from activities"""

    def test_unregister_existing_participant(self):
        """Test unregistering an existing participant"""
        # First sign up
        client.post("/activities/Science%20Olympiad/signup?email=unregister@test.edu")

        # Then unregister
        response = client.delete(
            "/activities/Science%20Olympiad/unregister?email=unregister@test.edu"
        )
        assert response.status_code == 200
        result = response.json()
        assert "Unregistered" in result["message"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "removal@test.edu"

        # Sign up
        client.post("/activities/Tennis%20Club/signup?email=" + email)

        # Get activities before unregister
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Tennis Club"]["participants"]

        # Unregister
        client.delete(f"/activities/Tennis%20Club/unregister?email={email}")

        # Check participant was removed
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Tennis Club"]["participants"]

    def test_unregister_nonexistent_activity(self):
        """Test unregistering from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Fake%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_nonexistent_participant(self):
        """Test unregistering non-existent participant returns 400"""
        response = client.delete(
            "/activities/Debate%20Team/unregister?email=notregistered@test.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]


class TestRoot:
    """Tests for root endpoint"""

    def test_root_redirects(self):
        """Test that root endpoint redirects"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
