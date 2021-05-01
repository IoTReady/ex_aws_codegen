defmodule {{modulename}} do

  # version: {{version}}
  {% for key,value in metadata.items() %}
  # {{key}}: {{value}}
  {%- endfor %}

  @service :{{servicename}}

  {% for key,value in types.items() %}
  {% if value.shape == 'basic' %}
  @type {{key}} :: {{value.def}}
  {% elif value.shape == 'list' %}
  @type {{key}} :: [{{value.def}}]
  {% elif value.shape == 'structure' %}
  @type {{key}} :: %{{value.def | tojson | replace('"', '') }}
  {% endif %}
  {% endfor %}


  @query %ExAws.Operation.RestQuery {service: @service}

  {% for key, value in functions.items() %}
  @spec {{key}}({{value.input_type}}) :: {{value.output_type}}
  def {{key}}(%{{value.params | tojson | replace('"', '') }} = params) do
    %{@query | http_method: {{value.http_method}}, path: "{{value.uri}}", params: params}
  end
  {% endfor %}


end
