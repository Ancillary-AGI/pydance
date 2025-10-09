# shim package - re-export from pydance.core.cli
from pydance.core import cli as _core

globals().update({k:v for k,v in vars(_core).items() if not k.startswith('__')})

