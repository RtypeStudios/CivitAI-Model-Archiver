from common.base_task import BaseTask

class CompositeTask(BaseTask):
    '''
    Composite task to run multiple tasks in sequence.
    '''
    def __init__(self, tasks:list[BaseTask], name:str = "Composite Task"):
        super().__init__(name, "", "")
        self.tasks = tasks
        
    def run(self) -> bool:
        '''
        Run the composite task.
        '''
        for task in self.tasks:
            result = task.run()
            if result is False:
                self.logger.error("Task %s failed, exiting chain.", task.name)
                return False