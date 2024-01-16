import os
import re

_err_dup_scripts = (
    "The script name {script_name} exists more than once (first_instance "
    + "{first_path}, second instance {script_full_path})"
)
_err_dup_scripts_version = (
    "The script version {script_version} exists more than once "
    + "(second instance {script_full_path})"
)


def get_all_scripts_recursively(root_directory, verbose):
    all_files = dict()
    all_versions = list()
    # Walk the entire directory structure recursively
    for directory_path, directory_names, file_names in os.walk(root_directory):
        for file_name in file_names:
            file_full_path = os.path.join(directory_path, file_name)
            script_name_parts = re.search(
                r"^([V])(.+?)__(.+?)\.(?:sql|sql.jinja)$",
                file_name.strip(),
                re.IGNORECASE,
            )
            repeatable_script_name_parts = re.search(
                r"^([R])__(.+?)\.(?:sql|sql.jinja)$", file_name.strip(), re.IGNORECASE
            )
            always_script_name_parts = re.search(
                r"^([A])__(.+?)\.(?:sql|sql.jinja)$", file_name.strip(), re.IGNORECASE
            )

            # Set script type depending on whether it matches the versioned file naming format
            if script_name_parts is not None:
                script_type = "V"
                if verbose:
                    print(f"Found Versioned file {file_full_path}")
            elif repeatable_script_name_parts is not None:
                script_type = "R"
                if verbose:
                    print(f"Found Repeatable file {file_full_path}")
            elif always_script_name_parts is not None:
                script_type = "A"
                if verbose:
                    print(f"Found Always file {file_full_path}")
            else:
                if verbose:
                    print(f"Ignoring non-change file {file_full_path}")
                continue

            # script name is the filename without any jinja extension
            (file_part, extension_part) = os.path.splitext(file_name)
            if extension_part.upper() == ".JINJA":
                script_name = file_part
            else:
                script_name = file_name

            # Add this script to our dictionary (as nested dictionary)
            script = dict()
            script["script_name"] = script_name
            script["script_full_path"] = file_full_path
            script["script_type"] = script_type
            script["script_version"] = (
                "" if script_type in ["R", "A"] else script_name_parts.group(2)
            )
            if script_type == "R":
                script["script_description"] = (
                    repeatable_script_name_parts.group(2).replace("_", " ").capitalize()
                )
            elif script_type == "A":
                script["script_description"] = (
                    always_script_name_parts.group(2).replace("_", " ").capitalize()
                )
            else:
                script["script_description"] = (
                    script_name_parts.group(3).replace("_", " ").capitalize()
                )

            # Throw an error if the script_name already exists
            if script_name in all_files:
                raise ValueError(
                    _err_dup_scripts.format(
                        first_path=all_files[script_name]["script_full_path"], **script
                    )
                )

            all_files[script_name] = script

            # Throw an error if the same version exists more than once
            if script_type == "V":
                if script["script_version"] in all_versions:
                    raise ValueError(_err_dup_scripts_version.format(**script))
                all_versions.append(script["script_version"])

    return all_files
