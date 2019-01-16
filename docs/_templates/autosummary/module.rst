{{ fullname }}
{{ underline }}


{% if classes %}
Classes
-------
.. autosummary::
   {% for class in classes %}
	{{ fullname }}.{{ class }}
   {% endfor %}
{% endif %}

{% if functions %}
Functions
---------
.. autosummary::
   {% for function in functions %}
	{{ fullname }}.{{ function }}
   {% endfor %}
{% endif %}

{% if exceptions %}
Exceptions
----------
.. autosummary::
   {% for exception in exceptions %}
	{{ fullname }}.{{ exception }}
   {% endfor %}
{% endif %}
.. autosummary::


.. automodule:: {{ fullname }}
   :members:
