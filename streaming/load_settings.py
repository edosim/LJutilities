import yaml

# YAML file path
yaml_file = 'streaming\settings.yaml'

# Reading YAML data from file
with open(yaml_file, 'r') as f:
    settings = yaml.safe_load(f)

#Assign variables
DEFAULT_POSITIONS = settings['DEFAULT_POSITIONS']
DEFAULT_DATE = settings['DEFAULT_DATE']
DEFAULT_XLIMS = settings['DEFAULT_XLIMS']
DEFAULT_CAL_PARAMS = settings['DEFAULT_CAL_PARAMS']
DEFAULT_FOLDER = settings['DEFAULT_FOLDER']
DEFAULT_WAVELENGTH = settings['DEFAULT_WAVELENGTH']

