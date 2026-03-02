import json
import numpy as np
import pandas as pd

data_path = "data/T200_Data.xlsx"

force_col_name = " Force (Kg f)"
current_col_name = " Current (A)"
pwm_col_name = " PWM (µs)"

page_names = ["14 V", "16 V"]
target_v = 14.8
v14, v16 = 14.0, 16.0
alpha = (target_v - v14) / (v16 - v14)  # 0.4 for 14.8V

output_file = "data/14.8V_T200_data.json"

def clean_numeric(s):
    # Convert cells like "1,234", " 12.3 " etc. to floats; non-numeric -> NaN
    return pd.to_numeric(
        s.astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce"
    )

def load_sheet(sheet_name: str) -> pd.DataFrame:
    df = pd.read_excel(data_path, sheet_name=sheet_name)

    # Keep only needed columns (exact names from your file)
    df = df[[pwm_col_name, force_col_name, current_col_name]].copy()

    # Clean + numeric
    df[pwm_col_name] = clean_numeric(df[pwm_col_name])
    df[force_col_name] = clean_numeric(df[force_col_name])
    df[current_col_name] = clean_numeric(df[current_col_name])

    # Drop bad rows
    df = df.dropna(subset=[pwm_col_name, force_col_name, current_col_name])

    # Sort by PWM and de-duplicate PWM by averaging (common in measured tables)
    df = (
        df.groupby(pwm_col_name, as_index=False)[[force_col_name, current_col_name]]
          .mean()
          .sort_values(pwm_col_name)
          .reset_index(drop=True)
    )
    return df

df14 = load_sheet(page_names[0])
df16 = load_sheet(page_names[1])

pwm14 = df14[pwm_col_name].to_numpy()
pwm16 = df16[pwm_col_name].to_numpy()

# Use the union of PWM points, but only keep those inside BOTH ranges (no extrapolation)
pwm_grid = np.unique(np.concatenate([pwm14, pwm16]))
lo = max(pwm14.min(), pwm16.min())
hi = min(pwm14.max(), pwm16.max())
pwm_grid = pwm_grid[(pwm_grid >= lo) & (pwm_grid <= hi)]

# Interpolate within each sheet (piecewise linear vs PWM)
f14 = np.interp(pwm_grid, pwm14, df14[force_col_name].to_numpy())
c14 = np.interp(pwm_grid, pwm14, df14[current_col_name].to_numpy())

f16 = np.interp(pwm_grid, pwm16, df16[force_col_name].to_numpy())
c16 = np.interp(pwm_grid, pwm16, df16[current_col_name].to_numpy())

# Voltage interpolation to 14.8V
f148 = f14 + alpha * (f16 - f14)
c148 = c14 + alpha * (c16 - c14)

out = {
    "meta": {
        "source_file": data_path,
        "sheets": page_names,
        "pwm_units": "us",
        "force_units": "kgf",
        "current_units": "A",
        "target_voltage": target_v,
        "voltage_interpolation": {
            "v_low": v14,
            "v_high": v16,
            "alpha": alpha,
            "method": "linear"
        },
        "pwm_domain_used": {"min": float(lo), "max": float(hi)},
        "row_count": int(len(pwm_grid)),
    },
    "data": [
        {"pwm": float(p), "force": float(f), "current": float(c)}
        for p, f, c in zip(pwm_grid, f148, c148)
    ]
}

with open(output_file, "w") as f:
    json.dump(out, f, indent=2)

print(f"Wrote {output_file} with {len(out['data'])} rows.")