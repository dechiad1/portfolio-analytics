{% macro s3_path(layer, table_name) -%}
{%- set bucket = env_var('S3_BUCKET', 'portfolio-analytics') -%}
{%- set prefix = env_var('S3_PREFIX', 'data') -%}
s3://{{ bucket }}/{{ prefix }}/{{ layer }}/{{ table_name }}.parquet
{%- endmacro %}


{% macro mart_config(table_name) %}
  {#- Config for mart tables - always writes to S3 as Parquet -#}
  {{ return({
    'materialized': 'external',
    'location': s3_path('marts', table_name),
    'format': 'parquet'
  }) }}
{% endmacro %}


{% macro intermediate_config(table_name) %}
  {#- Config for intermediate tables - always writes to S3 as Parquet -#}
  {{ return({
    'materialized': 'external',
    'location': s3_path('intermediate', table_name),
    'format': 'parquet'
  }) }}
{% endmacro %}
