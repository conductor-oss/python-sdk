from conductor.client.http.models import PollData


class PollDataAdapter(PollData):
    def __init__(self, queue_name=None, domain=None, worker_id=None, last_poll_time=None):
        super().__init__(domain=domain, last_poll_time=last_poll_time, queue_name=queue_name, worker_id=worker_id)
