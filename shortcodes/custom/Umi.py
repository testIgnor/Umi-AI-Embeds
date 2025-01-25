import os
import random
import inspect
import pathlib
import re
import time
import glob
from random import choices
import yaml

ALL_KEY = 'all yaml files'

def get_index(items, item):
    try:
        return items.index(item)
    except Exception:
        return None


def parse_tag(tag):
    return tag.replace("__", "").replace('<', '').replace('>', '').strip()


def read_file_lines(file):
    f_lines = file.read().splitlines()
    lines = []
    for line in f_lines:
        line = line.strip()
        # Check if we have a line that is not empty or starts with an #
        if line and not line.startswith('#'):
            lines.append(line)
    return lines


# Wildcards
class TagLoader:
    files = []
    wildcard_location = os.path.join(
        pathlib.Path(inspect.getfile(lambda: None)).parent.parent, "wildcards")
    loaded_tags = {}
    missing_tags = set()

    def __init__(self, options):
        self.wildcard_location = dict(options).get('wildcard_path')
        self.ignore_paths = dict(options).get('ignore_paths', True)
        self.all_txt_files = glob.glob(os.path.join(self.wildcard_location, '**/*.txt'), recursive=True)
        self.all_yaml_files = glob.glob(os.path.join(self.wildcard_location, '**/*.yaml'), recursive=True)
        self.txt_basename_to_path = {os.path.basename(file).lower().split('.')[0]: file for file in self.all_txt_files}
        self.yaml_basename_to_path = {os.path.basename(file).lower().split('.')[0]: file for file in self.all_yaml_files}
        self.verbose = dict(options).get('verbose', False)
        self.debug = dict(options).get('debug', False)

    def load_tags(self, file_path, verbose=False, cache_files=True):
        if cache_files and self.loaded_tags.get(file_path):
            return self.loaded_tags.get(file_path)

        txt_full_file_path = os.path.join(self.wildcard_location, f'{file_path}.txt')
        yaml_full_file_path = os.path.join(self.wildcard_location, f'{file_path}.yaml')
        txt_file_match = self.txt_basename_to_path.get(file_path.lower()) or txt_full_file_path
        yaml_file_match = self.yaml_basename_to_path.get(file_path.lower()) or yaml_full_file_path
        txt_file_path = txt_file_match if self.ignore_paths else txt_full_file_path
        yaml_file_path = yaml_file_match if self.ignore_paths else yaml_full_file_path

        if (file_path == ALL_KEY):
            key = ALL_KEY
        else:
            if (self.ignore_paths):
                basename = os.path.basename(file_path.lower())
            key = file_path

        if self.wildcard_location and os.path.isfile(txt_file_path):
            with open(txt_file_path, encoding="utf8") as file:
                self.files.append(f"{file_path}.txt")
                self.loaded_tags[key] = read_file_lines(file)
                if (self.ignore_paths):
                    if (self.loaded_tags.get(basename)):
                        print(f'UmiAI: Warning: Duplicate filename "{basename}" in {txt_file_path}. Only the last one will be used.')
                    self.loaded_tags[basename] = self.loaded_tags[key]

        if key is ALL_KEY and self.wildcard_location:
            files = glob.glob(os.path.join(self.wildcard_location, '**/*.yaml'), recursive=True)
            output = {}
            for file in files:
                with open(file, encoding="utf8") as file:
                    self.files.append(f"{file_path}.yaml")
                    path = os.path.relpath(file.name)
                    try:
                        data = yaml.safe_load(file)
                        if not isinstance(data, dict) and verbose:
                            print(f'Warning: Missing contents in {path}')
                            continue

                        for item in data:
                            if (hasattr(output, item) and verbose):
                                print(f'Warning: Duplicate key "{item}" in {path}')
                            if data[item] and 'Tags' in data[item]:
                                if not isinstance(data[item]['Tags'], list):
                                    if verbose:
                                        print(f'Warning: No tags found in at item "{item}" (add at least one tag to it) in {path}')
                                    continue
                                output[item] = {
                                    x.lower().strip()
                                    for i, x in enumerate(data[item]['Tags'])
                                }
                            else:
                                if verbose: print(f'Warning: No "Tags" section found in at item "{item}" in {path}')
                    except yaml.YAMLError as exc:
                        print(exc)
            self.loaded_tags[key] = output

        if self.wildcard_location and os.path.isfile(yaml_file_path):
            with open(yaml_file_path, encoding="utf8") as file:
                self.files.append(f"{file_path}.yaml")
                try:
                    data = yaml.safe_load(file)
                    output = {}
                    for item in data:
                        output[item] = {
                            x.lower().strip()
                            for i, x in enumerate(data[item]['Tags'])
                        }
                    self.loaded_tags[key] = output
                    if (self.ignore_paths):
                        if (self.loaded_tags.get(basename)):
                            print(f'UmiAI: Warning: Duplicate filename "{basename}" in {yaml_file_path}. Only the last one will be used.')
                        self.loaded_tags[basename] = self.loaded_tags[key]
                except yaml.YAMLError as exc:
                    print(exc)

        if not os.path.isfile(yaml_file_path) and not os.path.isfile(
                txt_file_path):
            self.missing_tags.add(file_path)

        return self.loaded_tags.get(key) if self.loaded_tags.get(
            key) else []


