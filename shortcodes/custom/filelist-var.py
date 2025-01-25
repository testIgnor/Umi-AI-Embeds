import glob
import random
import os


class Shortcode():
	def __init__(self, Unprompted):
		self.Unprompted = Unprompted
		self.description = "Returns a list of files at a given location using glob."

	def run_atomic(self, pargs, kwargs, context):
		import lib_unprompted.helpers as helpers
		file_strings = helpers.ensure(self.Unprompted.parse_alt_tags(pargs[0], context).split(self.Unprompted.Config.syntax.delimiter), list)
		_delimiter = self.Unprompted.parse_advanced(kwargs["_delimiter"], context) if "_delimiter" in kwargs else self.Unprompted.Config.syntax.delimiter
		_basename = self.Unprompted.shortcode_var_is_true("_basename", pargs, kwargs)
		_hide_ext = self.Unprompted.shortcode_var_is_true("_hide_ext", pargs, kwargs)
		_recursive = self.Unprompted.parse_arg("_recursive", False)

		f_strings = []
		for fs in file_strings:
			if (fs in self.Unprompted.shortcode_user_vars):
				f_strings.append(self.Unprompted.shortcode_user_vars[fs])
		file_strings = f_strings
		all_files = ""
		for file_string in file_strings:
			# Relative path
			if (file_string[0] == "."):
				file_string = os.path.dirname(context) + "/" + file_string
			else:
				file_string = file_string.replace("%BASE_DIR%", self.Unprompted.base_dir)

			# Calculate base_dir as the parent directory of the glob pattern up to the first wildcard
			if "*" in file_string:
				base_dir = file_string[:file_string.find("*")]
			else:
				base_dir = os.path.dirname(file_string)

			files = glob.glob(file_string, recursive=_recursive)
			if (len(files) == 0):
				self.log.warning(f"No files found at this location: {file_string}")
				continue

			if _hide_ext:
				for idx, file in enumerate(files):
					files[idx] = os.path.splitext(file)[0]

			if _basename:
				for idx, file in enumerate(files):
					# Calculate the relative path from the base directory to the file
					relative_path = os.path.relpath(file, base_dir).replace("\\", "/")
					files[idx] = relative_path

			if all_files:
				all_files += _delimiter
			all_files += _delimiter.join(helpers.ensure(files, list))

		return all_files

	def ui(self, gr):
		return [
		    gr.Textbox(label="Filepath 🡢 arg_str", max_lines=1),
		    gr.Textbox(label="Result delimiter 🡢 _delimiter", max_lines=1, value=self.Unprompted.Config.syntax.delimiter),
		]
