from typing import Any

from pydantic import BaseModel, Field


class ParameterMapping(BaseModel):
    """
    Defines how a standard internal query parameter maps to a portal's URL parameter.
    """

    name: str = Field(..., description="The query parameter key name on the portal (e.g. 'type', 'rent', 'bedroom')")
    value_mapping: dict[str, str] | None = Field(
        default=None,
        description="Optional mapping from standard internal values to portal-specific values (e.g. '1' -> 'BHK1')",
    )
    delimiter: str | None = Field(
        default=None,
        description="Delimiter to join multiple values if a list is provided (e.g. ',' for type=BHK1,BHK2)",
    )
    prefix: str | None = Field(default=None, description="Optional prefix to prepend to the final parameter value")
    suffix: str | None = Field(default=None, description="Optional suffix to append to the final parameter value")
    default_value: str | None = Field(
        default=None, description="Default value to use if this filter is not explicitly provided in the request"
    )


class PortalConfig(BaseModel):
    """
    Validation schema for portal configuration.
    Determines URL routing, path construction, and parameter mapping for a specific real estate portal.
    """

    portal_id: str = Field(..., description="Unique string identifier for the portal (e.g. 'nobroker', '99acres')")
    portal_name: str = Field(..., description="Human-readable name of the portal (e.g. 'NoBroker', '99acres')")
    base_url: str = Field(..., description="Base domain URL of the portal (e.g. 'https://www.nobroker.in')")

    rent_url_template: str = Field(
        ...,
        description="Rental URL template. E.g. '{base_url}/property/rent/{city_slug}/{city_capitalized}'",
    )
    buy_url_template: str = Field(
        ...,
        description="Buy URL template. E.g. '{base_url}/property/sale/{city_slug}/{city_capitalized}'",
    )

    rent_params: dict[str, ParameterMapping] = Field(..., description="Mappings for rental search query parameters")
    buy_params: dict[str, ParameterMapping] = Field(..., description="Mappings for buy/sale search query parameters")

    city_slug_map: dict[str, str] = Field(
        ..., description="Mapping from standard lowercase city name (e.g. 'bangalore') to portal-specific slug"
    )

    example_urls: dict[str, str] = Field(
        ..., description="Map of scenario names to expected URLs, used for testing and documentation"
    )

    def generate_url(self, flow: str, city: str, filters: dict[str, Any]) -> str:
        """
        Generates a search URL for the portal based on the flow (rent/buy), city, and filters.

        Args:
            flow: The transaction flow type, must be either 'rent' or 'buy'.
            city: The target city name (e.g., 'bangalore', 'mumbai').
            filters: A dictionary of filter key-value pairs (e.g. {'bhk': ['2', '3'], 'price_min': 15000}).

        Returns:
            The complete constructed URL with query parameters.

        Raises:
            ValueError: If the flow or city is invalid/unsupported.
        """
        flow_lower = flow.lower()
        if flow_lower == "rent":
            url_template = self.rent_url_template
            params_mapping = self.rent_params
        elif flow_lower == "buy":
            url_template = self.buy_url_template
            params_mapping = self.buy_params
        else:
            raise ValueError(f"Invalid flow type: '{flow}'. Must be 'rent' or 'buy'")

        city_lower = city.lower()
        city_slug = self.city_slug_map.get(city_lower)
        if not city_slug:
            raise ValueError(f"City '{city}' is not supported by portal '{self.portal_name}'")

        # Standard capitalization for templates that use it
        city_capitalized = city_lower.capitalize()

        # Interpolate the base URL and city details into the path template
        formatted_url = url_template.format(
            base_url=self.base_url.rstrip("/"), city_slug=city_slug, city_capitalized=city_capitalized
        )

        # Build the list of query parameters
        query_params = []
        for filter_key, param_map in params_mapping.items():
            filter_val = filters.get(filter_key)
            if filter_val is None:
                if param_map.default_value is not None:
                    filter_val = param_map.default_value
                else:
                    continue

            # Format value depending on whether it's a list or scalar
            val_str = ""
            if isinstance(filter_val, list):
                mapped_vals = []
                for val in filter_val:
                    val_str_item = str(val)
                    if param_map.value_mapping and val_str_item in param_map.value_mapping:
                        mapped_vals.append(param_map.value_mapping[val_str_item])
                    else:
                        mapped_vals.append(val_str_item)

                # Join with specified delimiter (defaulting to comma)
                delim = param_map.delimiter or ","
                val_str = delim.join(mapped_vals)
            else:
                val_str_item = str(filter_val)
                if param_map.value_mapping and val_str_item in param_map.value_mapping:
                    val_str = param_map.value_mapping[val_str_item]
                else:
                    val_str = val_str_item

            if val_str:
                # Apply prefix/suffix if configured
                if param_map.prefix:
                    val_str = f"{param_map.prefix}{val_str}"
                if param_map.suffix:
                    val_str = f"{val_str}{param_map.suffix}"

                query_params.append(f"{param_map.name}={val_str}")

        # Append query params to the URL path
        if query_params:
            separator = "&" if "?" in formatted_url else "?"
            formatted_url = f"{formatted_url}{separator}{'&'.join(query_params)}"

        return formatted_url
