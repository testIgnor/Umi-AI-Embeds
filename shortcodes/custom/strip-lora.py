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
        return pattern.sub('', content).replace('  ', ' ').replace(' ,', ',')