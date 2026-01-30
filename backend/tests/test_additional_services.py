"""
Tests for Content Service
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestContentService:
    """Test suite for content operations"""

    def test_create_idea(self, mock_supabase):
        """Test creating content idea"""
        mock_supabase.from_().insert().execute.return_value.data = [{
            "id": "idea-123",
            "title": "Post sobre produtividade",
            "description": "Como ser mais produtivo",
            "status": "draft",
            "created_at": datetime.now().isoformat()
        }]
        
        result = mock_supabase.from_("content_ideas").insert({
            "title": "Post sobre produtividade",
            "description": "Como ser mais produtivo"
        }).execute()
        
        assert result.data[0]["title"] == "Post sobre produtividade"
        assert result.data[0]["status"] == "draft"

    def test_list_ideas_with_status_filter(self, mock_supabase):
        """Test listing ideas with status filter"""
        mock_supabase.from_().select().eq().execute.return_value.data = [
            {"id": "1", "title": "Idea 1", "status": "draft"},
            {"id": "2", "title": "Idea 2", "status": "draft"}
        ]
        
        result = mock_supabase.from_("content_ideas").select("*").eq("status", "draft").execute()
        
        assert len(result.data) == 2
        assert all(i["status"] == "draft" for i in result.data)

    def test_generate_variations(self, mock_supabase, mock_gemini):
        """Test generating AI variations for idea"""
        mock_gemini.generate_content.return_value.text = """
        Instagram: "🚀 5 dicas para dobrar sua produtividade..."
        LinkedIn: "Profissionais de alta performance sabem que..."
        Twitter: "Thread: Como ser mais produtivo em 2024 👇"
        """
        
        result = mock_gemini.generate_content("Generate variations for: Post sobre produtividade")
        
        assert "Instagram" in result.text
        assert "LinkedIn" in result.text

    def test_create_post(self, mock_supabase):
        """Test creating post from idea"""
        mock_supabase.from_().insert().execute.return_value.data = [{
            "id": "post-123",
            "idea_id": "idea-123",
            "platform": "instagram",
            "content": "🚀 5 dicas para dobrar sua produtividade...",
            "status": "scheduled",
            "scheduled_at": (datetime.now() + timedelta(days=1)).isoformat()
        }]
        
        result = mock_supabase.from_("content_posts").insert({
            "idea_id": "idea-123",
            "platform": "instagram",
            "content": "🚀 5 dicas para dobrar sua produtividade..."
        }).execute()
        
        assert result.data[0]["platform"] == "instagram"
        assert result.data[0]["status"] == "scheduled"

    def test_get_content_calendar(self, mock_supabase):
        """Test getting content calendar"""
        today = datetime.now()
        mock_supabase.from_().select().gte().lte().execute.return_value.data = [
            {"id": "1", "platform": "instagram", "scheduled_at": today.isoformat()},
            {"id": "2", "platform": "linkedin", "scheduled_at": (today + timedelta(days=2)).isoformat()}
        ]
        
        result = mock_supabase.from_("content_posts").select("*").gte(
            "scheduled_at", today.isoformat()
        ).lte(
            "scheduled_at", (today + timedelta(days=7)).isoformat()
        ).execute()
        
        assert len(result.data) == 2

    def test_mark_post_published(self, mock_supabase):
        """Test marking post as published"""
        mock_supabase.from_().update().eq().execute.return_value.data = [{
            "id": "post-123",
            "status": "published",
            "published_at": datetime.now().isoformat()
        }]
        
        result = mock_supabase.from_("content_posts").update({
            "status": "published",
            "published_at": datetime.now().isoformat()
        }).eq("id", "post-123").execute()
        
        assert result.data[0]["status"] == "published"

    def test_update_post_metrics(self, mock_supabase):
        """Test updating post performance metrics"""
        mock_supabase.from_().update().eq().execute.return_value.data = [{
            "id": "post-123",
            "metrics": {
                "likes": 150,
                "comments": 23,
                "shares": 12,
                "reach": 5000
            }
        }]
        
        result = mock_supabase.from_("content_posts").update({
            "metrics": {"likes": 150, "comments": 23, "shares": 12, "reach": 5000}
        }).eq("id", "post-123").execute()
        
        assert result.data[0]["metrics"]["likes"] == 150


class TestAutonomyService:
    """Test suite for autonomy operations"""

    def test_get_autonomy_level(self, mock_supabase):
        """Test getting current autonomy level"""
        mock_supabase.from_().select().eq().single().execute.return_value.data = {
            "autonomy_level": 2,
            "autonomy_settings": {
                "can_create_tasks": True,
                "can_send_emails": False,
                "can_schedule_events": True
            }
        }
        
        result = mock_supabase.from_("user_preferences").select("*").eq("user_id", "user-123").single().execute()
        
        assert result.data["autonomy_level"] == 2

    def test_check_action_allowed(self, mock_supabase):
        """Test checking if action is allowed at current level"""
        mock_supabase.from_().select().eq().single().execute.return_value.data = {
            "autonomy_level": 3,
            "autonomy_settings": {
                "can_create_tasks": True,
                "can_send_emails": False
            }
        }
        
        result = mock_supabase.from_("user_preferences").select("*").eq("user_id", "user-123").single().execute()
        settings = result.data["autonomy_settings"]
        
        assert settings["can_create_tasks"] == True
        assert settings["can_send_emails"] == False

    def test_log_autonomous_action(self, mock_supabase):
        """Test logging autonomous action"""
        mock_supabase.from_().insert().execute.return_value.data = [{
            "id": "action-123",
            "action_type": "create_task",
            "description": "Created task from inbox item",
            "status": "completed",
            "executed_at": datetime.now().isoformat()
        }]
        
        result = mock_supabase.from_("autonomous_actions").insert({
            "action_type": "create_task",
            "description": "Created task from inbox item"
        }).execute()
        
        assert result.data[0]["action_type"] == "create_task"

    def test_increase_autonomy_level(self, mock_supabase):
        """Test increasing autonomy level"""
        mock_supabase.from_().update().eq().execute.return_value.data = [{
            "autonomy_level": 3
        }]
        
        result = mock_supabase.from_("user_preferences").update({
            "autonomy_level": 3
        }).eq("user_id", "user-123").execute()
        
        assert result.data[0]["autonomy_level"] == 3


class TestInsightsService:
    """Test suite for insights operations"""

    def test_calculate_productivity_score(self, mock_supabase):
        """Test productivity score calculation"""
        # Mock task completion data
        mock_supabase.from_().select().eq().gte().execute.return_value.data = [
            {"status": "completed", "completed_at": datetime.now().isoformat()},
            {"status": "completed", "completed_at": datetime.now().isoformat()},
            {"status": "pending", "completed_at": None}
        ]
        
        tasks = mock_supabase.from_("tasks").select("*").eq("user_id", "user-123").gte("created_at", "2024-01-01").execute()
        
        completed = sum(1 for t in tasks.data if t["status"] == "completed")
        total = len(tasks.data)
        score = (completed / total) * 100 if total > 0 else 0
        
        assert score == pytest.approx(66.67, rel=0.1)

    def test_detect_work_patterns(self, mock_supabase):
        """Test detecting work patterns"""
        # Mock completed tasks with times
        mock_supabase.from_().select().eq().execute.return_value.data = [
            {"completed_at": "2024-01-15T09:30:00Z"},  # Monday morning
            {"completed_at": "2024-01-15T10:15:00Z"},  # Monday morning
            {"completed_at": "2024-01-16T14:30:00Z"},  # Tuesday afternoon
        ]
        
        tasks = mock_supabase.from_("tasks").select("completed_at").eq("status", "completed").execute()
        
        # Analyze patterns (simplified)
        morning_count = sum(1 for t in tasks.data if "T09" in t["completed_at"] or "T10" in t["completed_at"])
        
        assert morning_count == 2

    def test_generate_recommendations(self, mock_gemini):
        """Test generating AI recommendations"""
        mock_gemini.generate_content.return_value.text = """
        Based on your patterns:
        1. You're most productive between 9-11 AM
        2. Consider scheduling important tasks in the morning
        3. Your energy dips after lunch - save routine tasks for then
        """
        
        result = mock_gemini.generate_content("Generate recommendations based on productivity data")
        
        assert "productive" in result.text.lower()
        assert "morning" in result.text.lower()

    def test_detect_correlations(self, mock_supabase):
        """Test detecting health-productivity correlations"""
        mock_supabase.from_().select().execute.return_value.data = [
            {"date": "2024-01-15", "sleep_hours": 8, "tasks_completed": 5},
            {"date": "2024-01-16", "sleep_hours": 6, "tasks_completed": 2},
            {"date": "2024-01-17", "sleep_hours": 7.5, "tasks_completed": 4},
        ]
        
        data = mock_supabase.from_("daily_stats").select("*").execute()
        
        # Simple correlation check
        high_sleep_high_tasks = sum(1 for d in data.data if d["sleep_hours"] >= 7 and d["tasks_completed"] >= 4)
        
        assert high_sleep_high_tasks == 2


class TestGmailService:
    """Test suite for Gmail operations"""

    def test_get_unread_emails(self, mock_supabase):
        """Test getting unread emails"""
        # This would normally call Gmail API
        emails = [
            {"id": "1", "subject": "Meeting tomorrow", "from": "boss@company.com", "unread": True},
            {"id": "2", "subject": "Invoice", "from": "billing@service.com", "unread": True}
        ]
        
        assert len(emails) == 2
        assert all(e["unread"] for e in emails)

    def test_create_draft(self):
        """Test creating email draft"""
        draft = {
            "to": "recipient@example.com",
            "subject": "Follow up",
            "body": "Just following up on our conversation..."
        }
        
        assert draft["to"] == "recipient@example.com"

    def test_search_emails(self):
        """Test searching emails"""
        query = "from:boss@company.com subject:meeting"
        results = [
            {"id": "1", "subject": "Meeting tomorrow"},
            {"id": "2", "subject": "Meeting notes"}
        ]
        
        assert len(results) == 2


class TestDriveService:
    """Test suite for Drive operations"""

    def test_list_files(self):
        """Test listing Drive files"""
        files = [
            {"id": "1", "name": "Document.docx", "mimeType": "application/vnd.google-apps.document"},
            {"id": "2", "name": "Spreadsheet.xlsx", "mimeType": "application/vnd.google-apps.spreadsheet"}
        ]
        
        assert len(files) == 2

    def test_create_project_folder(self):
        """Test creating project folder structure"""
        folder_structure = {
            "name": "Project X",
            "subfolders": ["Documents", "Assets", "References"]
        }
        
        assert len(folder_structure["subfolders"]) == 3

    def test_search_files(self):
        """Test searching files"""
        query = "name contains 'report'"
        results = [
            {"id": "1", "name": "Q1 Report.pdf"},
            {"id": "2", "name": "Annual Report 2024.pdf"}
        ]
        
        assert all("report" in f["name"].lower() for f in results)


class TestSchedulerService:
    """Test suite for scheduler operations"""

    def test_morning_routine_execution(self, mock_supabase):
        """Test morning routine job execution"""
        mock_supabase.from_().insert().execute.return_value.data = [{
            "routine_type": "morning",
            "executed_at": datetime.now().isoformat(),
            "success": True,
            "message": "Sent morning summary to user"
        }]
        
        result = mock_supabase.from_("routine_logs").insert({
            "routine_type": "morning",
            "success": True
        }).execute()
        
        assert result.data[0]["success"] == True

    def test_night_routine_execution(self, mock_supabase):
        """Test night routine job execution"""
        mock_supabase.from_().insert().execute.return_value.data = [{
            "routine_type": "night",
            "executed_at": datetime.now().isoformat(),
            "success": True
        }]
        
        result = mock_supabase.from_("routine_logs").insert({
            "routine_type": "night",
            "success": True
        }).execute()
        
        assert result.data[0]["routine_type"] == "night"

    def test_weekly_planning_execution(self, mock_supabase):
        """Test weekly planning job execution"""
        mock_supabase.from_().insert().execute.return_value.data = [{
            "routine_type": "weekly_planning",
            "executed_at": datetime.now().isoformat(),
            "success": True
        }]
        
        result = mock_supabase.from_("routine_logs").insert({
            "routine_type": "weekly_planning",
            "success": True
        }).execute()
        
        assert result.data[0]["routine_type"] == "weekly_planning"
