# Data audit: coimbatore

```json
{
  "city": "coimbatore",
  "file": "data/h3_panel/final/coimbatore.parquet",
  "shape": [
    35820,
    30
  ],
  "columns": [
    "city_id",
    "h3_index",
    "date",
    "temp_mean_c",
    "dewpoint_mean_c",
    "precip_sum_mm",
    "wind_speed",
    "radiation",
    "soil_moisture",
    "ndvi",
    "lst_c",
    "pm25",
    "built_up_fraction",
    "road_density_km_km2",
    "building_density",
    "building_fp_fraction",
    "green_space_fraction",
    "latitude",
    "longitude",
    "heat_stress_idx",
    "water_stress_idx",
    "pollution_idx",
    "vegetation_idx",
    "urban_vulnerability_idx",
    "ssi_linear",
    "omega_compound",
    "ssi_value",
    "ssi_band",
    "archetype_id",
    "anomaly_flag"
  ],
  "date_min": "2020-01-01",
  "date_max": "2022-12-01",
  "n_months": 36,
  "n_hexes": 995,
  "balanced_panel": true,
  "missing_cols": {
    "ndvi": 1065,
    "lst_c": 190
  },
  "missing_by_date_top3": {
    "ndvi": {
      "2021-03-01": 995,
      "2020-12-01": 35,
      "2022-11-01": 35
    },
    "lst_c": {
      "2020-07-01": 83,
      "2021-11-01": 73,
      "2021-09-01": 22
    }
  },
  "constant_cols": [],
  "static_per_hex_cols": [
    "built_up_fraction",
    "road_density_km_km2",
    "building_density",
    "building_fp_fraction",
    "green_space_fraction",
    "latitude",
    "longitude",
    "urban_vulnerability_idx"
  ],
  "distinct_per_date_avg": {
    "temp_mean_c": 995.0,
    "dewpoint_mean_c": 995.0,
    "precip_sum_mm": 995.0,
    "wind_speed": 995.0,
    "radiation": 995.0,
    "soil_moisture": 995.0,
    "ndvi": 965.4,
    "lst_c": 842.8,
    "pm25": 3.0,
    "built_up_fraction": 920.0,
    "road_density_km_km2": 920.0,
    "building_density": 453.0,
    "building_fp_fraction": 459.0,
    "green_space_fraction": 60.0,
    "latitude": 995.0,
    "longitude": 995.0,
    "heat_stress_idx": 995.0,
    "water_stress_idx": 995.0,
    "pollution_idx": 3.0,
    "vegetation_idx": 965.0,
    "urban_vulnerability_idx": 902.0,
    "ssi_linear": 995.0,
    "omega_compound": 214.2,
    "ssi_value": 978.4,
    "archetype_id": 4.0
  },
  "city_scale_cols(<=5 distinct per date)": [
    "pm25",
    "pollution_idx",
    "archetype_id"
  ],
  "index_cols": [
    "heat_stress_idx",
    "water_stress_idx",
    "pollution_idx",
    "vegetation_idx",
    "urban_vulnerability_idx"
  ],
  "index_summary": {
    "heat_stress_idx": {
      "min": 0.30755,
      "max": 0.69245,
      "mean": 0.5,
      "std": 0.13608
    },
    "water_stress_idx": {
      "min": 0.30755,
      "max": 0.69245,
      "mean": 0.5,
      "std": 0.13608
    },
    "pollution_idx": {
      "min": 0.0,
      "max": 1.0,
      "mean": 0.42487,
      "std": 0.24562
    },
    "vegetation_idx": {
      "min": 0.30755,
      "max": 0.69245,
      "mean": 0.49461,
      "std": 0.13231
    },
    "urban_vulnerability_idx": {
      "min": 0.35195,
      "max": 1.0,
      "mean": 0.49816,
      "std": 0.16025
    }
  },
  "monthly_mean_spread": {
    "heat_stress_idx": 0.0,
    "water_stress_idx": 0.0,
    "pollution_idx": 0.62033,
    "vegetation_idx": 0.06044,
    "urban_vulnerability_idx": 0.0
  },
  "flag_per_month_normalised(spread<0.01)": [
    "heat_stress_idx",
    "water_stress_idx"
  ],
  "flag_identical_range_indices": [
    [
      "heat_stress_idx",
      "water_stress_idx"
    ]
  ],
  "implied_linear_weights": {
    "heat_stress_idx": 0.384,
    "water_stress_idx": 0.2904,
    "pollution_idx": 0.1063,
    "vegetation_idx": 0.1978,
    "urban_vulnerability_idx": 0.0215
  },
  "implied_weights_intercept": -0.0,
  "implied_weights_R2": 1.0,
  "omega_positive_share": 0.2177,
  "omega_max": 2.8496,
  "implied_gamma_median": 0.3,
  "implied_gamma_std": 0.0,
  "share_clipped_at_1": 0.017,
  "additive_formula_exact": true,
  "ssi_var_share": {
    "between_month": 0.6584,
    "between_hex": 0.0238,
    "hex_x_month_residual": 0.3178
  },
  "spearman_pooled_idx_vs_raw": {
    "heat_stress_idx": {
      "temp_mean_c": 0.142,
      "dewpoint_mean_c": -0.021,
      "precip_sum_mm": -0.16,
      "wind_speed": 0.042,
      "radiation": 0.07,
      "soil_moisture": -0.165,
      "ndvi": 0.095,
      "lst_c": 0.243,
      "pm25": -0.201,
      "built_up_fraction": 0.001,
      "building_density": -0.0,
      "green_space_fraction": -0.0
    },
    "water_stress_idx": {
      "temp_mean_c": 0.181,
      "dewpoint_mean_c": 0.069,
      "precip_sum_mm": -0.077,
      "wind_speed": 0.028,
      "radiation": -0.023,
      "soil_moisture": -0.16,
      "ndvi": -0.004,
      "lst_c": 0.137,
      "pm25": -0.102,
      "built_up_fraction": -0.0,
      "building_density": -0.0,
      "green_space_fraction": -0.001
    },
    "pollution_idx": {
      "temp_mean_c": -0.224,
      "dewpoint_mean_c": -0.617,
      "precip_sum_mm": -0.406,
      "wind_speed": -0.739,
      "radiation": 0.242,
      "soil_moisture": -0.257,
      "ndvi": 0.082,
      "lst_c": -0.445,
      "pm25": 1.0,
      "built_up_fraction": -0.084,
      "building_density": -0.06,
      "green_space_fraction": -0.021
    },
    "vegetation_idx": {
      "temp_mean_c": -0.048,
      "dewpoint_mean_c": -0.015,
      "precip_sum_mm": 0.01,
      "wind_speed": 0.068,
      "radiation": -0.064,
      "soil_moisture": -0.009,
      "ndvi": -0.576,
      "lst_c": -0.085,
      "pm25": 0.085,
      "built_up_fraction": 0.005,
      "building_density": 0.005,
      "green_space_fraction": 0.002
    },
    "urban_vulnerability_idx": {
      "temp_mean_c": 0.045,
      "dewpoint_mean_c": -0.002,
      "precip_sum_mm": -0.02,
      "wind_speed": 0.028,
      "radiation": 0.01,
      "soil_moisture": -0.071,
      "ndvi": -0.328,
      "lst_c": 0.264,
      "pm25": -0.073,
      "built_up_fraction": 0.91,
      "building_density": 0.761,
      "green_space_fraction": 0.223
    }
  },
  "heat_vs_lst_within_month": {
    "mean": 0.244,
    "min": -0.109,
    "max": 0.614,
    "n_months": 36
  },
  "anomaly_overall_share": 0.1,
  "anomaly_top_months": {
    "2020-05-01": 0.706,
    "2022-12-01": 0.659,
    "2022-02-01": 0.596,
    "2020-03-01": 0.361,
    "2020-07-01": 0.332
  },
  "n_archetypes": 6,
  "archetypes_per_hex_avg": 4.73
}
```
