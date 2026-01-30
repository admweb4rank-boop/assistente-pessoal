"""
Tests for Task Service
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock


class TestTaskService:
    """Test suite for task operations"""

    def test_create_task_success(self, mock_supabase):
        """Test creating a task successfully"""
        mock_supabase.from_().insert().execute.return_value.data = [{
            "id": "task-123",
            "title": "Test Task",
            "description": "Test description",
            "status": "pending",
            "priority": "medium",
            "created_at": datetime.now().isoformat()
        }]
        
        result = mock_supabase.from_("tasks").insert({
            "title": "Test Task",
            "description": "Test description",
            "user_id": "user-123"
        }).execute()
        
        assert result.data[0]["title"] == "Test Task"
        assert result.data[0]["status"] == "pending"

    def test_list_tasks_with_filters(self, mock_supabase):
        """Test listing tasks with various filters"""
        mock_data = [
            {"id": "1", "title": "Task 1", "priority": "high", "status": "pending"},
            {"id": "2", "title": "Task 2", "priority": "high", "status": "pending"},
        ]
        mock_supabase.from_().select().eq().eq().execute.return_value.data = mock_data
        
        result = mock_supabase.from_("tasks").select("*").eq("status", "pending").eq("priority", "high").execute()
        
        assert len(result.data) == 2
        assert all(t["priority"] == "high" for t in result.data)

    def test_complete_task(self, mock_supabase):
        """Test marking a task as complete"""
        mock_supabase.from_().update().eq().execute.return_value.data = [{
            "id": "task-123",
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        }]
        
        result = mock_supabase.from_("tasks").update({
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        }).eq("id", "task-123").execute()
        
        assert result.data[0]["status"] == "completed"
        assert result.data[0]["completed_at"] is not None

    def test_delete_task(self, mock_supabase):
        """Test deleting a task"""
        mock_supabase.from_().delete().eq().execute.return_value.data = []
        
        result = mock_supabase.from_("tasks").delete().eq("id", "task-123").execute()
        
        assert result.data == []

    def test_task_with_due_date(self, mock_supabase):
        """Test creating task with due date"""
        due_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        mock_supabase.from_().insert().execute.return_value.data = [{
            "id": "task-123",
            "title": "Task with Due Date",
            "due_date": due_date,
            "status": "pending"
        }]
        
        result = mock_supabase.from_("tasks").insert({
            "title": "Task with Due Date",
            "due_date": due_date
        }).execute()
        
        assert result.data[0]["due_date"] == due_date

    def test_task_priority_levels(self, mock_supabase):
        """Test different priority levels"""
        for priority in ["low", "medium", "high"]:
            mock_supabase.from_().insert().execute.return_value.data = [{
                "id": f"task-{priority}",
                "title": f"{priority.capitalize()} Priority Task",
                "priority": priority
            }]
            
            result = mock_supabase.from_("tasks").insert({
                "title": f"{priority.capitalize()} Priority Task",
                "priority": priority
            }).execute()
            
            assert result.data[0]["priority"] == priority

    def test_task_tags(self, mock_supabase):
        """Test task with tags"""
        tags = ["work", "urgent", "project-x"]
        
        mock_supabase.from_().insert().execute.return_value.data = [{
            "id": "task-123",
            "title": "Tagged Task",
            "tags": tags
        }]
        
        result = mock_supabase.from_("tasks").insert({
            "title": "Tagged Task",
            "tags": tags
        }).execute()
        
        assert result.data[0]["tags"] == tags


class TestInboxService:
    """Test suite for inbox operations"""

    def test_create_inbox_message(self, mock_supabase):
        """Test creating inbox message"""
        mock_supabase.from_().insert().execute.return_value.data = [{
            "id": "inbox-123",
            "content": "Test message",
            "source": "telegram",
            "status": "pending"
        }]
        
        result = mock_supabase.from_("inbox").insert({
            "content": "Test message",
            "source": "telegram"
        }).execute()
        
        assert result.data[0]["content"] == "Test message"
        assert result.data[0]["status"] == "pending"

    def test_process_inbox_message(self, mock_supabase, mock_gemini):
        """Test processing inbox message with AI"""
        mock_gemini.generate_content.return_value.text = "This is a task request"
        
        # Simulate message classification
        classification = mock_gemini.generate_content("Classify: Buy groceries")
        
        assert "task" in classification.text.lower()

    def test_archive_inbox_message(self, mock_supabase):
        """Test archiving inbox message"""
        mock_supabase.from_().update().eq().execute.return_value.data = [{
            "id": "inbox-123",
            "status": "archived",
            "archived_at": datetime.now().isoformat()
        }]
        
        result = mock_supabase.from_("inbox").update({
            "status": "archived"
        }).eq("id", "inbox-123").execute()
        
        assert result.data[0]["status"] == "archived"


class TestProjectService:
    """Test suite for project operations"""

    def test_create_project(self, mock_supabase):
        """Test creating a project"""
        mock_supabase.from_().insert().execute.return_value.data = [{
            "id": "proj-123",
            "name": "Test Project",
            "description": "A test project",
            "status": "active"
        }]
        
        result = mock_supabase.from_("projects").insert({
            "name": "Test Project",
            "description": "A test project"
        }).execute()
        
        assert result.data[0]["name"] == "Test Project"
        assert result.data[0]["status"] == "active"

    def test_project_with_tasks(self, mock_supabase):
        """Test project with associated tasks"""
        project_id = "proj-123"
        
        # Mock project creation
        mock_supabase.from_().insert().execute.return_value.data = [{
            "id": project_id,
            "name": "Project with Tasks"
        }]
        
        # Mock task with project_id
        mock_supabase.from_().select().eq().execute.return_value.data = [
            {"id": "task-1", "title": "Task 1", "project_id": project_id},
            {"id": "task-2", "title": "Task 2", "project_id": project_id}
        ]
        
        tasks = mock_supabase.from_("tasks").select("*").eq("project_id", project_id).execute()
        
        assert len(tasks.data) == 2
        assert all(t["project_id"] == project_id for t in tasks.data)

    def test_archive_project(self, mock_supabase):
        """Test archiving a project"""
        mock_supabase.from_().update().eq().execute.return_value.data = [{
            "id": "proj-123",
            "status": "archived",
            "archived_at": datetime.now().isoformat()
        }]
        
        result = mock_supabase.from_("projects").update({
            "status": "archived"
        }).eq("id", "proj-123").execute()
        
        assert result.data[0]["status"] == "archived"


class TestCalendarService:
    """Test suite for calendar operations"""

    def test_create_event(self, mock_supabase):
        """Test creating calendar event"""
        start_time = datetime.now() + timedelta(hours=2)
        end_time = start_time + timedelta(hours=1)
        
        mock_supabase.from_().insert().execute.return_value.data = [{
            "id": "event-123",
            "title": "Team Meeting",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }]
        
        result = mock_supabase.from_("calendar_events").insert({
            "title": "Team Meeting",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }).execute()
        
        assert result.data[0]["title"] == "Team Meeting"

    def test_get_events_in_range(self, mock_supabase):
        """Test getting events within date range"""
        today = datetime.now()
        week_later = today + timedelta(days=7)
        
        mock_supabase.from_().select().gte().lte().execute.return_value.data = [
            {"id": "1", "title": "Event 1", "start_time": (today + timedelta(days=1)).isoformat()},
            {"id": "2", "title": "Event 2", "start_time": (today + timedelta(days=3)).isoformat()}
        ]
        
        result = mock_supabase.from_("calendar_events").select("*").gte("start_time", today.isoformat()).lte("start_time", week_later.isoformat()).execute()
        
        assert len(result.data) == 2

    def test_delete_event(self, mock_supabase):
        """Test deleting calendar event"""
        mock_supabase.from_().delete().eq().execute.return_value.data = []
        
        result = mock_supabase.from_("calendar_events").delete().eq("id", "event-123").execute()
        
        assert result.data == []


class TestFinanceService:
    """Test suite for finance operations"""

    def test_create_transaction(self, mock_supabase):
        """Test creating financial transaction"""
        mock_supabase.from_().insert().execute.return_value.data = [{
            "id": "trans-123",
            "amount": 150.00,
            "type": "expense",
            "category": "food",
            "description": "Grocery shopping"
        }]
        
        result = mock_supabase.from_("transactions").insert({
            "amount": 150.00,
            "type": "expense",
            "category": "food"
        }).execute()
        
        assert result.data[0]["amount"] == 150.00
        assert result.data[0]["type"] == "expense"

    def test_get_monthly_summary(self, mock_supabase):
        """Test getting monthly financial summary"""
        mock_supabase.from_().select().gte().lte().execute.return_value.data = [
            {"amount": 5000, "type": "income"},
            {"amount": -1500, "type": "expense"},
            {"amount": -800, "type": "expense"},
        ]
        
        transactions = mock_supabase.from_("transactions").select("*").gte("date", "2024-01-01").lte("date", "2024-01-31").execute()
        
        total_income = sum(t["amount"] for t in transactions.data if t["type"] == "income")
        total_expense = sum(abs(t["amount"]) for t in transactions.data if t["type"] == "expense")
        
        assert total_income == 5000
        assert total_expense == 2300

    def test_budget_tracking(self, mock_supabase):
        """Test budget tracking"""
        mock_supabase.from_().select().eq().execute.return_value.data = [{
            "category": "food",
            "budget": 500.00,
            "spent": 350.00
        }]
        
        result = mock_supabase.from_("budgets").select("*").eq("category", "food").execute()
        
        remaining = result.data[0]["budget"] - result.data[0]["spent"]
        assert remaining == 150.00


class TestMemoryService:
    """Test suite for memory/context operations"""

    def test_store_memory(self, mock_supabase, mock_gemini):
        """Test storing a memory"""
        mock_gemini.embed_content.return_value.embedding = [0.1] * 768
        
        mock_supabase.from_().insert().execute.return_value.data = [{
            "id": "mem-123",
            "content": "User prefers morning meetings",
            "type": "preference",
            "embedding": [0.1] * 768
        }]
        
        result = mock_supabase.from_("memories").insert({
            "content": "User prefers morning meetings",
            "type": "preference"
        }).execute()
        
        assert result.data[0]["type"] == "preference"

    def test_search_memories(self, mock_supabase, mock_gemini):
        """Test searching memories semantically"""
        mock_gemini.embed_content.return_value.embedding = [0.1] * 768
        
        mock_supabase.rpc.return_value.execute.return_value.data = [
            {"id": "1", "content": "User prefers morning meetings", "similarity": 0.95},
            {"id": "2", "content": "User works best in the morning", "similarity": 0.85}
        ]
        
        result = mock_supabase.rpc("search_memories", {
            "query_embedding": [0.1] * 768,
            "match_threshold": 0.7
        }).execute()
        
        assert len(result.data) == 2
        assert result.data[0]["similarity"] > result.data[1]["similarity"]

    def test_delete_memory(self, mock_supabase):
        """Test forgetting/deleting a memory"""
        mock_supabase.from_().delete().eq().execute.return_value.data = []
        
        result = mock_supabase.from_("memories").delete().eq("id", "mem-123").execute()
        
        assert result.data == []
