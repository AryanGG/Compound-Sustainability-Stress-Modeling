import pandas as pd
df = pd.read_csv("reports/frontend_data_mumbai.csv")
print("Data shape:", df.shape)
for col in ['ssi_value', 'heat_stress_idx', 'water_stress_idx', 'vegetation_idx', 'pollution_idx']:
    if col in df.columns:
        print(f"{col}: mean={df[col].mean():.3f}, max={df[col].max():.3f}, zeros={(df[col]==0).sum()}")
    else:
        print(f"{col} not found")
