class Notes():
    def __init__(self):
        self.notes = []
        
    def add_note(self, note):
        self.notes.append(note)
        
    def get_notes(self):
        rtndata = "No current notes."
        if len(self.notes) > 0:
            rtndata = "\n\n".join(self.notes)
        return rtndata
