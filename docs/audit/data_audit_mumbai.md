# Data audit: mumbai

```json
{
  "city": "mumbai",
  "file": "data/h3_panel/final/mumbai.parquet",
  "shape": [
    25452,
    34
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
    "bpl_pct",
    "slum_pct",
    "elderly_pct",
    "literacy_pct",
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
  "n_hexes": 707,
  "balanced_panel": true,
  "missing_cols": {
    "ndvi": 707,
    "lst_c": 866,
    "pm25": 707
  },
  "missing_by_date_top3": {
    "ndvi": {
      "2022-11-01": 707
    },
    "lst_c": {
      "2022-07-01": 47,
      "2020-07-01": 29,
      "2022-08-01": 26
    },
    "pm25": {
      "2021-12-01": 707
    }
  },
  "constant_cols": [
    "bpl_pct",
    "slum_pct",
    "elderly_pct",
    "literacy_pct"
  ],
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
    "temp_mean_c": 707.0,
    "dewpoint_mean_c": 707.0,
    "precip_sum_mm": 671.3,
    "wind_speed": 707.0,
    "radiation": 707.0,
    "soil_moisture": 707.0,
    "ndvi": 687.3,
    "lst_c": 589.2,
    "pm25": 2.9,
    "built_up_fraction": 588.0,
    "road_density_km_km2": 557.0,
    "building_density": 556.0,
    "building_fp_fraction": 560.0,
    "green_space_fraction": 483.0,
    "bpl_pct": 1.0,
    "slum_pct": 1.0,
    "elderly_pct": 1.0,
    "literacy_pct": 1.0,
    "latitude": 707.0,
    "longitude": 707.0,
    "heat_stress_idx": 707.0,
    "water_stress_idx": 703.3,
    "pollution_idx": 2.9,
    "vegetation_idx": 646.8,
    "urban_vulnerability_idx": 614.0,
    "ssi_linear": 707.0,
    "omega_compound": 125.3,
    "ssi_value": 629.0,
    "archetype_id": 2.8
  },
  "city_scale_cols(<=5 distinct per date)": [
    "pm25",
    "bpl_pct",
    "slum_pct",
    "elderly_pct",
    "literacy_pct",
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
      "min": 0.21102,
      "max": 0.7727,
      "mean": 0.47201,
      "std": 0.1155
    },
    "water_stress_idx": {
      "min": 0.0,
      "max": 1.0,
      "mean": 0.6994,
      "std": 0.27242
    },
    "pollution_idx": {
      "min": 0.59667,
      "max": 0.98759,
      "mean": 0.82465,
      "std": 0.12313
    },
    "vegetation_idx": {
      "min": 0.0,
      "max": 1.0,
      "mean": 0.64188,
      "std": 0.22862
    },
    "urban_vulnerability_idx": {
      "min": 0.0,
      "max": 0.94256,
      "mean": 0.46106,
      "std": 0.23618
    }
  },
  "monthly_mean_spread": {
    "heat_stress_idx": 0.39389,
    "water_stress_idx": 0.6415,
    "pollution_idx": 0.30412,
    "vegetation_idx": 0.12322,
    "urban_vulnerability_idx": 0.0
  },
  "flag_per_month_normalised(spread<0.01)": [],
  "flag_identical_range_indices": [],
  "implied_linear_weights": {
    "heat_stress_idx": 0.1714,
    "water_stress_idx": 0.1452,
    "pollution_idx": 0.2784,
    "vegetation_idx": 0.126,
    "urban_vulnerability_idx": 0.2791
  },
  "implied_weights_intercept": 0.0,
  "implied_weights_R2": 1.0,
  "omega_positive_share": 0.1759,
  "omega_max": 3.3934,
  "implied_gamma_median": 0.3,
  "implied_gamma_std": 0.0,
  "share_clipped_at_1": 0.1113,
  "additive_formula_exact": true,
  "ssi_var_share": {
    "between_month": 0.3885,
    "between_hex": 0.4934,
    "hex_x_month_residual": 0.1181
  },
  "spearman_pooled_idx_vs_raw": {
    "heat_stress_idx": {
      "temp_mean_c": 0.952,
      "dewpoint_mean_c": 0.745,
      "precip_sum_mm": 0.235,
      "wind_speed": 0.023,
      "radiation": 0.182,
      "soil_moisture": 0.102,
      "ndvi": -0.067,
      "lst_c": 0.493,
      "pm25": -0.467,
      "built_up_fraction": 0.087,
      "building_density": 0.073,
      "green_space_fraction": -0.015
    },
    "water_stress_idx": {
      "temp_mean_c": -0.093,
      "dewpoint_mean_c": -0.586,
      "precip_sum_mm": -0.794,
      "wind_speed": -0.188,
      "radiation": 0.782,
      "soil_moisture": -0.95,
      "ndvi": -0.292,
      "lst_c": 0.496,
      "pm25": 0.559,
      "built_up_fraction": 0.244,
      "building_density": 0.196,
      "green_space_fraction": -0.105
    },
    "pollution_idx": {
      "temp_mean_c": -0.333,
      "dewpoint_mean_c": -0.798,
      "precip_sum_mm": -0.821,
      "wind_speed": -0.566,
      "radiation": 0.524,
      "soil_moisture": -0.392,
      "ndvi": 0.043,
      "lst_c": 0.173,
      "pm25": 1.0,
      "built_up_fraction": -0.09,
      "building_density": -0.06,
      "green_space_fraction": 0.032
    },
    "vegetation_idx": {
      "temp_mean_c": 0.002,
      "dewpoint_mean_c": -0.082,
      "precip_sum_mm": -0.107,
      "wind_speed": 0.11,
      "radiation": 0.133,
      "soil_moisture": -0.363,
      "ndvi": -1.0,
      "lst_c": 0.314,
      "pm25": -0.043,
      "built_up_fraction": 0.476,
      "building_density": 0.345,
      "green_space_fraction": -0.258
    },
    "urban_vulnerability_idx": {
      "temp_mean_c": -0.054,
      "dewpoint_mean_c": -0.029,
      "precip_sum_mm": 0.013,
      "wind_speed": 0.139,
      "radiation": 0.012,
      "soil_moisture": -0.341,
      "ndvi": -0.512,
      "lst_c": 0.42,
      "pm25": -0.096,
      "built_up_fraction": 0.973,
      "building_density": 0.749,
      "green_space_fraction": -0.375
    }
  },
  "heat_vs_lst_within_month": {
    "mean": 0.835,
    "min": 0.535,
    "max": 0.998,
    "n_months": 36
  },
  "anomaly_overall_share": 0.0,
  "anomaly_top_months": {
    "2020-01-01": 0.0,
    "2020-02-01": 0.0,
    "2021-09-01": 0.0,
    "2021-10-01": 0.0,
    "2021-11-01": 0.0
  },
  "n_archetypes": 6,
  "archetypes_per_hex_avg": 3.9
}
```
