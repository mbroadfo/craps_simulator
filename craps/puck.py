class Puck:
    def __init__(self):
        self.position = "Off"
        self.point = None

    def set_point(self, value):
        self.position = "On"
        self.point = value

    def reset(self):
        self.position = "Off"
        self.point = None