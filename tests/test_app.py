"""
Tests for the Mergington High School Activities API using AAA (Arrange-Act-Assert) pattern.

AAA Pattern:
- Arrange: Set up test data and fixtures
- Act: Perform the action being tested
- Assert: Verify the result
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Arrange: Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Arrange: Reset activities data before and after each test."""
    from src import app as app_module
    
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    
    # Reset before test
    app_module.activities.clear()
    app_module.activities.update(original_activities)
    yield
    # Reset after test
    app_module.activities.clear()
    app_module.activities.update(original_activities)


class TestRootEndpoint:
    """Test suite for the root endpoint."""

    def test_root_redirects_to_index(self, client):
        """Test that root endpoint redirects to static/index.html.
        
        AAA:
        - Arrange: Client is ready
        - Act: Make GET request to root
        - Assert: Verify 307 redirect status and correct location header
        """
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Test suite for the GET /activities endpoint."""

    def test_get_all_activities_returns_success(self, client):
        """Test that retrieving all activities returns 200 OK.
        
        AAA:
        - Arrange: Client is ready
        - Act: Make GET request to /activities
        - Assert: Verify 200 status code
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200

    def test_get_all_activities_contains_all_activities(self, client):
        """Test that all activities are returned in the response.
        
        AAA:
        - Arrange: Client is ready with 3 activities
        - Act: Fetch activities from API
        - Assert: Verify all 3 activities are present
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_activity_contains_required_fields(self, client):
        """Test that each activity has all required fields.
        
        AAA:
        - Arrange: Client is ready
        - Act: Fetch activities from API
        - Assert: Verify each activity contains description, schedule, max_participants, participants
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        # Assert
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity

    def test_participants_list_is_correct(self, client):
        """Test that participants list matches expected data.
        
        AAA:
        - Arrange: Client is ready with Chess Club having 2 participants
        - Act: Fetch activities from API
        - Assert: Verify both participants are present and count is 2
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        participants = data["Chess Club"]["participants"]
        
        # Assert
        assert "michael@mergington.edu" in participants
        assert "daniel@mergington.edu" in participants
        assert len(participants) == 2


class TestSignup:
    """Test suite for the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_student_succeeds(self, client):
        """Test that a new student can successfully sign up for an activity.
        
        AAA:
        - Arrange: Client ready, student not yet signed up
        - Act: Post signup request for new student
        - Assert: Verify 200 OK response with success message
        """
        # Act
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the student to participants list.
        
        AAA:
        - Arrange: Client ready, student not signed up
        - Act: Sign up new student and fetch activities
        - Assert: Verify participant is in the list
        """
        # Arrange
        email = "newstudent@mergington.edu"
        
        # Act
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        
        # Assert
        assert email in participants

    def test_signup_duplicate_student_fails(self, client):
        """Test that duplicate signup is rejected with 400 error.
        
        AAA:
        - Arrange: Chess Club has michael@mergington.edu already signed up
        - Act: Try to sign up the same student again
        - Assert: Verify 400 error with appropriate message
        """
        # Act
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signup for non-existent activity returns 404.
        
        AAA:
        - Arrange: Client ready
        - Act: Try to sign up for non-existent activity
        - Assert: Verify 404 error
        """
        # Act
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=student@mergington.edu"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_full_activity_fails(self, client):
        """Test that signup fails when activity is at capacity.
        
        AAA:
        - Arrange: Create activity with max_participants=1 and 1 existing participant
        - Act: Try to sign up new student when full
        - Assert: Verify 400 error indicating activity is full
        """
        # Arrange
        from src import app as app_module
        app_module.activities["Test Activity"] = {
            "description": "Test",
            "schedule": "Test",
            "max_participants": 1,
            "participants": ["existing@mergington.edu"]
        }
        
        # Act
        response = client.post(
            "/activities/Test%20Activity/signup?email=newstudent@mergington.edu"
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "full" in data["detail"]

    def test_signup_multiple_students_same_activity(self, client):
        """Test that multiple different students can sign up for same activity.
        
        AAA:
        - Arrange: Chess Club has 2 participants
        - Act: Sign up 2 new students for Chess Club
        - Assert: Verify all 4 participants are present
        """
        # Act
        client.post("/activities/Chess%20Club/signup?email=student1@mergington.edu")
        client.post("/activities/Chess%20Club/signup?email=student2@mergington.edu")
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        
        # Assert
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants
        assert len(participants) == 4


class TestUnregister:
    """Test suite for the DELETE /activities/{activity_name}/signup endpoint."""

    def test_unregister_existing_participant_succeeds(self, client):
        """Test that an existing participant can successfully unregister.
        
        AAA:
        - Arrange: michael@mergington.edu is registered for Chess Club
        - Act: Delete signup for michael@mergington.edu
        - Assert: Verify 200 OK response
        """
        # Act
        response = client.delete(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant_from_list(self, client):
        """Test that unregister removes participant from participants list.
        
        AAA:
        - Arrange: michael@mergington.edu in Chess Club participants
        - Act: Unregister and fetch activities
        - Assert: Verify michael@mergington.edu not in participants
        """
        # Act
        client.delete(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        
        # Assert
        assert "michael@mergington.edu" not in participants

    def test_unregister_not_registered_student_fails(self, client):
        """Test that unregistering a non-registered student fails with 400.
        
        AAA:
        - Arrange: Student is not registered for activity
        - Act: Try to unregister non-registered student
        - Assert: Verify 400 error
        """
        # Act
        response = client.delete(
            "/activities/Chess%20Club/signup?email=notregistered@mergington.edu"
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregister for non-existent activity returns 404.
        
        AAA:
        - Arrange: Activity doesn't exist
        - Act: Try to unregister from non-existent activity
        - Assert: Verify 404 error
        """
        # Act
        response = client.delete(
            "/activities/Nonexistent%20Activity/signup?email=student@mergington.edu"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_all_participants(self, client):
        """Test that all participants can be unregistered one by one.
        
        AAA:
        - Arrange: Chess Club has 2 participants
        - Act: Unregister both participants
        - Assert: Verify no participants remain
        """
        # Act
        client.delete(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        client.delete(
            "/activities/Chess%20Club/signup?email=daniel@mergington.edu"
        )
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        
        # Assert
        assert len(participants) == 0


class TestSignupAndUnregisterWorkflow:
    """Integration test suite for signup and unregister workflows."""

    def test_signup_then_unregister_then_signup_again(self, client):
        """Test full lifecycle: signup -> unregister -> signup again.
        
        AAA:
        - Arrange: Student not signed up initially
        - Act: Sign up, unregister, sign up again
        - Assert: Verify student is signed up at end
        """
        # Arrange
        email = "lifecycle@mergington.edu"
        activity = "Programming%20Class"
        
        # Act: Sign up
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Assert: Verify signed up
        response = client.get("/activities")
        assert email in response.json()["Programming Class"]["participants"]
        
        # Act: Unregister
        response2 = client.delete(f"/activities/{activity}/signup?email={email}")
        assert response2.status_code == 200
        
        # Assert: Verify unregistered
        response = client.get("/activities")
        assert email not in response.json()["Programming Class"]["participants"]
        
        # Act: Sign up again
        response3 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response3.status_code == 200
        
        # Assert: Verify signed up again
        response = client.get("/activities")
        assert email in response.json()["Programming Class"]["participants"]

    def test_signup_updates_availability(self, client):
        """Test that signup updates activity availability count.
        
        AAA:
        - Arrange: Get initial participant count for Gym Class
        - Act: Sign up new student
        - Assert: Verify participant count increased by 1
        """
        # Arrange
        response = client.get("/activities")
        initial_count = len(response.json()["Gym Class"]["participants"])
        
        # Act
        client.post("/activities/Gym%20Class/signup?email=newgym@mergington.edu")
        response = client.get("/activities")
        new_count = len(response.json()["Gym Class"]["participants"])
        
        # Assert
        assert new_count == initial_count + 1

    def test_multiple_signups_and_unregisters(self, client):
        """Test multiple signup and unregister operations in sequence.
        
        AAA:
        - Arrange: Activity with initial participants
        - Act: Sign up 3 students, unregister 1, sign up 1 more
        - Assert: Verify final count matches expected
        """
        # Arrange
        response = client.get("/activities")
        initial_count = len(response.json()["Gym Class"]["participants"])
        
        # Act: Sign up 3 students
        client.post("/activities/Gym%20Class/signup?email=user1@mergington.edu")
        client.post("/activities/Gym%20Class/signup?email=user2@mergington.edu")
        client.post("/activities/Gym%20Class/signup?email=user3@mergington.edu")
        
        # Act: Unregister 1 student
        client.delete("/activities/Gym%20Class/signup?email=user1@mergington.edu")
        
        # Act: Sign up 1 more student
        client.post("/activities/Gym%20Class/signup?email=user4@mergington.edu")
        
        # Assert: Verify final count is initial + 3 - 1 + 1 = initial + 3
        response = client.get("/activities")
        final_count = len(response.json()["Gym Class"]["participants"])
        assert final_count == initial_count + 3
