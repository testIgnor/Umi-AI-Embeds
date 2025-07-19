import re
class Shortcode():
    def __init__(self, Unprompted):
        self.Unprompted = Unprompted
        self.description = """
                            Multiplies LORA weights by supplied factor
                            """

    def run_block(self, pargs, kwargs, context, content):
        if not content:
            return
        try:
            factor = float(pargs[0])
        except IndexError as e:
            self.log.exception('Please supply a number from 0.0 - 1.0 or 0 - 100')

        if factor > 1:
            factor = factor / 100

        pattern = re.compile(r'<lora:(.+?)>')
        newtext = content
        for x in pattern.findall(content):
            name = x.split(':')[0]
            weight = float(x.split(':')[1])
            newtext = newtext.replace(x, f'{name}:{weight*factor:.2f}')
        return newtext