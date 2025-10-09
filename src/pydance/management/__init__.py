# shim package - re-export from pydance.core.management
from pydance.core import management as _core

globals().update({k:v for k,v in vars(_core).items() if not k.startswith('__')})

