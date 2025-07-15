import re
class Shortcode():
    def __init__(self, Unprompted):
        self.Unprompted = Unprompted
        self.description = """
                            Removes a substring from the input string
                            """

    def run_block(self, pargs, kwargs, context, content):
        if not content:
            return
        if len(pargs) == 0:
            self.log.exception('Please supply substrings.')
        new_content = content
        for substring in pargs:
            new_content = new_content.replace(substring, '').strip()
        return new_content