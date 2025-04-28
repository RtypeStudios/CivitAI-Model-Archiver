class Version:
    def __init__(self, version_id:int, version_name:str, base_model:str):
        self.id = version_id
        self.name = version_name
        self.base_model = base_model
        self.tasks = []