# <yaml:[tag]> notation
class TagSelector:

    def __init__(self, tag_loader, options):
        self.tag_loader = tag_loader
        self.previously_selected_tags = {}
        self.used_values = {}
        self.selected_options = dict(options).get('selected_options', {})
        self.verbose = dict(options).get('verbose', False)
        self.debug = dict(options).get('debug', False)
        self.cache_files = dict(options).get('cache_files', True)
        self.used_tags = set()

    def get_used_tags(self):
        return self.used_tags

    def select_value_from_candidates(self, candidates):
        if len(candidates) == 1:
            if self.verbose: print(f'UmiAI: Only one value {candidates} found. Returning it.')
            self.used_values[candidates[0]] = True
            return candidates[0]
        if len(candidates) > 1:
            for candidate in candidates:
                if candidate not in self.used_values:
                    self.used_values[candidate] = True
                    return candidate
            random.shuffle(candidates)
            if self.verbose: print(f'UmiAI: All values in {candidates} were used. Returning random tag ({candidates[0]}).')
            return candidates[0]

    def get_tag_choice(self, parsed_tag, tags):
        if self.selected_options.get(parsed_tag.lower()) is not None:
            return tags[self.selected_options.get(parsed_tag.lower())]
        if len(tags) == 0:
            return ""
        shuffled_tags = list(tags)
        random.shuffle(shuffled_tags)
        return self.select_value_from_candidates(shuffled_tags)

    def get_tag_group_choice(self, parsed_tag, groups, tags):
        if self.debug:
            print('selected_options', self.selected_options)
            print('groups', groups)
            print('parsed_tag', parsed_tag)
        neg_groups = [x.strip().lower() for x in groups if x.startswith('--')]
        neg_groups_set = {x.replace('--', '') for x in neg_groups}
        any_groups = [{y.strip()
                       for i, y in enumerate(x.lower().split('|'))}
                      for x in groups if '|' in x]
        pos_groups = [
            x.strip().lower() for x in groups
            if not x.startswith('--') and '|' not in x
        ]
        pos_groups_set = {x for x in pos_groups}
        if self.debug:
            print('pos_groups', pos_groups_set)
            print('negative_groups', neg_groups_set)
            print('any_groups', any_groups)
        candidates = []
        for tag in tags:
            tag_set = tags[tag]
            if len(list(pos_groups_set & tag_set)) != len(pos_groups_set):
                continue
            if len(list(neg_groups_set & tag_set)) > 0:
                continue
            if len(any_groups) > 0:
                any_groups_found = 0
                for any_group in any_groups:
                    if len(list(any_group & tag_set)) == 0:
                        break
                    any_groups_found += 1
                if len(any_groups) != any_groups_found:
                    continue
            candidates.append(tag)
        if len(candidates) > 0:
            self.used_tags = self.used_tags.union(pos_groups_set)
            if self.verbose:
                print(
                    f'UmiAI: Found {len(candidates)} candidates for "{parsed_tag}" with tags: {groups}, first 10: {candidates[:10]}'
                )
            random.shuffle(candidates)
            return self.select_value_from_candidates(candidates)
        if self.verbose: print(f'UmiAI: No tag candidates found for: "{parsed_tag}" with tags: {groups}')
        return ""

    def select(self, tag, groups=None):
        self.previously_selected_tags.setdefault(tag, 0)
        if (tag.count(':')==2) or (len(tag) < 2 and groups):
            return False
        if self.previously_selected_tags.get(tag) < 50000:
            self.previously_selected_tags[tag] += 1
            parsed_tag = parse_tag(tag)
            tags = self.tag_loader.load_tags(parsed_tag, self.verbose, self.cache_files)
            if groups and len(groups) > 0:
                return self.get_tag_group_choice(parsed_tag, groups, tags)
            if len(tags) > 0:
                return self.get_tag_choice(parsed_tag, tags)
            else:
                print(
                    f'UmiAI: No tags found in wildcard file "{parsed_tag}" or file does not exist'
                )
            return False
        if self.previously_selected_tags.get(tag) == 50000:
            self.previously_selected_tags[tag] += 1
            print(f'Processed more than 50000 hits on "{tag}". This probaly is a reference loop. Inspect your tags and remove any loops.')
        return False


