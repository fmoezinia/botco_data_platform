"""
Task management service for asynchronous processing.
"""
import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from utils.logging import logger
from models import TaskInfo, TaskStatus
from exceptions import TaskError


class TaskManager:
    """Manages asynchronous tasks and their execution."""
    
    def __init__(self, max_workers: int = 4):
        """Initialize task manager."""
        self.tasks: Dict[str, TaskInfo] = {}
        self.task_lock = Lock()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = True
        logger.info(f"Task manager initialized with {max_workers} workers")
    
    def create_task(self, task_type: str, **kwargs) -> str:
        """Create a new task."""
        task_id = str(uuid.uuid4())
        
        with self.task_lock:
            self.tasks[task_id] = TaskInfo(
                task_id=task_id,
                status=TaskStatus.PENDING,
                progress=0.0,
                result=None,
                error=None,
                started_at=None,
                completed_at=None
            )
        
        logger.info(f"Created task {task_id} of type {task_type}")
        return task_id
    
    def update_task_status(self, task_id: str, status: TaskStatus, **kwargs):
        """Update task status."""
        with self.task_lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = status
                
                if 'progress' in kwargs:
                    task.progress = kwargs['progress']
                if 'result' in kwargs:
                    task.result = kwargs['result']
                if 'error' in kwargs:
                    task.error = kwargs['error']
                if status == TaskStatus.RUNNING and not task.started_at:
                    task.started_at = datetime.now()
                elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    task.completed_at = datetime.now()
                
                logger.info(f"Updated task {task_id}: {status} (progress: {task.progress})")
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Get task information."""
        with self.task_lock:
            return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, TaskInfo]:
        """Get all tasks."""
        with self.task_lock:
            return self.tasks.copy()
    
    async def execute_task(self, task_id: str, func: Callable, *args, **kwargs):
        """Execute a task asynchronously."""
        try:
            self.update_task_status(task_id, TaskStatus.RUNNING)
            
            # Run function in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, func, *args, **kwargs)
            
            self.update_task_status(task_id, TaskStatus.COMPLETED, result=result)
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            error_msg = str(e)
            self.update_task_status(task_id, TaskStatus.FAILED, error=error_msg)
            logger.error(f"Task {task_id} failed: {error_msg}")
            raise TaskError(f"Task execution failed: {error_msg}")
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        with self.task_lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                    task.status = TaskStatus.CANCELLED
                    task.completed_at = time.time()
                    logger.info(f"Task {task_id} cancelled")
                    return True
        return False
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks."""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        with self.task_lock:
            tasks_to_remove = []
            for task_id, task in self.tasks.items():
                if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] 
                    and task.completed_at 
                    and (current_time - task.completed_at) > max_age_seconds):
                    tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self.tasks[task_id]
                logger.info(f"Cleaned up old task: {task_id}")
    
    def shutdown(self):
        """Shutdown task manager."""
        self.running = False
        self.executor.shutdown(wait=True)
        logger.info("Task manager shutdown complete")


# Global task manager instance
task_manager = TaskManager()
