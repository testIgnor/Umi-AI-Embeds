import re
class Shortcode():
    def __init__(self, Unprompted):
        self.Unprompted = Unprompted
        self.description = """
                            Counts the number of occurances of provided character
                            in the input string
                            """

    def run_block(self, pargs, kwargs, context, content):
        if not content:
            return
        pattern = re.compile(r'<lora:(.+?)>')
        newtext = content
        for x in pattern.findall(content):
            print(x)
            name = x.split(':')[0]
            weight = float(x.split(':')[1])
            newtext = newtext.replace(x, f'{name}:{weight/2}')
        return newtext