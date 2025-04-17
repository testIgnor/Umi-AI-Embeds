
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
        try:
            char = pargs[0]
        except IndexError as e:
            self.log.exception('Please supply a character.')
        return content.count(char)