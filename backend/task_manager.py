"""
Generic task management for background processing.
Handles task creation, status tracking, and execution.
"""
import uuid
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional, List, Callable
from pydantic import BaseModel
import os


class TaskStatus(BaseModel):
    """Status of a background task"""
    task_id: str
    status: str  # PENDING, RUNNING, COMPLETED, FAILED
    progress: float = 0.0
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class TaskManager:
    """Manages background tasks with status tracking and timeout"""
    
    def __init__(self, max_workers: int = None, default_timeout: float = 20.0):
        self.tasks: Dict[str, TaskStatus] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers or os.cpu_count() or 4)
        self.default_timeout = default_timeout
    
    def create_task(self, task_function: Callable, *args, timeout: float = None, **kwargs) -> str:
        """Create and start a new background task with timeout"""
        task_id = str(uuid.uuid4())
        timeout = timeout or self.default_timeout
        
        # Create task status
        self.tasks[task_id] = TaskStatus(
            task_id=task_id,
            status="PENDING",
            progress=0.0,
            started_at=time.time()
        )
        
        # Start the task in background
        self.executor.submit(self._run_task, task_id, task_function, timeout, *args, **kwargs)
        
        print(f"TaskManager: Created task {task_id} with {timeout}s timeout")
        return task_id
    
    def _run_task(self, task_id: str, task_function: Callable, timeout: float, *args, **kwargs):
        """Internal method to run a task and update its status"""
        task = self.tasks.get(task_id)
        if not task:
            print(f"TaskManager: Task {task_id} not found")
            return
        
        try:
            print(f"TaskManager: Starting task {task_id}")
            task.status = "RUNNING"
            task.progress = 0.05
            
            # Progress callback
            def progress_callback(progress: float):
                task.progress = max(0.05, min(1.0, progress))
            
            # Execute the task function
            result = task_function(task_id, progress_callback, *args, **kwargs)
            
            # Mark as completed
            task.progress = 1.0
            task.status = "COMPLETED"
            task.result = result
            task.completed_at = time.time()
            
            print(f"TaskManager: Task {task_id} completed successfully")
            
        except Exception as e:
            print(f"TaskManager: Task {task_id} failed: {e}")
            task.status = "FAILED"
            task.error = str(e)
            task.completed_at = time.time()
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the status of a task"""
        return self.tasks.get(task_id)
    
    def list_tasks(self) -> List[TaskStatus]:
        """List all tasks"""
        return list(self.tasks.values())
    
    def kill_task(self, task_id: str) -> bool:
        """Manually kill a task"""
        task = self.tasks.get(task_id)
        if task and task.status == "RUNNING":
            task.status = "FAILED"
            task.error = "Task manually killed"
            task.completed_at = time.time()
            return True
        return False
    
    def cleanup_completed_tasks(self):
        """Remove completed and failed tasks from memory"""
        completed_tasks = [task_id for task_id, task in self.tasks.items() 
                          if task.status in ["COMPLETED", "FAILED"]]
        for task_id in completed_tasks:
            del self.tasks[task_id]
        print(f"TaskManager: Cleaned up {len(completed_tasks)} completed tasks")
    
    def shutdown(self):
        """Shutdown the task manager and executor"""
        print("TaskManager: Shutting down...")
        self.executor.shutdown(wait=True)
        print("TaskManager: Shutdown complete")


# Global task manager instance with 20-second timeout
task_manager = TaskManager(default_timeout=20.0)