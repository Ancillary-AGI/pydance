# shim package - re-export from pydance.core.locale
from pydance.core import locale as _core

globals().update({k:v for k,v in vars(_core).items() if not k.startswith('__')})

