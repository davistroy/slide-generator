"""
Async Workflow Utilities for Concurrent Task Execution

Provides utilities for running async tasks with concurrency control,
progress tracking, error handling, and timeout support.

Usage:
    executor = AsyncWorkflowExecutor(max_concurrent=5)

    # Run tasks in parallel with concurrency limit
    results = await executor.run_parallel(tasks)

    # Run tasks sequentially
    results = await executor.run_sequential(tasks)

    # Run with custom semaphore and timeout
    results = await executor.run_with_semaphore(tasks, max_concurrent=3, timeout=60)
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar, Union

from plugin.types import ProgressCallback

T = TypeVar('T')


@dataclass
class TaskResult:
    """Result of a single task execution."""

    task_id: str
    success: bool
    result: Optional[Any] = None
    error: Optional[Exception] = None
    duration: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    @property
    def failed(self) -> bool:
        """Check if task failed."""
        return not self.success


@dataclass
class WorkflowResult:
    """Result of workflow execution."""

    total_tasks: int
    successful: int
    failed: int
    results: List[TaskResult] = field(default_factory=list)
    total_duration: float = 0.0
    errors: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_tasks == 0:
            return 0.0
        return (self.successful / self.total_tasks) * 100

    @property
    def all_succeeded(self) -> bool:
        """Check if all tasks succeeded."""
        return self.failed == 0

    @property
    def any_failed(self) -> bool:
        """Check if any task failed."""
        return self.failed > 0

    def get_successful_results(self) -> List[Any]:
        """Get results from successful tasks only."""
        return [r.result for r in self.results if r.success]

    def get_failed_tasks(self) -> List[TaskResult]:
        """Get failed task results."""
        return [r for r in self.results if r.failed]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_tasks": self.total_tasks,
            "successful": self.successful,
            "failed": self.failed,
            "success_rate": self.success_rate,
            "total_duration": self.total_duration,
            "errors": self.errors,
        }


class AsyncWorkflowExecutor:
    """
    Executor for running async tasks with concurrency control.

    Features:
    - Parallel execution with concurrency limits
    - Sequential execution
    - Progress tracking
    - Error aggregation and partial success handling
    - Per-task and overall timeout support
    - Graceful cancellation

    Args:
        max_concurrent: Default maximum concurrent tasks (default: 5)
        task_timeout: Default timeout per task in seconds (default: None)
        overall_timeout: Default overall timeout in seconds (default: None)
        stop_on_error: Stop execution on first error (default: False)
        progress_callback: Optional callback for progress updates

    Example:
        >>> executor = AsyncWorkflowExecutor(max_concurrent=3)
        >>> tasks = [async_task1(), async_task2(), async_task3()]
        >>> result = await executor.run_parallel(tasks)
        >>> print(f"Success rate: {result.success_rate}%")
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        task_timeout: Optional[float] = None,
        overall_timeout: Optional[float] = None,
        stop_on_error: bool = False,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        """Initialize async workflow executor."""
        self.max_concurrent = max_concurrent
        self.task_timeout = task_timeout
        self.overall_timeout = overall_timeout
        self.stop_on_error = stop_on_error
        self.progress_callback = progress_callback

    async def run_parallel(
        self,
        tasks: List[Awaitable[T]],
        task_ids: Optional[List[str]] = None,
        max_concurrent: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> WorkflowResult:
        """
        Run tasks in parallel with concurrency limit.

        Args:
            tasks: List of awaitable tasks
            task_ids: Optional list of task identifiers
            max_concurrent: Override default max concurrent tasks
            timeout: Override default overall timeout

        Returns:
            WorkflowResult with execution results

        Example:
            >>> tasks = [fetch_data(url) for url in urls]
            >>> result = await executor.run_parallel(tasks, max_concurrent=10)
        """
        return await self.run_with_semaphore(
            tasks=tasks,
            task_ids=task_ids,
            max_concurrent=max_concurrent or self.max_concurrent,
            timeout=timeout or self.overall_timeout,
        )

    async def run_sequential(
        self,
        tasks: List[Awaitable[T]],
        task_ids: Optional[List[str]] = None,
        timeout: Optional[float] = None,
    ) -> WorkflowResult:
        """
        Run tasks sequentially (one at a time).

        Args:
            tasks: List of awaitable tasks
            task_ids: Optional list of task identifiers
            timeout: Override default overall timeout

        Returns:
            WorkflowResult with execution results

        Example:
            >>> tasks = [process_item(item) for item in items]
            >>> result = await executor.run_sequential(tasks)
        """
        return await self.run_with_semaphore(
            tasks=tasks,
            task_ids=task_ids,
            max_concurrent=1,
            timeout=timeout or self.overall_timeout,
        )

    async def run_with_semaphore(
        self,
        tasks: List[Awaitable[T]],
        task_ids: Optional[List[str]] = None,
        max_concurrent: int = 5,
        timeout: Optional[float] = None,
    ) -> WorkflowResult:
        """
        Run tasks with semaphore-based concurrency control.

        Args:
            tasks: List of awaitable tasks
            task_ids: Optional list of task identifiers
            max_concurrent: Maximum concurrent tasks
            timeout: Overall timeout in seconds (None for no timeout)

        Returns:
            WorkflowResult with execution results

        Example:
            >>> result = await executor.run_with_semaphore(
            ...     tasks=[task1(), task2()],
            ...     max_concurrent=1,
            ...     timeout=30.0
            ... )
        """
        # Generate task IDs if not provided
        if task_ids is None:
            task_ids = [f"task-{i}" for i in range(len(tasks))]
        elif len(task_ids) != len(tasks):
            raise ValueError("task_ids length must match tasks length")

        semaphore = asyncio.Semaphore(max_concurrent)
        results: List[TaskResult] = []
        completed = 0
        total = len(tasks)
        start_time = time.time()

        async def run_with_semaphore_and_tracking(
            task: Awaitable[T],
            task_id: str
        ) -> TaskResult:
            """Run single task with semaphore and tracking."""
            nonlocal completed

            async with semaphore:
                task_start = time.time()
                task_result = TaskResult(
                    task_id=task_id,
                    success=False,
                    started_at=task_start,
                )

                try:
                    # Apply task timeout if configured
                    if self.task_timeout:
                        result = await asyncio.wait_for(task, timeout=self.task_timeout)
                    else:
                        result = await task

                    task_result.success = True
                    task_result.result = result

                except asyncio.TimeoutError as e:
                    task_result.error = e
                    task_result.success = False

                except Exception as e:
                    task_result.error = e
                    task_result.success = False

                    # Stop on error if configured
                    if self.stop_on_error:
                        raise

                finally:
                    task_result.completed_at = time.time()
                    task_result.duration = task_result.completed_at - task_start

                    # Update progress
                    completed += 1
                    if self.progress_callback:
                        progress = (completed / total) * 100
                        self.progress_callback(
                            f"Completed {completed}/{total} tasks",
                            progress
                        )

                return task_result

        # Create wrapped tasks
        wrapped_tasks = [
            run_with_semaphore_and_tracking(task, task_id)
            for task, task_id in zip(tasks, task_ids)
        ]

        # Run all tasks with optional overall timeout
        try:
            if timeout:
                results = await asyncio.wait_for(
                    asyncio.gather(*wrapped_tasks, return_exceptions=False),
                    timeout=timeout
                )
            else:
                results = await asyncio.gather(*wrapped_tasks, return_exceptions=False)

        except asyncio.TimeoutError:
            # Overall timeout - cancel remaining tasks
            for task in wrapped_tasks:
                if not task.done():
                    task.cancel()

            # Gather results from completed tasks
            results = []
            for task in wrapped_tasks:
                if task.done():
                    try:
                        results.append(task.result())
                    except Exception:
                        pass

        except Exception as e:
            # Error in execution - gather partial results
            results = []
            for task in wrapped_tasks:
                if task.done():
                    try:
                        results.append(task.result())
                    except Exception:
                        pass

        # Build workflow result
        total_duration = time.time() - start_time
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        errors = [str(r.error) for r in results if r.error]

        return WorkflowResult(
            total_tasks=total,
            successful=successful,
            failed=failed,
            results=results,
            total_duration=total_duration,
            errors=errors,
        )

    async def run_batched(
        self,
        items: List[Any],
        processor: Callable[[Any], Awaitable[T]],
        batch_size: int = 10,
        max_concurrent: Optional[int] = None,
    ) -> WorkflowResult:
        """
        Run tasks in batches with concurrency control.

        Useful for processing large lists with backpressure control.

        Args:
            items: List of items to process
            processor: Async function to process each item
            batch_size: Number of items per batch
            max_concurrent: Max concurrent tasks per batch

        Returns:
            WorkflowResult with all results

        Example:
            >>> async def process_url(url):
            ...     return await fetch(url)
            >>> result = await executor.run_batched(
            ...     urls,
            ...     processor=process_url,
            ...     batch_size=50
            ... )
        """
        all_results: List[TaskResult] = []
        total_successful = 0
        total_failed = 0
        all_errors: List[str] = []
        start_time = time.time()

        # Process in batches
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            tasks = [processor(item) for item in batch]
            task_ids = [f"batch-{i//batch_size}-item-{j}" for j in range(len(batch))]

            batch_result = await self.run_with_semaphore(
                tasks=tasks,
                task_ids=task_ids,
                max_concurrent=max_concurrent or self.max_concurrent,
            )

            all_results.extend(batch_result.results)
            total_successful += batch_result.successful
            total_failed += batch_result.failed
            all_errors.extend(batch_result.errors)

            # Report batch progress
            if self.progress_callback:
                progress = ((i + len(batch)) / len(items)) * 100
                self.progress_callback(
                    f"Processed {i + len(batch)}/{len(items)} items",
                    progress
                )

        total_duration = time.time() - start_time

        return WorkflowResult(
            total_tasks=len(items),
            successful=total_successful,
            failed=total_failed,
            results=all_results,
            total_duration=total_duration,
            errors=all_errors,
        )

    async def run_with_retry(
        self,
        task: Awaitable[T],
        task_id: str = "task",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_multiplier: float = 2.0,
    ) -> TaskResult:
        """
        Run a single task with retry logic.

        Args:
            task: Awaitable task to run
            task_id: Task identifier
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay in seconds
            backoff_multiplier: Backoff multiplier for exponential delay

        Returns:
            TaskResult with execution result

        Example:
            >>> result = await executor.run_with_retry(
            ...     fetch_data(),
            ...     max_retries=5,
            ...     retry_delay=2.0
            ... )
        """
        start_time = time.time()
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                if self.task_timeout:
                    result = await asyncio.wait_for(task, timeout=self.task_timeout)
                else:
                    result = await task

                # Success
                duration = time.time() - start_time
                return TaskResult(
                    task_id=task_id,
                    success=True,
                    result=result,
                    duration=duration,
                    started_at=start_time,
                    completed_at=time.time(),
                )

            except Exception as e:
                last_error = e

                # Don't wait after last attempt
                if attempt < max_retries:
                    delay = retry_delay * (backoff_multiplier ** attempt)
                    await asyncio.sleep(delay)

        # All retries exhausted
        duration = time.time() - start_time
        return TaskResult(
            task_id=task_id,
            success=False,
            error=last_error,
            duration=duration,
            started_at=start_time,
            completed_at=time.time(),
        )


# Convenience functions

async def run_parallel(
    tasks: List[Awaitable[T]],
    max_concurrent: int = 5,
    timeout: Optional[float] = None,
) -> WorkflowResult:
    """
    Run tasks in parallel with concurrency limit (convenience function).

    Args:
        tasks: List of awaitable tasks
        max_concurrent: Maximum concurrent tasks
        timeout: Overall timeout in seconds

    Returns:
        WorkflowResult with execution results

    Example:
        >>> from plugin.lib.async_workflow import run_parallel
        >>> result = await run_parallel([task1(), task2()], max_concurrent=2)
    """
    executor = AsyncWorkflowExecutor(max_concurrent=max_concurrent)
    return await executor.run_parallel(tasks, timeout=timeout)


async def run_sequential(
    tasks: List[Awaitable[T]],
    timeout: Optional[float] = None,
) -> WorkflowResult:
    """
    Run tasks sequentially (convenience function).

    Args:
        tasks: List of awaitable tasks
        timeout: Overall timeout in seconds

    Returns:
        WorkflowResult with execution results

    Example:
        >>> from plugin.lib.async_workflow import run_sequential
        >>> result = await run_sequential([task1(), task2()])
    """
    executor = AsyncWorkflowExecutor(max_concurrent=1)
    return await executor.run_sequential(tasks, timeout=timeout)


async def run_batched(
    items: List[Any],
    processor: Callable[[Any], Awaitable[T]],
    batch_size: int = 10,
    max_concurrent: int = 5,
) -> WorkflowResult:
    """
    Run tasks in batches (convenience function).

    Args:
        items: List of items to process
        processor: Async function to process each item
        batch_size: Number of items per batch
        max_concurrent: Max concurrent tasks per batch

    Returns:
        WorkflowResult with all results

    Example:
        >>> async def process(item):
        ...     return await do_something(item)
        >>> result = await run_batched(items, process, batch_size=20)
    """
    executor = AsyncWorkflowExecutor(max_concurrent=max_concurrent)
    return await executor.run_batched(items, processor, batch_size)
