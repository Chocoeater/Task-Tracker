from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Min

from tasks.models import Task

User = get_user_model()


def get_important_task_and_candidates():
    important_tasks = (
        Task.objects.filter(
            status="created", executor__isnull=True, subtasks__status="in_progress"
        )
        .distinct()
        .prefetch_related("subtasks")
    )

    executors = User.objects.annotate(
        active_count=Count(
            "executed_tasks", filter=Q(executed_tasks__status="in_progress")
        )
    )
    executor_load_map = {user.id: user.active_count for user in executors}
    min_load = executors.aggregate(min_val=Min("active_count"))["min_val"] or 0
    least_loaded = executors.filter(active_count=min_load, role="developer")

    response_data = []

    for task in important_tasks:
        candidates = set()

        in_progress_subtusks = task.subtasks.filter(status="in_progress")
        for subtask in in_progress_subtusks:
            executor = subtask.executor
            if executor and executor_load_map.get(executor.id, 0) <= min_load + 2:
                candidates.add(executor.full_name)

        for user in least_loaded:
            candidates.add(user.full_name)

        response_data.append(
            {
                "task_id": task.id,
                "name": task.name,
                "deadline": task.deadline,
                "candidates": list(candidates),
            }
        )
    return response_data


def all_subtasks_is_done(parent_task):
    """True, если все подзадачи выполнены"""
    for subtask in parent_task.subtasks:
        if subtask.status != "done":
            return False
    return True
