"""Module with Celery configurations to Euromillions Results worker."""
from kombu import Queue

task_acks_late = True

worker_prefetch_multiplier = 1

task_queues = [Queue(name="euro")]

result_expires = 60 * 60 * 48  # 48 hours in seconds
