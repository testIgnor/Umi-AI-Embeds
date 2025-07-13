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
        try:
            substring = pargs[0]
        except IndexError as e:
            self.log.exception('Please supply a substring.')
        if substring not in content:
            return content
        return content.replace(substring, '').strip()