class TagReplacer:

    def __init__(self, tag_selector, options):
        self.tag_selector = tag_selector
        self.options = options
        self.wildcard_regex = re.compile('((__|<)(.*?)(__|>))')
        self.opts_regexp = re.compile('(?<=\[)(.*?)(?=\])')
        self.debug = dict(options).get('debug', False)

    def replace_wildcard(self, matches):
        if matches is None or len(matches.groups()) == 0:
            return ""
        match = matches.groups()[2]
        match_and_opts = match.split(':')
        if self.debug: print(f'match_and_ops: {match_and_opts}')
        # note:
        # file names should NOT contain double underscore '__'
        # or more than one set of brackets '<>' as this will
        # BREAK the regex matching
        # if you're reading this, just bite the bullet and
        # learn unprompted
        if (len(match_and_opts) == 2):
            selected_tags = self.tag_selector.select(
                match_and_opts[0], self.opts_regexp.findall(match_and_opts[1]))
        else:
            global_opts = self.opts_regexp.findall(match)
            if len(global_opts) > 0:
                selected_tags = self.tag_selector.select(ALL_KEY, global_opts)
            else:
                selected_tags = self.tag_selector.select(match)

        if selected_tags:
            return selected_tags
        return matches[0]

    # why are we doing recurison here when there's another recursion step below?
    # by processing || logic in steps, branch early and process less
    def replace_wildcard_recursive(self, prompt):
        p = self.wildcard_regex.sub(self.replace_wildcard, prompt)
        return p

    def replace(self, prompt):
        return self.replace_wildcard_recursive(prompt)


# handle {1$$this | that} notation
class DynamicPromptReplacer:

    def __init__(self, options):
        self.re_combinations = re.compile(r"\{([^{}]*)\}")
        self.debug = dict(options).get('debug', False)

    def get_variant_weight(self, variant):
        split_variant = variant.split("%")
        if len(split_variant) == 2:
            num = split_variant[0]
            try:
                return int(num)
            except ValueError:
                print(f'{num} is not a number')
        return 0

    def get_variant(self, variant):
        split_variant = variant.split("%")
        if len(split_variant) == 2:
            return split_variant[1]
        return variant

    def parse_range(self, range_str, num_variants):
        if range_str is None:
            return None

        parts = range_str.split("-")
        if len(parts) == 1:
            low = high = min(int(parts[0]), num_variants)
        elif len(parts) == 2:
            low = int(parts[0]) if parts[0] else 0
            high = min(int(parts[1]),
                       num_variants) if parts[1] else num_variants
        else:
            raise Exception(f"Unexpected range {range_str}")

        return min(low, high), max(low, high)

    def replace_combinations(self, match):
        if match is None or len(match.groups()) == 0:
            return ""

        combinations_str = match.groups()[0]
        if self.debug: print(combinations_str)
        variants = [s.strip() for s in combinations_str.split("||")] # problem line, doesn't keep [a|b] intact
        if self.debug: print(variants)                               # bodge solution is to change delimiter

        weights = [self.get_variant_weight(var) for var in variants]
        variants = [self.get_variant(var) for var in variants]

        splits = variants[0].split("$$")
        quantity = splits.pop(0) if len(splits) > 1 else str(1)
        variants[0] = splits[0]

        low_range, high_range = self.parse_range(quantity, len(variants))

        quantity = random.randint(low_range, high_range)

        summed = sum(weights)
        zero_weights = weights.count(0)
        weights = list(
            map(lambda x: (100 - summed) / zero_weights
                if x == 0 else x, weights))

        try:
            if self.debug: print(f"choosing {quantity} tag from:\n{' , '.join(variants)}")
            picked = []
            for x in range(quantity):
                choice = random.choices(variants, weights)[0]
                picked.append(choice)

                index = variants.index(choice)
                variants.pop(index)
                weights.pop(index)

            return ", ".join(picked)
        except ValueError as e:
            return ""

    def replace(self, template):
        if template is None:
            return None

        return self.re_combinations.sub(self.replace_combinations, template)

