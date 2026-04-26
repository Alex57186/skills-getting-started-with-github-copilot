"""Test suite for activities API endpoints"""


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns a 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client):
        """Test that /activities returns a dictionary of activities"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_get_activities_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_contains_known_activities(self, client):
        """Test that known activities are in the response"""
        response = client.get("/activities")
        activities = response.json()
        
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_valid_activity(self, client):
        """Test signing up for a valid activity"""
        response = client.post(
            "/activities/Basketball Team/signup?email=student1@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "signed up" in data["message"].lower()

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant"""
        email = "newstudent@mergington.edu"
        client.post(f"/activities/Basketball Team/signup?email={email}")
        
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Basketball Team"]["participants"]

    def test_signup_for_invalid_activity_returns_404(self, client):
        """Test that signing up for nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_duplicate_signup_returns_400(self, client):
        """Test that signing up twice for same activity returns 400"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/Basketball Team/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            f"/activities/Basketball Team/signup?email={email}"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_increases_participant_count(self, client):
        """Test that signup increases the participant count"""
        response_before = client.get("/activities")
        chess_before = len(response_before.json()["Chess Club"]["participants"])
        
        client.post("/activities/Chess Club/signup?email=newplayer@mergington.edu")
        
        response_after = client.get("/activities")
        chess_after = len(response_after.json()["Chess Club"]["participants"])
        
        assert chess_after == chess_before + 1


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/remove endpoint"""

    def test_remove_valid_participant(self, client):
        """Test removing a valid participant"""
        email = "michael@mergington.edu"
        response = client.delete(
            f"/activities/Chess Club/remove?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "removed" in data["message"].lower()

    def test_remove_decreases_participant_count(self, client):
        """Test that removal decreases the participant count"""
        email = "michael@mergington.edu"
        
        response_before = client.get("/activities")
        chess_before = len(response_before.json()["Chess Club"]["participants"])
        
        client.delete(f"/activities/Chess Club/remove?email={email}")
        
        response_after = client.get("/activities")
        chess_after = len(response_after.json()["Chess Club"]["participants"])
        
        assert chess_after == chess_before - 1

    def test_remove_actually_removes_participant(self, client):
        """Test that removal actually removes the participant"""
        email = "michael@mergington.edu"
        
        client.delete(f"/activities/Chess Club/remove?email={email}")
        
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Chess Club"]["participants"]

    def test_remove_from_invalid_activity_returns_404(self, client):
        """Test that removing from nonexistent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Club/remove?email=student@mergington.edu"
        )
        assert response.status_code == 404

    def test_remove_non_participant_returns_400(self, client):
        """Test that removing non-enrolled student returns 400"""
        response = client.delete(
            "/activities/Basketball Team/remove?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()

    def test_cannot_remove_twice(self, client):
        """Test that removing the same participant twice fails on second attempt"""
        email = "michael@mergington.edu"
        
        # First removal should succeed
        response1 = client.delete(f"/activities/Chess Club/remove?email={email}")
        assert response1.status_code == 200
        
        # Second removal should fail
        response2 = client.delete(f"/activities/Chess Club/remove?email={email}")
        assert response2.status_code == 400


class TestIntegrationScenarios:
    """Integration tests combining multiple operations"""

    def test_signup_then_remove_flow(self, client):
        """Test a complete signup and remove flow"""
        email = "testuser@mergington.edu"
        activity = "Basketball Team"
        
        # Initial state: no participants
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Remove
        response = client.delete(f"/activities/{activity}/remove?email={email}")
        assert response.status_code == 200
        
        # Verify removal
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]

    def test_multiple_signups_different_activities(self, client):
        """Test signing up for multiple different activities"""
        email = "multiactivity@mergington.edu"
        
        # Sign up for two activities
        client.post(f"/activities/Chess Club/signup?email={email}")
        client.post(f"/activities/Programming Class/signup?email={email}")
        
        response = client.get("/activities")
        activities = response.json()
        
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]
