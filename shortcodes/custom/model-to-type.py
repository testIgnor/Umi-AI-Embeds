import yaml
import os

class Shortcode():
    def __init__(self, Unprompted):
        self.Unprompted = Unprompted
        self.description = """
                            Identifies model type by lookup table
                            """

    def run_atomic(self, pargs, kwargs, context):

        model_fname = self.Unprompted.shortcode_user_vars["sd_model"]

        # typical format is filename.safetensors [hash]
        model_name = model_fname.split('.safetensors')[0]

        model_type_file = os.path.join(self.Unprompted.base_dir, 'templates/wildcards/models-to-type.yaml')
        with open(model_type_file, 'r') as f:
            model_dict = yaml.safe_load(f)

        try:
            model_type = model_dict[model_name]
        except KeyError as e:
            self.log.exception(f'Model {model_name} does NOT correspond to a known model!')
            return
        return model_type
