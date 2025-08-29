from conductor.client.codegen.models.task_details import TaskDetails


class TaskDetailsAdapter(TaskDetails):
    def put_output_item(self, key, output_item):
        """Adds an item to the output dictionary.

        :param key: The key for the output item
        :param output_item: The value to add
        :return: self
        """
        if self._output is None:
            self._output = {}
        self._output[key] = output_item
        return self
