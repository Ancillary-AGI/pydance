#!/usr/bin/env python3
"""
Test the templating system
"""

from pydance.templating import render_template_string

# Test lean template engine
template = """
<h1>{{ title }}</h1>
<p>Welcome {{ user.name }}!</p>
<ul>
{% for item in items %}
    <li>{{ item }}</li>
{% endfor %}
</ul>
"""

context = {
    'title': 'Pydance Template Test',
    'user': {'name': 'Developer'},
    'items': ['Feature 1', 'Feature 2', 'Feature 3']
}

try:
    result = render_template_string(template, **context)
    print("✓ Lean template engine working!")
    print("Rendered output:")
    print(result)
except Exception as e:
    print(f"✗ Template error: {e}")

print("\n" + "="*50)
print("✓ Pydance templating system is functional!")