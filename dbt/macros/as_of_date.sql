{# The reporting date every delinquency calculation is measured against. #}
{% macro as_of_date() -%}
    date '{{ var("as_of_date") }}'
{%- endmacro %}

{# Standard consumer-lending delinquency buckets from days past due. #}
{% macro delinquency_bucket(dpd_column) -%}
    case
        when {{ dpd_column }} = 0  then 'current'
        when {{ dpd_column }} < 30 then '1-29 dpd'
        when {{ dpd_column }} < 60 then '30-59 dpd'
        when {{ dpd_column }} < 90 then '60-89 dpd'
        else '90+ dpd'
    end
{%- endmacro %}
