from importlib.resources import files

def _get_resource(module: str, name: str) -> str:
    """Loads a resource from the package.

    call like this:
        resource_text = _get_resource('epiphany_python_tools.Library_Maps.resources.[folder]', '[filename]')

    see second response:
    https://stackoverflow.com/questions/1395593/managing-resources-in-a-python-project

    Args:
        module (str): path to resource (using python module format)
        name (str): name of resource being loaded

    Returns:
        str: text contents of the resource
    """
    return files(module).joinpath(name).read_text(encoding='utf-8')
