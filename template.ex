defmodule $modulename do

  # version: $version
  $metadata

  @service $service

  @query %ExAws.Operation.RestQuery {service: @service}

  $types

  $functions

  defp execute(query) do
    {:ok, %{status_code: 200, body: body}} = query |> ExAws.request(service_override: :"execute-api")
    body |> Jason.decode!()
  end

end
