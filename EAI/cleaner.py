import os
import sys

def clean_directory(directory):
	"""
	Cleans the specified directory by removing all .aux .log .out and .toc files.

	Args:
		directory (str): The path to the directory to be cleaned.
	"""
	if not os.path.exists(directory):
		print(f"The directory {directory} does not exist.")
		return

	for filename in os.listdir(directory):
		file_path = os.path.join(directory, filename)
		try:
			if (os.path.isfile(file_path) or os.path.islink(file_path)) and filename.endswith(('.aux', '.log', '.out', '.toc')):  # noqa: SIM102
				os.unlink(file_path)  # Remove the file or link
		except Exception as e:
			print(f"Failed to delete {file_path}. Reason: {e}")

if __name__ == "__main__":
	if len(sys.argv) != 2:
		print("Usage: python cleaner.py <directory_path>")
		sys.exit(1)

	directory_path = sys.argv[1]
	clean_directory(directory_path)