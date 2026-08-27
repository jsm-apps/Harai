import os 

class PromptUtil():
    def __init__(self):
        self.x = 5

    def load_from_file(self, filename, **placeholders):
        #print("Looking for:", path)
        if not os.path.isfile(filename):
            raise IOError("Prompt File Not Found: %s" % filename)
        with open(filename, "r") as f:
            template = f.read()
            
        for key, value in placeholders.items():
            template = template.replace("{" + key + "}", str(value))
        
        return template
