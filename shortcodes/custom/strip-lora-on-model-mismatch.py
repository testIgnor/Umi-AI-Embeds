import re
import os
import json
import yaml

class Shortcode():
    def __init__(self, Unprompted):
        self.Unprompted = Unprompted
        self.description = """
                            Checks if Loras in the prompt use the same
                            base model as the current model, then
                            strips off mismatching Loras.
                            The current sd_model type MUST be present in the
                            user variable sd_model_type, else
                            the defualt value of 'illu' will be used
                            """

    def run_block(self, pargs, kwargs, context, content):
        if not content:
            return

        try:
            current_model_type = self.Unprompted.shortcode_user_vars["sd_model_type"]
        except KeyError:
            current_model_type = 'illu'

        pattern = re.compile('<lora:(.+?):')

        lora_association_map = os.path.join(self.Unprompted.base_dir, 'templates/wildcards/used_resources.json')

        base_model_to_model_type_map = os.path.join(self.Unprompted.base_dir, 'templates/wildcards/admissible_base_model_types.json')

        with open(lora_association_map, 'r') as f:
            lora_info = json.load(f)
        with open(base_model_to_model_type_map, 'r') as f:
            base_model_to_model_type = json.load(f)

        matches = [ x.strip() for x in pattern.findall(content) ]

        for m in matches:
            try:
                base_model = lora_info['forward'][m]['baseModel']
            except KeyError as e:
                model_fname_candidates = lora_info['reverse'][m]

                if len(model_fname_candidates) > 1:
                    self.log.exception(f'Many-to-one Mapping for {m}')
                    return
                else:
                    model_fname = model_fname_candidates[0]
                    base_model = lora_info['forward'][model_fname]['baseModel']
            # convert base_model to model_type
            admissible_model_types = base_model_to_model_type[base_model]
            if current_model_type not in admissible_model_types:
                # strip the model
                subpattern = re.compile(fr'<lora:{m}(.+?)>')
                content = subpattern.sub('', content).replace('  ', ' ').replace(' ,', ',')
        return content
