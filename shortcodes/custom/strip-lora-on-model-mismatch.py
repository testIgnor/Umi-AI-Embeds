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
                            """

    def run_block(self, pargs, kwargs, context, content):
        if not content:
            return

        model_fname = self.Unprompted.shortcode_user_vars["sd_model"]

        # typical format is filename.safetensors [hash]
        model_name = model_fname.split('.safetensors')[0]

        model_type_file = os.path.join(self.Unprompted.base_dir, 'templates/wildcards/models-to-type.yaml')
        with open(model_type_file, 'r') as f:
            model_dict = yaml.safe_load(f)

        try:
            current_model_type = model_dict[model_name]
        except KeyError as e:
            self.log.exception(f'Model {model_name} does NOT correspond to a known model!')
            return

        pattern = re.compile('<lora:(.+?):')

        lora_association_map = os.path.join(self.Unprompted.base_dir, 'templates/wildcards/used_resources.json')

        with open(lora_association_map, 'r') as f:
            lora_info = json.load(f)

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

            if base_model not in current_model_type:
                # strip the model
                subpattern = re.compile(fr'<lora:{m}(.+?)>')
                content = subpattern.sub('', content).replace('  ', ' ').replace(' ,', ',')
        return content