class PromptGenerator:

    def __init__(self, options):
        self.tag_loader = TagLoader(options)
        self.tag_selector = TagSelector(self.tag_loader, options)
        self.negative_tag_generator = NegativePromptGenerator()
        self.replacers = [
            DynamicPromptReplacer(options),
            TagReplacer(self.tag_selector, options)
        ]
        self.verbose = dict(options).get('verbose', False)
        self.debug = dict(options).get('debug', False)

    def use_replacers(self, prompt):
        for replacer in self.replacers:
            prompt = replacer.replace(prompt)

        return prompt

    def prompt_memory_replace(self, prompt, memory_dict={}):
        p = prompt
        memory_regex = re.compile('((__|\$\#)(.*?)(__|\#\$))')
        # match regex for $#foo;bar#$ here
        results = memory_regex.findall(p)
        for result in results:
            match = result[2]
            match_and_key = match.split(';')
            # this is a value key combination
            if len(match_and_key) == 2:
                memory_dict.update( {match_and_key[1]: match_and_key[0]} )
                p = p.replace(result[0], match_and_key[0])
            # this is just a key
            else:
                try:
                    sub = memory_dict[match_and_key[0]]
                    p = p.replace(result[0], sub)
                except KeyError as e:
                    print(f'\nWARNING: key {match_and_key[0]} referenced before assignment.\nkey {match_and_key[0]} will NOT be replaced!\n')
        return p, memory_dict

    def generate_single_prompt(self, original_prompt):
        previous_prompt = original_prompt
        if self.debug:
            print('#####################')
            print('#####################')
            print('Before Recursion Step')
            print('#####################')
            print('#####################')
        start = time.time()
        prompt = self.use_replacers(original_prompt)
        while previous_prompt != prompt:
            if self.debug:
                print('#####################')
                print('During Recursion Step')
                print('#####################')
                print(f"\nDEBUG: Prompt is currently")
                print(f"{prompt}\n")
            previous_prompt = prompt
            prompt = self.use_replacers(prompt)
        prompt = self.negative_tag_generator.replace(prompt)
        end = time.time()
        if self.verbose:
            print(f"Prompt generated in {end - start} seconds")

        return prompt

    def get_negative_tags(self):
        return self.negative_tag_generator.get_negative_tags()


class NegativePromptGenerator:

    def __init__(self):
        self.negative_tag = set()

    def strip_negative_tags(self, tags):
        matches = re.findall('\*\*.*?\*\*', tags)
        if matches:
            for match in matches:
                self.negative_tag.add(match.replace("**", ""))
                tags = tags.replace(match, "")
        return tags

    def replace(self, prompt):
        return self.strip_negative_tags(prompt)

    def get_negative_tags(self):
        return ", ".join(self.negative_tag)

class Shortcode():
	def __init__(self, Unprompted):
		self.Unprompted = Unprompted
		self.description = """
							Processes a Prompt stored in first parg
							and a Negative Prompt stored in second parg
							according to Umi-AI rules
							"""

	def run_atomic(self, pargs, kwargs, context):
		_verbose = self.Unprompted.parse_arg("_verbose", True)
		_debug = self.Unprompted.parse_arg("_debug", False)
		_ignore_paths = self.Unprompted.parse_arg("_ignore_paths", False)
		_cache_files = self.Unprompted.parse_arg("_cache_files", True)

		if (pargs[0] not in self.Unprompted.shortcode_user_vars):
			return ""
		original_prompt = self.Unprompted.shortcode_user_vars[pargs[0]]
		original_negative_prompt = ""
		if (pargs[1] in self.Unprompted.shortcode_user_vars):
			original_negative_prompt = self.Unprompted.shortcode_user_vars[pargs[1]]

		TagLoader.files.clear()
		options = {
			'verbose': _verbose,
			'debug': _debug,
			'cache_files': _cache_files,
			'ignore_paths': _ignore_paths,
			'wildcard_path': os.path.join(self.Unprompted.base_dir, 'templates/wildcards') # bodge
		}
		if _debug: print(f'\nOriginal Prompt: "{original_prompt}"\nOriginal Negatives: "{original_negative_prompt}"\n')
		prompt_generator = PromptGenerator(options)

		prompt_generator.negative_tag_generator.negative_tag = set()
		memory_dict = {}
		prompt = prompt_generator.generate_single_prompt(original_prompt)
		prompt, memory_dict = prompt_generator.prompt_memory_replace(prompt, memory_dict)

		if _debug: print(f'Prompt: "{prompt}"\n')
		if _debug:
			print('Dumping Memory dict:\n')
			for key in memory_dict.keys():
				print(f'key: {key}\tvalue: {memory_dict[key]}')
			print('\n')
		negative = original_negative_prompt
		negative += ' ' # bodge, not necessary if we make other changes above
		negative += prompt_generator.get_negative_tags()
		negative = prompt_generator.prompt_memory_replace(negative, memory_dict)[0]
		if _debug: print(f'Negative: "{negative}\n"')

		final_string = f"{prompt}|{negative}"
		return final_string