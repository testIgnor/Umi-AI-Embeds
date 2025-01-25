import glob
import random
import os


class Shortcode():

	def __init__(self, Unprompted):
		self.Unprompted = Unprompted
		self.description = "Processes filepath from the first parg."

	def run_atomic(self, pargs, kwargs, context):
		import lib_unprompted.helpers as helpers

		# dereference here
		if (pargs[0] not in self.Unprompted.shortcode_user_vars):
			return ""
		name = self.Unprompted.shortcode_user_vars[pargs[0]]
		this_encoding = self.Unprompted.parse_advanced(kwargs["_encoding"], context) if "_encoding" in kwargs else "utf-8"

		file = self.Unprompted.parse_filepath(helpers.str_with_ext(name, self.Unprompted.Config.formats.txt), context=context, must_exist=False)

		if not os.path.exists(file):
			if "_suppress_errors" not in pargs:
				self.log.error(f"File does not exist: {file}")
			contents = ""
		else:
			next_context = file
			with open(file, "r", encoding=this_encoding) as f:
				contents = f.read()
			f.close()

		# Use [set] with keyword arguments
		for key, value in kwargs.items():
			if (self.Unprompted.is_system_arg(key)):
				continue
			self.Unprompted.shortcode_objects["set"].run_block([key], {}, context, self.Unprompted.parse_alt_tags(value))

		contents = self.Unprompted.process_string(contents, next_context)
		break_type = self.Unprompted.handle_breaks()

		# self.Unprompted.conditional_depth = max(0, self.Unprompted.conditional_depth -1)
		return contents
